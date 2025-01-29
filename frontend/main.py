import asyncio
import json
import os
import time

import aiofiles
import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prompts import main_system_message_template, use_search_system_message_template

vector_storage = None

CHROMA_PATH = "../chroma"

load_dotenv()

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

use_search_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(use_search_system_message_template),
        MessagesPlaceholder(variable_name="conversation"),
    ]
)

dynamic_main_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(main_system_message_template),
        MessagesPlaceholder(variable_name="conversation"),
    ]
)

conversation = []

search_decisions_memory = []

# Page info and config
st.set_page_config(page_title="Chat about Polish tech events!", page_icon="💻")

# Elements displayed above the chat
st.title("RAG app")
st.write("Welcome to the conversation with a chatbot that will tell you about tech meetups in Poland!")

# Initialize session state for user prompts and bot responses
if "user_prompts" not in st.session_state:
    st.session_state.user_prompts = []
if "bot_responses" not in st.session_state:
    st.session_state.bot_responses = []


def connect_to_vector_storage(collection_name, file_path):
    global vector_storage
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_storage = Chroma(
        collection_name=collection_name, persist_directory=file_path, embedding_function=embedding_function
    )
    print("Connected to Chroma vector storage.")


def get_search_decisions_history():
    history = ""
    for i, decision in enumerate(search_decisions_memory):
        history += f"{i+1}. {decision}\n"
    return history


async def read_json_file(file_path: str):
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        json_data = await file.read()
    return json_data


async def get_knowledge_from_vector_storage():
    decisive_prompt = use_search_prompt.format_messages(
        search_decisions_history=get_search_decisions_history(), conversation=conversation
    )
    print("Prompt used to make a decision: ", decisive_prompt)
    response = (chat_model.invoke(decisive_prompt)).content.strip()
    search_decisions_memory.append(response)
    print("Decision to search the database: ", response)
    response_json = json.loads(response)
    if response_json["number_of_results"] == 0:
        return "No data is needed."
    elif (
        response_json["number_of_results"] < 0 or response_json["number_of_results"] > 14 or response_json["expression"] == ""
    ):
        print("There was an error in decision-making!")
        return "An error occurred during data generation!"
    else:
        results = vector_storage.similarity_search_with_relevance_scores(
            response_json["expression"], k=response_json["number_of_results"] + response_json["results_shown"]
        )
        print("Results: ", results)

        if len(results) == 0:
            return "No relevant data was found."
        else:
            file_paths = []
            for doc, score in results[
                response_json["results_shown"] : (response_json["number_of_results"] + response_json["results_shown"])
            ]:
                file_path = doc.metadata.get("location", "Unkown")
                if file_path != "Unknown" and file_path not in file_paths:
                    file_paths.append(file_path)
            results = await asyncio.gather(*[read_json_file(path) for path in file_paths])

            final_string = "\n".join(results)
            return final_string


async def generate_response(user_query: str):
    conversation.append(HumanMessage(content=user_query))

    knowledge = await get_knowledge_from_vector_storage()

    prompt = dynamic_main_prompt.format_messages(knowledge=knowledge, conversation=conversation)

    response = chat_model.invoke(prompt)

    conversation.append(response)
    print("Generated prompt: ", prompt)
    print("\n\n\nResponse: ", response)
    return response.content.strip()


def stream_response(response: str):
    """
    Splits the response string into words and yields each word followed by a space.

    Args:
        response (str): The response string to be streamed.

    Yields:
        str: Each word in the response string followed by a space.
    """
    for word in response.split():
        yield word + " "
        time.sleep(0.02)


def display_conversation():
    """
    Display the conversation between the user and the chat-bot.

    This function iterates through the user prompts and chat-bot responses stored in the session state
    and displays them in the chat interface.
    """
    if "user_prompts" in st.session_state and "bot_responses" in st.session_state:
        for user_prompt, bot_response in zip(st.session_state.user_prompts, st.session_state.bot_responses):
            st.chat_message("user").write(user_prompt)
            st.empty()
            st.chat_message("assistant").write(bot_response)


async def display_response(user_prompt: str):
    """
    Grabs the user's input and passes it to the chat-bot to generate a response, then the function displays it.

    Args:
        user_prompt (str): The user's input prompt.
    """
    with st.chat_message("assistant"):
        with st.spinner("Thinking... "):
            # Operations performend while the spinner is displayed
            response = await generate_response(user_prompt)

        # Write out the response with a cool typing effect
        st.write_stream(stream_response(response))

        # Add bot response to session state
        st.session_state.bot_responses.append(response)


connect_to_vector_storage("PolandEventInfo", CHROMA_PATH)

# Get user input from chat input
user_prompt = st.chat_input("Ask a question about tech meetups in Poland")

# Check if user input is not empty
if user_prompt:
    # Display previous conversation
    display_conversation()

    # Add user prompt to session state
    st.chat_message("user").write(user_prompt)
    st.session_state.user_prompts.append(user_prompt)

    # Run asynchronous function to display response
    asyncio.run(display_response(user_prompt))

import asyncio
import json

import aiofiles
import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prompts import main_system_message_template, use_search_system_message_template

load_dotenv()

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


def connect_to_vector_storage(collection_name, file_path) -> Chroma:
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_storage = Chroma(
        collection_name=collection_name, persist_directory=file_path, embedding_function=embedding_function
    )
    print("Connected to Chroma vector storage.")
    return vector_storage


async def read_json_file(file_path: str) -> str:
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        json_data = await file.read()
    return json_data


async def get_knowledge_from_vector_storage() -> str:
    decisive_prompt = st.session_state.use_search_prompt.format_messages(
        search_decisions_history=st.session_state.search_decisions_memory, conversation=st.session_state.conversation
    )
    print("Prompt used to make a decision: ", decisive_prompt)
    response = (st.session_state.chat_model.invoke(decisive_prompt)).content.strip()
    st.session_state.search_decisions_memory += f"- {response}\n"
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
        results = st.session_state.vector_storage.similarity_search_with_relevance_scores(
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
                file_path = doc.metadata.get("filename", "Unknown")
                if file_path != "Unknown" and file_path not in file_paths:
                    file_paths.append(file_path)
            results = await asyncio.gather(*[read_json_file(path) for path in file_paths])

            full_knowledge = "\n".join(results)
            return full_knowledge


async def generate_response(user_query: str):
    st.session_state.conversation.append(HumanMessage(content=user_query))

    knowledge = await get_knowledge_from_vector_storage()

    prompt = st.session_state.dynamic_main_prompt.format_messages(
        knowledge=knowledge, conversation=st.session_state.conversation
    )

    response = st.session_state.chat_model.stream(prompt)

    print("Generated prompt: ", prompt)
    return response


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
            response_stream = await generate_response(user_prompt)

        full_response = st.write_stream(response_stream)
        print("\n\n\nResponse: ", full_response)
        st.session_state.conversation.append(AIMessage(content=full_response))
        st.session_state.bot_responses.append(full_response)


if "initialized" not in st.session_state:
    try:
        st.session_state.initialized = True

        st.session_state.CHROMA_PATH = "../chroma"

        st.session_state.chat_model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

        st.session_state.use_search_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(use_search_system_message_template),
                MessagesPlaceholder(variable_name="conversation"),
            ]
        )

        st.session_state.dynamic_main_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(main_system_message_template),
                MessagesPlaceholder(variable_name="conversation"),
            ]
        )

        st.session_state.conversation = []

        st.session_state.search_decisions_memory = ""
        st.session_state.vector_storage = connect_to_vector_storage("PolandEventInfo", st.session_state.CHROMA_PATH)
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.stop()

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

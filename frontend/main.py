import asyncio
import json
import os
from datetime import datetime
from typing import Generator

import aiofiles
import chromadb
import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prompts import main_system_message_template, use_search_system_message_template

# Load environment variables
load_dotenv()

# Page info and config
st.set_page_config(page_title="Chat about Polish tech events!", page_icon="💻")

# Elements displayed above the chat
st.title("GrepEvent")
st.write("Welcome to the conversation with a chatbot that will tell you about tech meetups in Poland!")

# Initialize session state for user prompts and bot responses
if "user_prompts" not in st.session_state:
    st.session_state.user_prompts = []
if "bot_responses" not in st.session_state:
    st.session_state.bot_responses = []


def connect_to_vector_storage(collection_name: str) -> Chroma:
    """
    Creates a connection to the Chromadb vector database collection.

    Parameters:
        collection_name (str): The name of the collection to connect to.

    Returns:
        Chroma: An object to connect to and perform operations on a Chromadb vector database collection.
    """

    # Embedding function used to create vectors while searching through a collection
    embedding_function = OpenAIEmbeddings(
        model="text-embedding-3-small", max_retries=5, request_timeout=15, retry_max_seconds=4, retry_min_seconds=1
    )

    # Create client for chroma
    client = chromadb.HttpClient(host=st.session_state.CHROMA_HOST, port=st.session_state.CHROMA_PORT)

    # Create a connection to the Chromadb vector database collection or create a new collection.
    vector_storage = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedding_function,
    )
    print("Connected to Chroma vector storage")
    return vector_storage


async def read_json_file(file_path: str) -> str:
    """
    Reads the content of a JSON file and returns it as a string.

    Parameters:
        file_path (str): The path to the file to read.

    Returns:
        str: The content of the file as a string or an error message if the file could not be read.

    Note:
        If there is an error while reading the file, the function returns an error message.
    """

    try:
        # Read the contents of the json file
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            json_data = await file.read()
        print(f"File {file_path} read successfully")
        return json_data
    except Exception as e:
        print(f"Error while reading file {file_path}: {e}")
        # Return an error message to AI if the file could not be read
        return "An error occurred while loading data about one of the events!"


async def get_knowledge_from_vector_storage() -> str:
    """
    Sends a prompt to the chat model to decide whether to search the vector storage for data and how much data to retrieve.
    Checks the response from the chat model and retrieves locations of files with data about events from the vector storage.
    Reads the content of the files and returns it as a string.

    Returns:
        str: The knowledge retrieved from the vector storage or information about no need for data or an error message.

    Note:
        If there is an error in parsing the JSON response, the function returns an error message to AI.
    """

    try:
        # Create a prompt to decide whether to search the database
        decisive_prompt = st.session_state.use_search_prompt.format_messages(
            today_date=datetime.now().strftime("%Y-%m-%d"),
            search_decisions_history=st.session_state.search_decisions_memory,
            conversation=st.session_state.conversation,
        )

        # Get the response from the chat model
        response = (st.session_state.decisive_model.invoke(decisive_prompt)).content.strip()
        print("Sent prompt to decide whether to search the vector storage")
        # Add the decision to the search decisions memory
        st.session_state.search_decisions_memory += f"- {response}\n"
        # Parse the response from the chat model
        response_json = json.loads(response)

        # Check if the response is in the correct format
        if (
            not isinstance(response_json, dict)
            or "number_of_results" not in response_json
            or "expression" not in response_json
            or "results_shown" not in response_json
            or not isinstance(response_json["number_of_results"], int)
            or not isinstance(response_json["results_shown"], int)
            or not isinstance(response_json["expression"], str)
            or response_json["number_of_results"] < 0
            or response_json["results_shown"] < 0
            or (response_json["number_of_results"] != 0 and response_json["expression"] == "")
        ):
            print("There was an error in decision-making!")
            return "An error occurred while deciding to load the data!"
        # Check if the response indicates that no data is needed
        elif response_json["number_of_results"] == 0:
            print("No data is needed to be loaded from the vector storage")
            return "No data is needed."
        # Retrieve data from the vector storage
        else:
            # Change the number of results that will be retrieved if the chat model has decided to search for too many results
            if response_json["number_of_results"] > 14:
                response_json["number_of_results"] = 14

            # Perform a similarity search in the vector storage
            print("Searching for relevant data in the vector storage")
            results = st.session_state.vector_storage.similarity_search_with_relevance_scores(
                response_json["expression"], k=response_json["number_of_results"] + response_json["results_shown"]
            )

            # Check if there are any results
            if len(results) == 0:
                return "No relevant data was found."
            else:
                # Retrieve paths to files with data about events(retrieve only from particular group of results to enable giving new results on the same topic)
                file_paths = []
                for doc, score in results[
                    response_json["results_shown"] : (response_json["number_of_results"] + response_json["results_shown"])
                ]:
                    # Get the path to the file where the data about the event is stored, but only if it is not already in the list or if it is not "Unknown"
                    file_path = doc.metadata.get("location", "Unknown")
                    if file_path != "Unknown" and file_path not in file_paths:
                        file_paths.append(file_path)
                # Read the content of the files by using asynchronous file reading
                results = await asyncio.gather(*[read_json_file(path) for path in file_paths])

                # Combine the content of the files into one string
                full_knowledge = "\n".join(results)
                return full_knowledge
    except json.JSONDecodeError as e:
        # Return an error message to AI if there is an error while parsing the JSON response
        print(f"Error while parsing JSON response: {e}")
        return "An error occurred while deciding to load the data!"


def generate_response(user_query: str) -> Generator[AIMessageChunk, None, None]:
    """
    Gets the knowledge from the vector storage and files with data about events, then creates a prompt for the chat model.
    Sends the prompt to the chat model and yields the response chunks. If the response is too long, the user is warned that the chatbot did not complete its speech.

    Parameters:
        user_query (str): The user's input query.

    Yields:
        Generator[AIMessageChunk, None, None]: A generator of AI message chunks containing the chat-bot responses.
    """

    # Add the user's query to the conversation history
    st.session_state.conversation.append(HumanMessage(content=user_query))

    # Get the knowledge from the vector storage and files with data about events
    knowledge = asyncio.run(get_knowledge_from_vector_storage())

    # Create a prompt for the chat model and get the response
    print("Sending prompt to the chat model")
    prompt = st.session_state.dynamic_main_prompt.format_messages(
        today_date=datetime.now().strftime("%Y-%m-%d"), knowledge=knowledge, conversation=st.session_state.conversation
    )
    response = st.session_state.chat_model.stream(prompt)

    # Yield the response chunks and check if the chatbot did not complete its speech or stopped unexpectedly
    for chunk in response:
        finish_reason = chunk.response_metadata.get("finish_reason", None)
        if finish_reason:
            if finish_reason == "length":
                st.warning(
                    "The chatbot did not complete its speech due to the limited permitted length of speech. Try phrasing your request differently."
                )
            elif finish_reason != "stop":
                st.warning(
                    "The chatbot did not complete its speech, ommited some parts of the response or stopped unexpectedly. Try phrasing your request differently."
                )
        yield chunk


def display_conversation() -> None:
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


def display_response(user_prompt: str) -> None:
    """
    Grabs the user's input and passes it to the chat-bot to generate a response, then the function displays it.

    Args:
        user_prompt (str): The user's input prompt.
    """
    with st.chat_message("assistant"):
        with st.spinner("Thinking... "):
            # Operations performend while the spinner is displayed
            response_stream = generate_response(user_prompt)
            # Write the response to the chat interface
            full_response = st.write_stream(response_stream)
            # Append the response to the conversation history and bot responses
            st.session_state.conversation.append(AIMessage(content=full_response))
            st.session_state.bot_responses.append(full_response)


# Check if the application is initialized(application variables and objects need to be initialized only once)
if "initialized" not in st.session_state:
    try:
        print("Initializing application variables and objects")
        # Set the flag to indicate that the application is initialized
        st.session_state.initialized = True

        # Get the port number and the host for the Chromadb vector storage
        st.session_state.CHROMA_PORT = int(os.getenv("CHROMADB_PORT"))
        st.session_state.CHROMA_HOST = os.getenv("CHROMADB_HOST")

        # Initialize the chat model, model used to decide on the need to search the vector storage, search prompt, main prompt, conversation history, search decisions memory, and vector storage
        st.session_state.chat_model = ChatOpenAI(
            model_name="gpt-4o-mini", max_retries=5, max_tokens=8000, request_timeout=40, temperature=0.4
        )

        st.session_state.decisive_model = ChatOpenAI(
            model_name="gpt-4o-mini",
            max_retries=5,
            max_tokens=5000,
            model_kwargs={"response_format": {"type": "json_object"}},
            request_timeout=40,
            temperature=0.2,
        )

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

        st.session_state.vector_storage = connect_to_vector_storage("PolandEventInfo")

        # Initialize conversation blocking flag
        st.session_state.blocking_conversation = False
    except Exception as e:
        # Display an error message if the application fails to initialize
        st.error(f"Failed to initialize application! Try refreshing the page. Error: {e}")
        st.session_state.blocking_conversation = True
        st.stop()

# Display previous conversation
display_conversation()

# Check if the conversation is not blocked by an error
if not st.session_state.blocking_conversation:
    # Get user input from chat input
    user_prompt = st.chat_input("Ask a question about tech meetups in Poland")

    # Check if user input is not empty
    if user_prompt:
        try:
            # Add user prompt to session state
            st.chat_message("user").write(user_prompt)
            st.session_state.user_prompts.append(user_prompt)

            # Run asynchronous function to display response
            display_response(user_prompt)
        # Handle exceptions from most of the functions
        except Exception as e:
            # Check if the error is due to exceeding the context length of the chatbot
            if "context_length_exceeded" in str(e):
                print("Context length exceeded")
                st.error(f"Conversation limit reached. Please refresh the page to start a new conversation.")
            else:
                print(f"An error occurred: {e}")
                st.error(
                    f"An error occurred. Try refreshing the page to start a new conversation, or checking your interent connection."
                )
            # Block the conversation after an error
            st.session_state.blocking_conversation = True
            st.stop()
else:
    # Inform the user that the conversation is blocked after he/she tries to send a message after an error
    st.error("Please refresh the page to start a new conversation.")

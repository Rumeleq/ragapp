import asyncio
import random
import time

import streamlit as st

# Page info and config
st.set_page_config(page_title="Chat about Polish tech events!", page_icon="💻")

# Elements displayed above the chat
st.title("RAG app")
st.write("Welcome to the conversation with a chatbot that will tell you about tech meetups in Poland!")

# Lorem ipsum text for generating random responses
LOREM_IPSUM = """
Lorem ipsum dolor sit amet, **consectetur adipiscing** elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""

# Initialize session state for user prompts and bot responses
if "user_prompts" not in st.session_state:
    st.session_state.user_prompts = []
if "bot_responses" not in st.session_state:
    st.session_state.bot_responses = []


async def search_for_events():
    await asyncio.sleep(2)
    print("searching for events...")


async def analyze_data():
    await asyncio.sleep(1)
    print("analyzing data...")


async def generate_response():
    """
    Generates a response by randomly selecting words from LOREM_IPSUM.

    Returns:
        str: The generated response.
    """
    await asyncio.sleep(1)
    print("generating response...")
    return "".join([str(random.choice(LOREM_IPSUM.split())) + " " for i in range(10)])


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
            await search_for_events()
            await analyze_data()
            response = await generate_response()
        st.write_stream(stream_response(response))
        st.session_state.bot_responses.append(response)


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

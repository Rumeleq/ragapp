import asyncio
import random
import time

import streamlit as st

st.set_page_config(page_title="Chat about Polish tech events!", page_icon="💻")

st.title("RAG app")
st.write("Welcome to the conversation with a chatbot that will tell you about tech meetups in Poland!")

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


async def generate_response():
    await asyncio.sleep(1)
    return "".join([str(random.choice(LOREM_IPSUM.split())) + " " for i in range(10)])


def stream_response(response: str):
    for word in response.split():
        yield word + " "
        time.sleep(0.02)


def display_conversation():
    for user_prompt, bot_response in zip(st.session_state.user_prompts, st.session_state.bot_responses):
        st.chat_message("user").write(user_prompt)
        st.empty()
        st.chat_message("assistant").write(bot_response)


async def display_response(user_prompt: str):
    with st.chat_message("assistant"):
        with st.spinner("Thinking... "):
            response = await generate_response()
        st.write_stream(stream_response(response))
        st.session_state.bot_responses.append(response)


user_prompt = st.chat_input("Ask a question about tech meetups in Poland")
if user_prompt:
    display_conversation()
    st.chat_message("user").write(user_prompt)
    st.session_state.user_prompts.append(user_prompt)
    asyncio.run(display_response(user_prompt))
    print({"user_prompts": st.session_state.user_prompts, "bot_responses": st.session_state.bot_responses})

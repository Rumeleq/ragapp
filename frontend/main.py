import time

import streamlit as st
from helper import bot_responses, user_prompts

st.set_page_config(page_title="Chat about polish tech events!", page_icon=":robot:")

st.title("RAG app")
st.write("Welcome to the conversation with chatbot, that will tell you about tech meetups in Poland!")

LOREM_IPSUM = """
Lorem ipsum dolor sit amet, **consectetur adipiscing** elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""


def stream_response(response: str):
    for word in response.split():
        yield word + " "
        time.sleep(0.02)


def display_conversation():
    for user_prompt, bot_response in zip(user_prompts[:-1], bot_responses[:-1]):
        st.chat_message("user").write(user_prompt)
        st.chat_message("assistant").write(bot_response)
    st.chat_message("user").write(user_prompts[-1])
    with st.chat_message("assistant"):
        empty_space = st.empty()
        with empty_space.container():
            with st.status("Generating response...", expanded=True) as status:
                st.write("Searching for events...")
                time.sleep(2)
                st.write("Analyzing data...")
                time.sleep(1)
                st.write("Constructing final message...")
                time.sleep(1)
                status.update(label="Complete!", state="complete", expanded=False)
                time.sleep(1)
        empty_space.empty()
        st.write_stream(stream_response(bot_responses[-1]))


user_prompt = st.chat_input("Ask a question about tech meetups in Poland")
if user_prompt:
    user_prompts.append(user_prompt)
    bot_responses.append(LOREM_IPSUM)
    display_conversation()

import streamlit as st
from helper import bot_responses, user_prompts

st.title("RAG app")
st.write("Welcome to the conversation with chatbot, that will tell you about tech meetups in Poland!")

LOREM_IPSUM = """
Lorem ipsum dolor sit amet, **consectetur adipiscing** elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""


def display_conversation():
    for user_prompt, bot_response in zip(user_prompts, bot_responses):
        st.chat_message("user").write(user_prompt)
        st.chat_message("assistant").write(bot_response)


user_prompt = st.chat_input("Ask a question about tech meetups in Poland")
if user_prompt:
    user_prompts.append(user_prompt)
    bot_responses.append(LOREM_IPSUM)
    display_conversation()

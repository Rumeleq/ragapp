import streamlit as st

st.title("RAG app")
st.write("Welcome in the conversation with chatbot, that will tell you about tech meetups in Poland!")

LOREM_IPSUM = """
Lorem ipsum dolor sit amet, **consectetur adipiscing** elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""

user_prompts: list[str] = []
bot_responses: list[str] = []

user_prompt = st.text_input("You: ", "")

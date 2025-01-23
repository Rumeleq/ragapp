import streamlit as st

st.title("RAG app")
st.write("Welcome in the conversation with chatbot, that will tell you about tech meetups in Poland!")

LOREM_IPSUM = """
Lorem ipsum dolor sit amet, **consectetur adipiscing** elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""

user_prompts: list[str] = [LOREM_IPSUM, "aaa"]
bot_responses: list[str] = ["bbb", LOREM_IPSUM]


def display_conversation():
    for user_prompt, bot_response in zip(user_prompts, bot_responses):
        st.header("You:")
        st.write(user_prompt)
        st.header("Bot:")
        st.write(bot_response)


display_conversation()
user_prompt = st.chat_input("Ask a question about tech meetups in Poland")
if user_prompt:
    user_prompts.append(user_prompt)
    bot_responses.append(LOREM_IPSUM)

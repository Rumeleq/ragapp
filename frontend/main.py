import asyncio
import random
import time

import streamlit as st
from helper import bot_responses, user_prompts

st.set_page_config(page_title="Chat about polish tech events!", page_icon="💻")

st.title("RAG app")
st.write("Welcome to the conversation with chatbot, that will tell you about tech meetups in Poland!")

LOREM_IPSUM = """
Lorem ipsum dolor sit amet, **consectetur adipiscing** elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
"""


async def search_for_events():
    await asyncio.sleep(2)
    print("searching for events...")


async def analize_data():
    await asyncio.sleep(1)
    print("analyzing data...")


async def generate_response():
    await asyncio.sleep(1)
    print("generating response...")
    return "".join([str(random.randint(1, 9)) for i in range(10)])


def stream_response(response: str):
    for word in response.split():
        yield word + " "
        time.sleep(0.02)


async def display_conversation():
    for user_prompt, bot_response in zip(user_prompts[:-1], bot_responses[:-1]):
        st.chat_message("user").write(user_prompt)
        st.chat_message("assistant").write(bot_response)
    st.chat_message("user").write(user_prompts[-1])
    with st.chat_message("assistant"):
        empty_space = st.empty()
        with empty_space.container():
            with st.status("Generating response...", expanded=True) as status:
                st.write("Searching for events...")
                await search_for_events()
                st.write("Analyzing data...")
                await analize_data()
                st.write("Constructing final message...")
                response = await generate_response()
                status.update(label="Complete!", state="complete", expanded=False)
                time.sleep(0.5)
                bot_responses.append(response)
        empty_space.empty()
        st.write_stream(stream_response(bot_responses[-1]))


user_prompt = st.chat_input("Ask a question about tech meetups in Poland")
if user_prompt:
    user_prompts.append(user_prompt)
    print({"user_prompts": user_prompts, "bot_responses": bot_responses})
    asyncio.run(display_conversation())

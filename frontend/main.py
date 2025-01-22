import streamlit as st

st.title("RAG app")
st.write("Welcome in the conversation with chatbot, that will tell you about tech meetups in Poland!")

user_prompt = st.text_input("You: ", "")

import asyncio
import json
import os

import aiofiles
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prompts import main_prompt_template


async def read_json_file(file_path: str):
    async with aiofiles.open(file_path, "r", encoding="utf-16") as file:
        json_data = await file.read()
    return json_data


async def get_knowledge_from_database(user_query: str):
    data = ""
    results = db.similarity_search_with_relevance_scores(user_query, k=5)

    if len(results) == 0 or results[0][1] < 0.3:
        return "No relevant data was found."
    else:
        file_paths = []
        for doc, score in results:
            url = doc["metadata"].get("filename", "Unkown")
            if url != "Unknown":
                file_paths.append(url)
        results = await asyncio.gather(*[read_json_file(file_path) for file_path in file_paths])

        final_string = "\n".join(results)
        return final_string


async def process_user_query(user_query: str):
    knowledge = await get_knowledge_from_database()

    history = memory.load_memory_variables({}).get("history", "")

    inputs = {"knowledge": knowledge, "history": history, "input": user_query}

    prompt = dynamic_prompt.format(**inputs)

    response = conversation_chain.run(inputs)

    print("Generated prompt: ", prompt)
    print("AI: ", response)


async def main():
    while True:
        user_query = input("User: ")
        if user_query.lower() in ["quit", "exit"]:
            break

        await process_user_query(user_query)


if __name__ == "__main__":
    result = load_dotenv()

    API_KEY = os.getenv("OPENAI_API_KEY")

    memory = ConversationBufferMemory(memory_key="history", input_key="input")

    dynamic_prompt = PromptTemplate.from_template(main_prompt_template)

    chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=API_KEY)

    conversation_chain = LLMChain(llm=chat_model, prompt=dynamic_prompt, memory=memory)

    CHROMA_PATH = "../chroma"

    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small", api_key=API_KEY)

    db = Chroma(collection_name="PolandEventInfo", persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    asyncio.run(main)

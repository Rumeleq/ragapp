import asyncio
import json
import os

import aiofiles
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from prompts import main_system_message_template, use_search_system_message_template

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=API_KEY)

use_search_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(use_search_system_message_template),
        MessagesPlaceholder(variable_name="conversation"),
    ]
)

dynamic_main_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(main_system_message_template),
        MessagesPlaceholder(variable_name="conversation"),
    ]
)

conversation = []

search_decisions_memory = []

CHROMA_PATH = "../chroma"

embedding_function = OpenAIEmbeddings(model="text-embedding-3-small", api_key=API_KEY)

vector_store = Chroma(collection_name="PolandEventInfo", persist_directory=CHROMA_PATH, embedding_function=embedding_function)
print("Number of documents in the collection:", vector_store._collection.count())


def get_search_decisions_history():
    history = ""
    for i, decision in enumerate(search_decisions_memory):
        history += f"{i+1}. {decision}\n"
    return history


async def read_json_file(file_path: str):
    async with aiofiles.open(file_path, "r", encoding="utf-16") as file:
        json_data = json.dumps(json.loads(await file.read()), ensure_ascii=False)
        # json_data = await file.read()
    return json_data


async def get_knowledge_from_database():
    decisive_prompt = use_search_prompt.format_messages(
        search_decisions_history=get_search_decisions_history(), conversation=conversation
    )
    print("Prompt do model1: ", decisive_prompt)
    response = (chat_model.invoke(decisive_prompt)).content.strip()
    search_decisions_memory.append(response)
    print("Decision to search the database: ", response)
    response_json = json.loads(response)
    if response_json["number_of_results"] == 0:
        return "No data is needed."
    elif (
        response_json["number_of_results"] < 0 or response_json["number_of_results"] > 14 or response_json["expression"] == ""
    ):
        print("There was an error in decision-making!")
        return "An error occurred during data generation!"
    else:
        results = vector_store.similarity_search_with_relevance_scores(
            response_json["expression"], k=response_json["number_of_results"] + response_json["results_shown"]
        )
        print("Results: ", results)

        if len(results) == 0:
            return "No relevant data was found."
        else:
            file_paths = []
            for doc, score in results[
                response_json["results_shown"] : (response_json["number_of_results"] + response_json["results_shown"])
            ]:
                file_path = doc.metadata.get("location", "Unkown")
                if file_path != "Unknown" and file_path not in file_paths:
                    file_paths.append(file_path)
            results = await asyncio.gather(*[read_json_file(path) for path in file_paths])

            final_string = "\n".join(results)
            # print("\n\nTest: ", final_string)
            return final_string


async def process_user_query(user_query: str):
    conversation.append(HumanMessage(content=user_query))

    knowledge = await get_knowledge_from_database()

    prompt = dynamic_main_prompt.format_messages(knowledge=knowledge, conversation=conversation)

    response = chat_model.invoke(prompt)

    conversation.append(response)
    print("Generated prompt: ", prompt)
    print("AI: ", response.content.strip())


async def main():
    while True:
        user_query = input("User: ")
        if user_query.lower() in ["quit", "exit"]:
            break

        await process_user_query(user_query)


if __name__ == "__main__":
    asyncio.run(main())

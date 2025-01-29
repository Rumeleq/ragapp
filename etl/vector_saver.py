import asyncio
import json
import os
import shutil

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


async def add_data_to_vector_storage(vector_storage: Chroma, main_information: dict[str], description: str, file_path: str):
    try:
        if description != "N/A":
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200, chunk_overlap=150, length_function=len, separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
            )

            chunks = text_splitter.split_text(description)
        else:
            chunks = []
        chunks.append(json.dumps(main_information, ensure_ascii=False))

        await vector_storage.aadd_texts(texts=chunks, metadatas=[{"location": file_path}] * len(chunks))
    except Exception as e:
        print(f"Error while embedding {file_path} or adding to vector_storage: {e}")


def create_new_vector_storage(API_KEY: str) -> Chroma:
    CHROMA_PATH = "../chroma"

    if os.path.exists(CHROMA_PATH):
        for item in os.listdir(CHROMA_PATH):
            item_path = os.path.join(CHROMA_PATH, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        print("The database has been deleted")
    else:
        print(f"Directory {CHROMA_PATH} does not exist")

    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small", api_key=API_KEY)

    vector_storage = Chroma(
        collection_name="PolandEventInfo", persist_directory=CHROMA_PATH, embedding_function=embedding_function
    )

    return vector_storage

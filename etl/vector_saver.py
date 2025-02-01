import json
import os
import shutil

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class VectorStorageError(Exception):
    """
    This is an exception for errors related to the creation of the vector database.
    """

    pass


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
        print(f"Error while adding {file_path} to vector_storage: {e}")


def create_new_vector_storage() -> Chroma:
    CHROMA_PATH = "../chroma"

    try:
        if os.path.exists(CHROMA_PATH):
            for item in os.listdir(CHROMA_PATH):
                if item == ".gitignore":  # must be removed at the end of application development
                    continue
                item_path = os.path.join(CHROMA_PATH, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except OSError as e:
                    raise VectorStorageError(f"Failed to clean vector storage: {e}")
        else:
            print(f"Directory {CHROMA_PATH} does not exist")

        embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small", max_retries=5, request_timeout=8, retry_max_seconds=4, retry_min_seconds=1
        )

        vector_storage = Chroma(
            collection_name="PolandEventInfo", persist_directory=CHROMA_PATH, embedding_function=embedding_function
        )

        print("Vector storage cleaned successfully")
        return vector_storage
    except Exception as e:
        error_msg = f"Error while cleaning vector storage: {e}"
        print(error_msg)
        raise VectorStorageError(error_msg)

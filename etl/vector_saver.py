import json
import os
import shutil

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class VectorStorageError(Exception):
    """
    This is an exception for errors related to the creation of the vector storage.
    """

    pass


async def add_data_to_vector_storage(vector_storage: Chroma, event_details: dict[str], filename: str):
    """
    It divides the extracted event information from the website into smaller parts and adds them to the vector storage after automatically converting them into vectors.
    Each vector is added with the name of the file where the data changed into this vector is stored.

    Parameters:
        vector_storage (Chroma): The vector storage to which the data is added.
        event_details (dict[str]): All data about the event.
        filename (str): The name of the file where all event data is held.

    Raises:
        Exception: If there is an error while adding data to the vector storage.
    """
    try:
        # Filter event information, removing descriptions (as they are long and need to be split separately) and non-event related values
        filtered_event_details = {
            key: value for key, value in event_details.items() if key != "event_description" and value != "N/A"
        }

        description = event_details["event_description"]

        # Check if the event has a description
        if description != "N/A":
            # Divide the event description into smaller parts
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200, chunk_overlap=150, length_function=len, separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
            )

            chunks = text_splitter.split_text(description)
        else:
            chunks = []

        # Add other information about the event to the chunks
        chunks.append(json.dumps(filtered_event_details, ensure_ascii=False))

        # Add the text chunks to the vector storage
        await vector_storage.aadd_texts(texts=chunks, metadatas=[{"filename": filename}] * len(chunks))
    except Exception as e:
        print(f"Error while adding {filename} to vector_storage: {e}")


def create_new_vector_storage() -> Chroma:
    """
    Resets the contents of the previous collection by deleting it and recreating it, but empty.

    Returns:
        Chroma: An empty vector storage object for storing new data.

    Raises:
        VectorStorageError: If there is an error while cleaning the vector storage.
    """
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

        # Embedding function used to create vectors
        embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small", max_retries=5, request_timeout=15, retry_max_seconds=4, retry_min_seconds=1
        )

        # Create a new vector storage object
        vector_storage = Chroma(
            collection_name="PolandEventInfo", persist_directory=CHROMA_PATH, embedding_function=embedding_function
        )

        print("Vector storage cleaned successfully")
        return vector_storage
    except Exception as e:
        error_msg = f"Error while cleaning vector storage: {e}"
        print(error_msg)
        raise VectorStorageError(error_msg)

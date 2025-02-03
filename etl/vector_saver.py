import json
import os

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


async def add_data_to_vector_storage(vector_storage: Chroma, event_details: dict[str], file_path: str) -> None:
    """
    It divides the extracted event information from the website into smaller parts and adds them to the vector storage after automatically converting them into vectors.
    Each vector is added with the path to the file where the data changed into this vector is stored.

    Parameters:
        vector_storage (Chroma): The vector storage to which the data is added.
        event_details (dict[str]): All data about the event.
        file_path (str): The path to the file where all event data is held.

    Note:
        If there is an error while adding data to the vector storage, it is handled internally and not re-raised.
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
        await vector_storage.aadd_texts(texts=chunks, metadatas=[{"location": file_path}] * len(chunks))
    except Exception as e:
        print(f"Error while adding {file_path} to vector_storage: {e}")


def create_new_vector_storage() -> Chroma:
    """
    Resets the contents of the previous collection by deleting it and recreating it, but empty.

    Returns:
        Chroma: An empty vector storage object for storing new data.

    Raises:
        Exception: If there is an error while resetting collection.
    """

    try:
        CHROMA_PORT = int(os.getenv("CHROMADB_PORT"))
        CHROMA_HOST = os.getenv("CHROMADB_HOST")

        # Embedding function used to create vectors
        embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small", max_retries=5, request_timeout=15, retry_max_seconds=4, retry_min_seconds=1
        )

        # Create Chroma's client
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

        # Create a connection to the Chromadb vector database collection or create a new collection
        vector_storage = Chroma(
            client=client,
            collection_name="PolandEventInfo",
            # client_settings=Settings(chroma_server_host=CHROMA_HOST, chroma_server_http_port=CHROMA_PORT),
            embedding_function=embedding_function,
        )

        # Reset the collection
        vector_storage.reset_collection()

        print("Vector storage reset successfully")
        return vector_storage
    except Exception as e:
        print(
            "An error occurred while cleaning the vector storage. The application will not work properly. Stopping application."
        )
        raise

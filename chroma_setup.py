import os
from dotenv import load_dotenv
import json

from chromadb import HttpClient
from chromadb.utils import embedding_functions

load_dotenv()
config = json.load(open("data/config.json"))

openai_api_key = os.getenv("OPENAI_API_KEY")
summaries_path = config["summaries"]["summaries_path"]

print('Connecting to ChromaDB...')

client = HttpClient(
    host=config["chromadb"]["chromadb_server_host"],
    port=config["chromadb"]["chromadb_server_port"]
)

print('Connected to ChromaDB.')

embedding_function = embedding_functions.DefaultEmbeddingFunction()

try:
    print('Creating ChromaDB collection...')

    collection = client.get_or_create_collection(
        name="book_embeddings",
        embedding_function=embedding_function
    )

    print('ChromaDB collection created.')
    print('Parsing summaries JSON and adding to collection...')

    with open(summaries_path, 'r') as summaries_fp:
        json_data = json.load(summaries_fp)

        try:
            collection.add(
                documents=[
                    str(s["summary"]).replace("\n", " ")
                    for s in json_data
                ],
                metadatas=[
                    {"title": s["title"], "author": s["author"]}
                    for s in json_data
                ],
                ids=[str(i) for i in range(len(json_data))]
            )

            print('Finished adding documents to collection.')

        except Exception as e:
            print(f"Error adding documents to collection: {e}")


except ValueError as e:
    print(f"Collection already exists: {e}.")
except Exception as e:
    print(f"Error creating collection: {e}")

import os
import dotenv
import json

import openai
from chromadb import HttpClient
from chromadb.utils import embedding_functions

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class RecommendationService:

    __system_prompt = """
       You are a book recommendation assistant.

        Rules:
        1. Use only the `search_books` function to find candidates.
        2. Choose exactly ONE book (best fit).
        3. Inform the user if no book fits.
        4. Return only the book title and author.
        5. Do not include summaries or explanations.
        6. After answering, ask the user if they would want the book summary.
        7. If user later asks for a summary, then call `get_summary_by_title`.
    """

    __tools = [
        {
            "type": "function",
            "function": {
                "name": "search_books",
                "description": "Finds the best matching books inside a ChromaDB based on the user description for RAG",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "A description of the book or topic the user is interested in."
                        }
                    },
                    "required": ["description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Retrieves the summary for a given book title.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the book."
                        }
                    },
                    "required": ["title"]
                }
            }
        }
    ]

    def __init__(self):
        dotenv.load_dotenv()
        self.config = self.__load_config()

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = openai.Client(
            base_url=self.config['ai']['endpoint_url'],
            api_key=self.openai_api_key
        )
        self.chromadb_client = HttpClient(
            host=self.config["chromadb"]["chromadb_server_host"],
            port=self.config["chromadb"]["chromadb_server_port"]
        )

    def call_model(self, message, history=[]):
        """
        Handle user message and decide what actions to take
        """

        messages = [
            {
                'role': 'system',
                'content': self.__system_prompt
            },
            *history,
            {
                'role': 'user',
                'content': message
            }
        ]

        response = self.openai_client.chat.completions.create(
            model=self.config['ai']["model"],
            messages=messages,
            tools=self.__tools,
            temperature=self.config['ai']['temperature']
        )

        if response.choices and response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            if tool_call.function.name == "search_books":
                call_args = json.loads(tool_call.function.arguments)
                print(f"Function call arguments: {call_args}")
                book_results = self.search_books(call_args['description'])

                print(f"Book results: {[book['title'] for book in book_results]}")

                if not book_results:
                    return "No suitable book found."

                response = self.openai_client.chat.completions.create(
                    model=self.config['ai']["model"],
                    messages=[
                        *messages,
                        {
                            "role": "system",
                            "content": f"""
                                `search_books` function call returned the following candidates: 
                                {"\n\n".join([
                                    f"{book['title']} by {book['author']}\nSummary: {book['summary']}"
                                    for book in book_results
                                ])}
                            """
                        }
                    ],
                    temperature=self.config['ai']['temperature'],
                )

                # TODO: Handle error cases
                return response.choices[0].message.content

            elif tool_call.function.name == "get_summary_by_title":
                call_args = json.loads(tool_call.function.arguments)
                summary = self.get_summary_by_title(call_args['title'])

                return summary

        # TODO: Handle error cases
        return response.choices[0].message.content

    def search_books(self, description: str):
        """
        Get the best matching book title based on the provided description
        using RAG (ChromaDB).
        """

        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name=self.config['ai']['embedding_model'],
            api_base=self.config['ai']['endpoint_url']
        )

        collection = self.chromadb_client.get_collection(
            name="book_embeddings",
            embedding_function=embedding_function
        )

        query_embedding = embedding_function([description])[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2
        )

        if results and results['documents'] and results['metadatas']:
            metadatas = [(meta['title'], meta['author']) for meta in results['metadatas'][0]]
            summaries = results['documents'][0]
            return [
                {
                    'title': title,
                    'summary': summary,
                    'author': author
                }
                for (title, author), summary in zip(metadatas, summaries)
            ]

        return None

    def get_summary_by_title(self, title: str) -> str:
        path = os.path.join(ROOT_DIR, self.config["summaries"]["summaries_path"])

        with open(path) as f:
            json_data = json.load(f)

            for book in json_data:
                if book["title"] == title:
                    return book["summary"]

        return "Summary not found."

    def __load_config(self) -> dict:
        with open("data/config.json") as f:
            return json.load(f)

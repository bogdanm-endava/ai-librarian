import os
import dotenv
import json

import openai
from chromadb import HttpClient
from chromadb.utils import embedding_functions
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class RecommendationService:

    __system_prompt = """
       You are a book recommendation assistant.\n\n
        1.
        - Use ONLY the `search_books` function to find candidates.\n
        - Call the function with the part of the user's query where he describes the book
        - Choose exactly ONE book (best fit).\n
        - If no book fits, say: "I couldn't find a suitable book."\n
        - Return ONLY the title and author, and ask: "Would you like a summary of this book?"\n
        - Do not include summaries or explanations.\n\n

        2. If the user later asks for a summary:\n
        - Call `get_summary_by_title` ONLY with the title.\n
        - Return ONLY the summary text.\n
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
            temperature=self.config['ai']['temperature'],
            max_completion_tokens=self.config['ai']['max_output_tokens'],
            messages=[
                {
                    'role': 'system',
                    'content': """
                        Detect if the user message is about books or book recommendations.
                        Answer with the format:
                        {"is_book_related": boolean}
                    """
                },
                {
                    'role': 'user',
                    'content': message
                }
            ],
        )

        if response.choices and response.choices[0]:
            def extract_non_think_content(text):
                return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

            response_content = response.choices[0].message.content
            response_content = extract_non_think_content(response_content)

            print(f"Response content: {response_content}")

            json_response = json.loads(response_content)
            if not json_response.get("is_book_related", False):
                return 'I can only help with book recommendations.'

        response = self.openai_client.chat.completions.create(
            model=self.config['ai']["model"],
            tools=self.__tools,
            temperature=self.config['ai']['temperature'],
            max_completion_tokens=self.config['ai']['max_output_tokens'],
            messages=messages
        )

        print(response)

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
                            "tool_call_id": tool_call.id,
                            "role": "tool",
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
                    max_completion_tokens=self.config['ai']['max_output_tokens']
                )

                try:
                    return response.choices[0].message.content
                except Exception as e:
                    raise RuntimeError(f"Failed to process model response: {e}")

            elif tool_call.function.name == "get_summary_by_title":
                call_args = json.loads(tool_call.function.arguments)

                print(f"Function call arguments: {call_args}")

                # Remove the author name from the argument
                title = call_args['title']
                title = re.sub(r'\s+by\s+.*$', '', title, flags=re.IGNORECASE).strip()
                summary = self.get_summary_by_title(title)

                return summary

        try:
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Failed to process model response: {e}")

    def search_books(self, description: str):
        """
        Get the best matching book title based on the provided description
        using RAG (ChromaDB).
        """

        embedding_function = embedding_functions.DefaultEmbeddingFunction()

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

        summaries_path = self.config["summaries"]["summaries_path"]
        path = os.path.join(ROOT_DIR, *summaries_path.split("/"))

        with open(path) as f:
            json_data = json.load(f)

            for book in json_data:
                if book["title"] == title:
                    return book["summary"]

        return "Summary not found."

    def __load_config(self) -> dict:
        config_path = os.path.join(ROOT_DIR, "config.json")
        with open(config_path) as f:
            return json.load(f)

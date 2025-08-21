from flask import Flask, request
from flask_cors import CORS
from recommendation_service import RecommendationService

app = Flask(__name__)
CORS(app)

recommendation_service = RecommendationService()


@app.route('/hello_world', methods=['GET'])
def hello_world():
    return "<h1>Hello, World!</h1>"


@app.route('/chat', methods=['POST'])
def chat():
    request_structure = {
        "query": str,
        "history": list
    }

    data = request.get_json()

    for key, expected_type in request_structure.items():
        if key not in data or not isinstance(data[key], expected_type):
            return {
                "payload": None,
                "error": "Request body does not match the expected format."
            }, 400

    try:
        service_response = recommendation_service.call_model(
            data['query'],
            data['history']
        )

        return {
            "payload": service_response,
            "error": None
        }
    except Exception as e:
        return {
            "payload": None,
            "error": str(e)
        }, 500

from flask import Flask, json, request

app = Flask(__name__)


@app.route('/hello_world', methods=['GET'])
def hello_world():
    return "<h1>Hello, World!</h1>"


@app.route('/chat', methods=['GET'])
def chat():
    data: json = request.get_json()
    print(f"Received data: {data}")
    return f"Chat query received: {data['query']}"

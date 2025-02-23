import jwt
import datetime
from flask_cors import CORS
from flask import Flask, jsonify, request, make_response


SECRET_KEY = "secret"
app = Flask(__name__)
CORS(app)

dummy = {
    "header": "Authenticate",
    "fname": "John",
    "lname": "Smith",
    "pword": "pword123"
}

dummy_response = {
    "status": int,
    "message": str
}

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:4200"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/", methods=["OPTIONS"])
def handle_options():
    return make_response("", 204)

@app.route("/", methods=["GET"])
def get():
    return jsonify({"message": "echo GET"})

@app.route("/", methods=["POST"])
@app.route("/map", methods=["POST"])
def post():
    data = request.get_json()

    print(data)

    if "header" in data:
        print("Auth request")

        payload = {
            "status": 200,
            "message": "Good auth",
            "newToken": ""
        }
    else:
        print("Other")

        payload = {
            "status": 200,
            "message": "Good something",
            "data": [
                {"token": "glerb"}
            ]
        }

    return jsonify(payload), 200

if __name__ == "__main__":
    app.run(debug=False)
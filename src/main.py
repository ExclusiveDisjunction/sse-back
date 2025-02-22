from flask import Flask, jsonify, request
from flask_cors import CORS

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

@app.route("/", methods=["GET"])
def get():
    return jsonify({"message": "echo GET"})

@app.route("/", methods=["POST"])
def post():
    data = request.get_json()

    return jsonify({"status": 200, "message": data["fName"]}), 200

if __name__ == "__main__":
    app.run(debug=True)
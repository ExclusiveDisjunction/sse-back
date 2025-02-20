from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def get():
    return jsonify({"message": "echo GET"})

@app.route("/", methods=["POST"])
def post():
    return jsonify({"message": "echo POST"})

if __name__ == "__main__":
    app.run(debug=True)
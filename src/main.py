from flask_cors import CORS
from flask import Flask, jsonify, request, make_response

app = Flask(__name__)
CORS(app, origins = ["*"])

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, ngrok-skip-browser-warning"
    return response

@app.route("/", methods=["OPTIONS"])
def options():
    response = make_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, ngrok-skip-browser-warning"
    return response

@app.route("/", methods = ["GET"])
def get():
    print("INCOMING GET REQUEST RECIEVED")
    return jsonify({"response": "Hello From Server"}), 200

if __name__ == "__main__":
    print("Starting server...\n")

    app.run(debug = True)
    # app.run(debug = True, ssl_context = ('server.crt', 'server.key'))
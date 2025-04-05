from flask_cors import CORS
from flask import Flask, jsonify, request, make_response

app = Flask(__name__)
CORS(app,
     origins=["http://localhost:4200"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "ngrok-skip-browser-warning", "token", "lat", "long", "start", "end"]
     )

@app.route("/test", methods = ["GET"])
def testGet():
    print("INCOMING GET REQUEST RECEIVED -> /test")
    return jsonify({"response": "Hello GET Server"}), 200

@app.route("/test", methods = ["POST"])
def testPost():
    print("INCOMING POST REQUEST RECEIVED -> /test")
    return jsonify({"response": "Hello POST Server"}), 200

@app.route("/login", methods = ["GET"])
def getLogin():
    print("INCOMING LOGIN GET REQUEST RECEIVED -> /login")
    return jsonify({"response": "Hello GET Server"}), 200

@app.route("/login", methods = ["POST"])
@app.route("/create-account", methods = ["POST"])
def postLogin():
    print("INCOMING LOGIN POST REQUEST RECEIVED -> /create-account or /login")

    good_payload = {
        "ok": True,
        "message": "Sign In Good",
        "user": {
            "user": {
                "fname": "John",
                "lname": "Doe",
                "username": "johndoe"
            },
            "token": "your-auth-token-here"
        }
    }

    bad_payload = {

    }

    return jsonify(good_payload), 200

@app.route("/validate-token", methods = ["POST"])
def validateToken():
    print("INCOMING TOKEN VALIDATION POST REQUEST RECEIVED -> /validate-token")

    payload = {
        "valid": True,
        "message": "",
    }

    return jsonify(payload), 200

@app.route("/map-nodes", methods = ["GET"])
def getMapNodes():
    print("INCOMING GET REQUEST RECEIVED -> /map-nodes")

    # payload = {
    #     "nodes": {
    #         1: {
    #             "x": 570,
    #             "y": 326,
    #             "name": "name",
    #             "group": "group",
    #             "kind": 0,
    #             "tags": [
    #                 "tag1"
    #             ]
    #         },
    #         2: {
    #             "x": 586,
    #             "y": 313,
    #             "name": "name",
    #             "group": "group",
    #             "kind": 0,
    #             "tags": [
    #                 "tag1"
    #             ]
    #         }
    #     }
    # }

    payload = {
        1: {
            "x": 570,
            "y": 326,
            "name": "name",
            "group": "group",
            "kind": 0,
            "tags": [
                "tag1"
            ]
        },
        2: {
            "x": 586,
            "y": 313,
            "name": "name",
            "group": "group",
            "kind": 0,
            "tags": [
                "tag1"
            ]
        }
    }

    return jsonify(payload), 200

@app.route("/traverse", methods = ["GET"])
def fetchNodesToTraverse():
    print("INCOMING GET REQUEST RECEIVED -> /traverse")

    payload = {
        "ids": [1, 2, 3, 4]
    }

    return jsonify(payload), 200

if __name__ == "__main__":
    print("Starting server...\n")

    app.run(debug = False)
    # app.run(debug = True, ssl_context = ('server.crt', 'server.key'))
from flask_cors import CORS
from flask import Flask, jsonify, request, make_response

import sqlite3
from usr import SignInRequest, SignInResponse, UserSessions, NetworkUser, User, AuthenticatedUser

active_users = UserSessions()
db: sqlite3.Connection = None

def generate_token() -> str: 
    pass

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

@app.route("/login", methods = ["POST"])
def loginRequest():
    global active_users
    global db

    msg = request.get_json()
    decoded: SignInRequest | None = SignInRequest.from_dict(msg)
    if decoded is None:
        return jsonify(SignInResponse(False, "Unable to decode request", None).to_dict()), 400
    
    if db is None:
        return jsonify(SignInResponse(False, "User authentication service is unavailable").to_dict()), 503

    found: User | None = User.lookup_db(db.cursor(), decoded.fname)
    if found is None:
        return jsonify(SignInResponse(False, "User credentials could not be found.").to_dict()), 401
    
    if found.password_hash != decoded.password: 
        return jsonify(SignInResponse(False, "User credentials did not match.").to_dict()), 401

    token = generate_token()
    active_users.auth_user(token, found)

    auth_user = AuthenticatedUser(found.net, token)
    return jsonify(SignInResponse(True, "", auth_user).to_dict())

@app.route("/create-account", methods = ["POST"])
def createAccountRequest():
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
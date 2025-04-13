"""
Stores the initial server interface using FLASK.
"""

import sys
import datetime
import random
import string
from typing import Optional

# import sqlite3

from flask_cors import CORS
from flask import Flask, jsonify, request
import jwt
import bcrypt

from src.usr import create_user_dict, SignInRequest
from src.usr import SignInResponse, UserSessions, User, CreateUserRequest
from src.nodes import NetworkNode, get_db_nodes, get_db_node_tags
from src.nodes import get_db_edges, strip_nodes, zip_nodes_and_tags
from src.graph import Graph
from src.db import open_db

active_users = UserSessions()
# db: sqlite3.Connection = None
graph: Graph
nodes: dict[int: NetworkNode] = {}
all_users: dict[str: User] = {}
new_users: list[User] = []

SECRET_KEY = "jwt-encryption"

app = Flask(__name__)
CORS(app,
     origins=["http://localhost:4200"],
     supports_credentials=True,
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type",
                    "Authorization",
                    "ngrok-skip-browser-warning",
                    "token",
                    "lat",
                    "long",
                    "start",
                    "end"],
     expose_headers=["Content-Type", "Authorization"]
     )

def generate_token(user: User) -> str:
    """
    Generates a JWT token for the passed `User`. 
    """
    payload = {
        "sub": user.username,
        "name": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def is_token_valid(token: str) -> bool:
    """ 
    Attempts to decode a specific JWT, and returns `False` if the token is invalid, or expired.
    """
    try:
        _ = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        print("Token is expired")
        return False
    except jwt.InvalidTokenError as e:
        print(f"The token is invalid '{e}'")
        return False

@app.route("/login", methods = ["POST"])
def login_request():
    """
    Provides the functionality for the login request. 
    It will decode a `SignInRequest`, and then attempt to lookup the user, 
    and validate the sign in.
    """

    msg = request.get_json()
    decoded: SignInRequest = SignInRequest.from_dict(msg)
    if decoded is None:
        return jsonify(SignInResponse(False, "Unable to decode request", None).to_dict()), 400

    try:
        found: Optional[User] = all_users[decoded.username]
    except KeyError:
        found = None

    if found is None:
        return jsonify(
            SignInResponse(
                False,
                "User credentials could not be found.",
                None
            ).to_dict()
        ), 401

    if active_users.user_signed_in(found) is not None:
        return jsonify(SignInResponse(False, "The user is already signed in.", None).to_dict()), 409

    salt = found.salt
    password = decoded.password.encode()
    hashed_password = bcrypt.hashpw(password, salt)

    if not bcrypt.checkpw(found.password, hashed_password):
        return jsonify(
            SignInResponse(
                False,
                "User credentials did not match.", 
                None
            ).to_dict()
        ), 401

    token = generate_token(found)
    active_users.auth_user(token, found)

    return jsonify(SignInResponse(True, "", token).to_dict()), 200

@app.route("/create-account", methods = ["POST"])
def create_account_request():
    """
    Processes a `CreateUserRequest` to create a user on the server.
    """

    msg = request.get_json()
    decoded: CreateUserRequest = CreateUserRequest.from_dict(msg)
    if decoded is None:
        return jsonify(SignInResponse(False, "Unable to decode request", None).to_dict()), 400

    try:
        found = all_users[decoded.username]
    except KeyError:
        found = None

    if found is not None:
        return jsonify(
            SignInResponse(
                False,
                "The user is already created with that username",
                None
            ).to_dict()
        ), 409

    salt = bcrypt.gensalt()
    password = bcrypt.hashpw(decoded.password, salt)
    db_user = User(0, decoded.username, password, salt)

    all_users[db_user.username] = db_user
    new_users.append(db_user)

    token = generate_token(db_user)
    active_users.auth_user(token, db_user)

    return jsonify(SignInResponse(True, "", token).to_dict()), 200

@app.route("/validate-token", methods = ["POST"])
def validate_token():
    """
    Validates the JWT provided by the client. 
    """
    token = request.get_json()
    ret_jwt = token["token"]

    if is_token_valid(ret_jwt):
        return jsonify({
            "valid": True,
            "message": ""
        }), 200

    return jsonify({
        "valid": False,
        "message": "Token is expired"
    }), 200

@app.route("/sign-out", methods = ["POST"])
def sign_out():
    """
    Removes the user's JWT from the server
    """

    print("got sign out request from user")
    token = request.get_json()
    ret_jwt = token["token"]

    if ret_jwt in active_users.users:
        active_users.users.remove(ret_jwt)

@app.route("/map-nodes", methods = ["GET"])
def get_map_nodes():
    """
    Retrieves the nodes from the internal database, and provides it to the user.
    """

    if graph is None:
        return jsonify({}), 503

    return jsonify(nodes), 200

@app.route("/traverse", methods = ["GET"])
def fetch_nodes_to_traverse():
    """
    Processes a request from the client to go from a source node to a destination one. 
    This requires JWT authentication. 
    """

    get_jwt = request.args.get("token", None)
    source = request.args.get("start", 0, type=int)
    dest = request.args.get("end", str(), type=str)
    is_group = request.args.get("is_group", False, type=bool)

    if get_jwt is None or source is None or dest is None:
        return jsonify({}), 400

    if not is_token_valid(get_jwt):
        return jsonify({}), 401

    if not is_group:
        dest = int(dest)
        result = graph.shortest_node_path(source, dest)
    else:
        result = graph.shortest_group_path(source, dest)

    if result is None:
        return jsonify({}), 404

    result_nodes = result.data.points
    return jsonify(result_nodes), 200

if __name__ == "__main__":
    print("Starting server...\n")

    db = open_db("data.sqlite")
    if db is None:
        print("Unable to open database. Exiting")
        sys.exit(1)

    cursor = db.cursor()
    db_nodes = get_db_nodes(cursor)
    db_tags = get_db_node_tags(cursor)
    db_users = User.get_all_users(cursor)

    all_users = create_user_dict(db_users)

    if db_nodes is None or db_tags is None:
        print("Unable to get database information. Exiting")
        sys.exit(2)

    graph = Graph(db_nodes, "dijkstra.json")
    nodes = zip_nodes_and_tags(db_nodes, db_tags)

    app.run(debug = True)

    for new_user in new_users:
        new_user.insert_db(cursor)

    db.commit()
    # app.run(debug = True, ssl_context = ('server.crt', 'server.key'))

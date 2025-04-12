"""
Stores the initial server interface using FLASK.
"""

import sys
import datetime
from typing import Optional

# import sqlite3

from flask_cors import CORS
from flask import Flask, jsonify, request
import jwt
import bcrypt

from src.usr import create_user_dict
from usr import SignInRequest, SignInResponse, UserSessions, User, CreateUserRequest
from nodes import NetworkNode, get_db_nodes, get_db_node_tags
from nodes import get_db_edges, strip_nodes, zip_nodes_and_tags
from graph import Graph
from db import open_db

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

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:4200')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,ngrok-skip-browser-warning,token,lat,long,start,end')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def generate_token(user: User) -> str:
    """
    Generates a JWT token for the passed `User`. 
    """
    payload = {
        "sub": user.username,
        "name": user.username,
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
    except jwt.InvalidTokenError:
        print("The token is invalid")
        return False

@app.route('/login', methods=['OPTIONS'])
def handle_options():
    # This route handles the preflight OPTIONS request
    response = app.make_default_options_response()
    return response

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

@app.route("/map-nodes", methods = ["GET"])
def get_map_nodes():
    """
    Retreives the nodes from the internal database, and provides it to the user. 
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
    source = request.args.get("src", 0, type=int)
    dest = request.args.get("dest", 0, type=int)

    if get_jwt is None or source is None or dest is None:
        return jsonify({}), 400

    if not is_token_valid(get_jwt):
        return jsonify({}), 401

    result = graph.shortest_path(source, dest)
    if result is None:
        return jsonify({}), 404

    result_nodes = result[0]
    return jsonify(result_nodes), 200

if __name__ == "__main__":
    print("Starting server...\n")

    db = open_db("data.sqlite")
    if db is None:
        print("Unable to open database. Exiting")
        sys.exit(1)

    cursor = db.cursor()
    db_nodes = get_db_nodes(cursor)
    db_edges = get_db_edges(cursor)
    db_tags = get_db_node_tags(cursor)
    db_users = User.get_all_users(cursor)

    all_users = create_user_dict(db_users)

    if db_nodes is None or db_edges is None or db_tags is None:
        print("Unable to get database information. Exiting")
        sys.exit(2)

    graph_nodes = strip_nodes(db_nodes)
    graph = Graph(graph_nodes, db_edges)

    nodes = zip_nodes_and_tags(db_nodes, db_tags)

    app.run(debug = True)

    for new_user in new_users:
        new_user.insert_db(cursor)

    db.commit()
    # app.run(debug = True, ssl_context = ('server.crt', 'server.key'))

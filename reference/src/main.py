"""
Stores the initial server interface using FLASK.
"""

import sys
import datetime
import random
import string
from typing import Optional

from flask_cors import CORS
from flask import Flask, jsonify, request
import jwt
import bcrypt

from usr import create_user_dict, SignInRequest
from usr import SignInResponse, UserSessions, User, CreateUserRequest
from nodes import NetworkNode, get_db_nodes, get_db_node_tags
from nodes import zip_nodes_and_tags
from graph import Graph, TraverseRequest, GraphError
from db import open_db

# Who is signed in
active_users = UserSessions()
# The graph data structure used for lookups
graph: Graph
# All nodes to send to the client
nodes: dict[int: NetworkNode] = {}
# All users known to the server (username -> User)
all_users: dict[str: User] = {}
# All new users created this session, that will be added to the database.
new_users: list[User] = []

# For true production, this will need to be kept in a more secure manner.
SECRET_KEY = "jwt-encryption"

app = Flask(__name__)
CORS(app,
     origins=["http://localhost:4200",  "https://langtowl.com"],
     supports_credentials=True,
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type",
                    "Authorization",
                    "ngrok-skip-browser-warning",
                    "token",
                    "lat",
                    "long",
                    "start",
                    "end",
                    "is_group"],
     expose_headers=["Content-Type", "Authorization"]
     )

def generate_token(user: User) -> str:
    """
    Generates a JWT token for the passed `User`. 
    """
    payload = {
        "sub": user.username,
        # We dont truly have a 'name' parameter.
        "name": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        # We want it to last for 2 hours
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

    # First, we lookup the user
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

    # Compare the passwords, using the user's salt.
    salt = found.salt
    password = decoded.password.encode()
    hashed_password = bcrypt.hashpw(password, salt)

    if found.password != hashed_password:
        return jsonify(
            SignInResponse(
                False,
                "User credentials did not match.", 
                None
            ).to_dict()
        ), 401

    # Success! Generate the token and send it back to the front.
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

    # We lookup this new username to see if it already exists. We do not want it to.
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

    # Since this is a new user, we make a new salt, and store it with the user.
    salt = bcrypt.gensalt()
    password = bcrypt.hashpw(decoded.password, salt)
    db_user = User(0, decoded.username, password, salt)

    # Notate the user so that it can be used later on
    all_users[db_user.username] = db_user
    new_users.append(db_user) # Register it for saving

    # Lastly, generate the token and send it back.
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
        try:
            active_users.users.pop(ret_jwt)
        except KeyError:
            print(f"Attempted to remove jwt '{ret_jwt}' from system, but it was not found.")

@app.route("/map-nodes", methods = ["GET"])
def get_map_nodes():
    """
    Retrieves the nodes from the internal database, and provides it to the user.
    """

    if graph is None:
        return jsonify({}), 503

    result: dict[int: dict] = {}
    for (n_id, node) in nodes.items():
        result[n_id] = node.to_dict()
    return jsonify(result), 200

@app.route("/traverse", methods = ["POST"])
def fetch_nodes_to_traverse():
    """
    Processes a request from the client to go from a source node to a destination one. 
    This requires JWT authentication. 
    """

    raw_message = request.get_json()
    message = TraverseRequest.from_dict(raw_message)
    if message is None:
        return jsonify({}), 400

    # It is important that the correct path finding approach is used.
    if not message.is_group:
        result = graph.shortest_node_path(message.source, message.dest)
    else:
        result = graph.shortest_group_path(message.source, message.dest)

    if result is None:
        return jsonify({}), 404

    result_nodes = result.points
    return jsonify({"ids": result_nodes}), 200

if __name__ == "__main__":
    print("Starting server...\n")

    # Requests the database for object retrival
    db = open_db("data.sqlite")
    if db is None:
        print("Unable to open database. Exiting")
        sys.exit(1)

    # load up all DB information
    cursor = db.cursor()
    db_nodes = get_db_nodes(cursor)
    db_tags = get_db_node_tags(cursor)
    db_users = User.get_all_users(cursor)

    # Map users
    # 
    all_users = create_user_dict(db_users)

    if db_nodes is None or db_tags is None:
        print("Unable to get database information. Exiting")
        sys.exit(2)

    # load graph data
    try:
        graph = Graph(db_nodes, "dijkstra.json")
    except GraphError as e:
        print(f"The graph was not able to load, error '{e}'. Please ensure the data path is valid.")

    try:
        nodes = zip_nodes_and_tags(db_nodes, db_tags)
    except ValueError as e:
        print(
            f"""
            One or more data anomalies were found.
            Please ensure the data in the database is valid. Inner error '{e}'
            """)

    app.run(debug = True, ssl_context = ('server.crt', 'server.key'))

    # now that the app has finished, we can insert all new users.
    print(f"Commiting {len(new_users)} to the database...")
    for new_user in new_users:
        new_user.insert_db(cursor)

    db.commit()
    print("All tasks completed.")

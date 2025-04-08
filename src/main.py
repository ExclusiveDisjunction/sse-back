from flask_cors import CORS
from flask import Flask, jsonify, request, make_response

import sqlite3
import jwt
import datetime
from usr import SignInRequest, SignInResponse, UserSessions, User, AuthenticatedUser, CreateUserRequest
from nodes import NetworkNode, get_db_nodes, get_db_node_tags, get_db_edges, strip_nodes, zip_nodes_and_tags
from graph import Graph
from db import open_db

active_users = UserSessions()
db: sqlite3.Connection = None
graph: Graph = None
nodes: dict[int: NetworkNode] = {}

SECRET_KEY = "jwt-encryption"

def generate_token(user: User) -> str: 
    payload = {
        "sub": user.net.username,
        "name": user.net.fname,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def is_token_valid(token: str) -> bool:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except: 
        return False

app = Flask(__name__)
CORS(app,
     origins=["http://localhost:4200"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "ngrok-skip-browser-warning", "token", "lat", "long", "start", "end"]
     )

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

    found: User | None = User.lookup_db(db.cursor(), decoded.username)
    if found is None:
        return jsonify(SignInResponse(False, "User credentials could not be found.").to_dict()), 401
    
    if active_users.user_signed_in(found) is not None:
        return jsonify(SignInResponse(False, "The user is already signed in.").to_dict()), 409
    
    if found.password_hash != decoded.password: 
        return jsonify(SignInResponse(False, "User credentials did not match.").to_dict()), 401

    token = generate_token()
    active_users.auth_user(token, found)

    auth_user = AuthenticatedUser(found.net, token)
    return jsonify(SignInResponse(True, "", auth_user).to_dict()), 200

@app.route("/create-account", methods = ["POST"])
def createAccountRequest():
    global active_users
    global db

    msg = request.get_json()
    decoded: CreateUserRequest | None = CreateUserRequest.from_dict(msg)
    if decoded is None:
        return jsonify(SignInResponse(False, "Unable to decode request", None).to_dict()), 400
    
    user_to_make = decoded.user

    if db is None:
        return jsonify(SignInResponse(False, "User authentication service is unavailable").to_dict()), 503

    found: User | None = User.lookup_db(db.cursor(), user_to_make.username)
    if found is not None:
        return jsonify(SignInResponse(False, "The user is already created with that username").to_dict()), 409
    
    if active_users.user_signed_in(found) is not None:
        return jsonify(SignInResponse(False, "The user is already signed in.").to_dict()), 409
    
    db_user = User(0, user_to_make, decoded.password)
    if not db_user.insert_db(db.cursor()):
        return jsonify(SignInResponse(False, "The user could not be created.").to_dict()), 417

    token = generate_token()
    active_users.auth_user(token, db_user)

    auth_user = AuthenticatedUser(user_to_make, token)
    return jsonify(SignInResponse(True, "", auth_user).to_dict()), 200

@app.route("/validate-token", methods = ["POST"])
def validateToken():
    token = request.get_json()
    jwt = token["token"]

    if is_token_valid(jwt):
        return jsonify({ 
            "valid": True,
            "message": ""
        }), 200
    else: 
        return jsonify( {
            "valid": False,
            "message": "Token is expired"
        }), 200

@app.route("/map-nodes", methods = ["GET"])
def getMapNodes():
    global graph
    global nodes

    if graph is None:
        return jsonify({}), 503

    return jsonify(nodes), 200

@app.route("/traverse", methods = ["GET"])
def fetchNodesToTraverse():
    global graph 

    jwt = request.args.get("token", None, type=str)
    source = request.args.get("src", None, type=int)
    dest = request.args.get("dest", None, type=int)

    if jwt is None or source is None or dest is None:
        return jsonify({}), 400

    if not is_token_valid(jwt):
        return jsonify({}), 401
    
    result = graph.shortest_path(source, int)
    if result is None:
        return jsonify({}), 404
    
    nodes = result[0]
    return jsonify(nodes), 200

if __name__ == "__main__":
    print("Starting server...\n")

    db = open_db("data.sqlite")
    if db is None:
        print("Unable to open database. Exiting")
        exit(1)

    db_nodes = get_db_nodes(db.cursor())
    db_edges = get_db_edges(db.cursor())
    db_tags = get_db_node_tags(db.cursor())

    if db_nodes is None or db_edges is None or db_tags is None:
        print("Unable to get database information. Exiting")
        exit(2)

    graph_nodes = strip_nodes(db_nodes)
    graph = Graph(graph_nodes, db_edges)

    nodes = zip_nodes_and_tags(db_nodes, db_tags)

    app.run(debug = False)

    db.commit()
    # app.run(debug = True, ssl_context = ('server.crt', 'server.key'))
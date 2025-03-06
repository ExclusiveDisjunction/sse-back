from flask_cors import CORS
from flask import Flask, jsonify, request, make_response

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


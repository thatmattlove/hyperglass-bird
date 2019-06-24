"""
hyperglass-bird API Controller
"""
# Standard Imports
import json
import logging

# Module Imports
import logzero
from logzero import logger
from waitress import serve
from passlib.hash import pbkdf2_sha256
from flask import Flask, request, Response

# Project Imports
import execute
import configuration

# Logzero Configuration
if configuration.debug_state():
    logzero.loglevel(logging.DEBUG)
else:
    logzero.loglevel(logging.INFO)

# Import API Parameters
api = configuration.api()
logger.debug(f"API parameters: {api}")

# Flask Configuration
app = Flask(__name__)


@app.route("/bird", methods=["POST"])
def bird():
    """Main Flask route ingests JSON parameters and API key hash from hyperglass and passes it to \
    execute module for execution"""
    headers = request.headers
    logger.debug(f"Request headers:\n{headers}")
    api_key_hash = headers.get("X-Api-Key")
    # Verify API key hash against plain text value in configuration.py
    if pbkdf2_sha256.verify(api["key"], api_key_hash) is True:
        logger.debug("Verified API Key")

        query_json = request.get_json()
        logger.debug(f"Raw JSON Query:\n{query_json}")
        query = json.loads(query_json)
        logger.debug(f"Input query data:\n{query}")
        logger.debug("Executing query...")

        bird_response = execute.execute(query)

        logger.debug(f"Raw output:\n{bird_response}")

        return Response(bird_response[0], bird_response[1])
    logger.error(f"Validation of API key failed. Hash:\n{api_key_hash}")
    return Response("Error: API Key Invalid", 401)


# Simple Waitress WSGI implementation
if __name__ == "__main__":
    logger.debug("Starting hyperglass-bird API via Waitress...")
    serve(app, host=api["listen_addr"], port=api["port"])

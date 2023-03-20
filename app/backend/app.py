from flask import Flask, request, jsonify, make_response
import requests
import json
from dotenv import load_dotenv
import os
import logging

load_dotenv()
app = Flask(__name__)

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)

@app.route("/ask", methods=["POST"])
def ask():
    chainType=request.json["chainType"]
    question=request.json["question"]
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    postBody=request.json["postBody"]
 
    logging.info(f"chainType: {chainType}")
    logging.info(f"question: {question}")
    logging.info(f"indexType: {indexType}")
    logging.info(f"indexNs: {indexNs}")
    
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("QA_URL")

        data = postBody
        params = {'chainType': chainType, 'question': question, 'indexType': indexType, "indexNs": indexNs }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /ask")
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    postBody=request.json["postBody"]
 
    logging.info(f"indexType: {indexType}")
    logging.info(f"indexNs: {indexNs}")
    
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("CHAT_URL")

        data = postBody
        params = {'indexType': indexType, "indexNs": indexNs }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500


@app.route("/chat3", methods=["POST"])
def chat3():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    question=request.json["question"]
    postBody=request.json["postBody"]
 
    logging.info(f"indexType: {indexType}")
    logging.info(f"indexNs: {indexNs}")
    
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("CHAT3_URL")

        data = postBody
        params = {'indexType': indexType, "indexNs": indexNs, "question": question }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /chat3")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run()

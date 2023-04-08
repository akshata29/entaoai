from flask import Flask, request, jsonify, make_response
import requests
import json
from dotenv import load_dotenv
import os
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
import base64

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

@app.route("/sqlChat", methods=["POST"])
def sqlChat():
    question=request.json["question"]
    top=request.json["top"]
    postBody=request.json["postBody"]

    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SQLCHAT_URL")

        data = postBody
        params = {'question': question, 'topK': top, }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /sqlChat")
        return jsonify({"error": str(e)}), 500
    
@app.route("/processDoc", methods=["POST"])
def processDoc():
    indexType=request.json["indexType"]
    indexName=request.json["indexName"]
    multiple=request.json["multiple"]
    loadType=request.json["loadType"]
    postBody=request.json["postBody"]
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("DOCGENERATOR_URL")

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "multiple": multiple , "loadType": loadType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /processDoc")
        return jsonify({"error": str(e)}), 500

@app.route("/refreshIndex", methods=["GET"])
def refreshIndex():
   
    try:
        url = os.environ.get("BLOB_CONNECTION_STRING")
        containerName = os.environ.get("BLOB_CONTAINER_NAME")
        blobClient = BlobServiceClient.from_connection_string(url)
        containerClient = blobClient.get_container_client(container=containerName)
        blobList = containerClient.list_blobs(include=['tags', 'metadata'])
        blobJson = []
        for blob in blobList:
            #print(blob)
            try:
                blobJson.append({
                    "embedded": blob.metadata["embedded"],
                    "indexName": blob.metadata["indexName"],
                    "namespace":blob.metadata["namespace"],
                    "qa":blob.metadata["qa"],
                    "summary":blob.metadata["summary"],
                    "name":blob.name,
                    "indexType":blob.metadata["indexType"],
                })
            except Exception as e:
                pass

        #jsonDict = json.dumps(blobJson)
        return jsonify({"values" : blobJson})
    except Exception as e:
        logging.exception("Exception in /refreshIndex")
        return jsonify({"error": str(e)}), 500

@app.route("/uploadFile", methods=["POST"])
def uploadFile():
   
    try:
        fileName=request.json["fileName"]
        contentType=request.json["contentType"]
        if contentType == "text/plain":
            fileContent = request.json["fileContent"]
        url = os.environ.get("BLOB_CONNECTION_STRING")
        containerName = os.environ.get("BLOB_CONTAINER_NAME")
        blobClient = BlobServiceClient.from_connection_string(url)
        blobClient = blobClient.get_blob_client(container=containerName, blob=fileName)
        #blob_client.upload_blob(bytes_data,overwrite=True, content_settings=ContentSettings(content_type=content_type))
        blobClient.upload_blob(fileContent, overwrite=True, content_settings=ContentSettings(content_type=contentType))
        #jsonDict = json.dumps(blobJson)
        return jsonify({"Status" : "Success"})
    except Exception as e:
        logging.exception("Exception in /uploadFile")
        return jsonify({"error": str(e)}), 500

@app.route("/uploadBinaryFile", methods=["POST"])
def uploadBinaryFile():
   
    try:
        if 'file' not in request.files:
            return jsonify({'message': 'No file in request'}), 400
        
        file = request.files['file']
        fileName = file.filename
        blobName = os.path.basename(fileName)

        url = os.environ.get("BLOB_CONNECTION_STRING")
        containerName = os.environ.get("BLOB_CONTAINER_NAME")
        blobServiceClient = BlobServiceClient.from_connection_string(url)
        containerClient = blobServiceClient.get_container_client(containerName)
        blobClient = containerClient.get_blob_client(blobName)
        #blob_client.upload_blob(bytes_data,overwrite=True, content_settings=ContentSettings(content_type=content_type))
        blobClient.upload_blob(file.read(), overwrite=True)
        #jsonDict = json.dumps(blobJson)
        return jsonify({'message': 'File uploaded successfully'}), 200
    except Exception as e:
        logging.exception("Exception in /uploadBinaryFile")
        return jsonify({"error": str(e)}), 500

@app.route("/secsearch", methods=["POST"])
def secsearch():
    indexType=request.json["indexType"]
    indexName=request.json["indexName"]
    question=request.json["question"]
    top=request.json["top"]
    postBody=request.json["postBody"]
  
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SECSEARCH_URL")

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "question": question, "top": top }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /secsearch")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()

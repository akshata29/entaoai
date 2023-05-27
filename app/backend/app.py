from flask import Flask, request, jsonify, make_response
import requests
import json
from dotenv import load_dotenv
import os
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
import base64
import mimetypes
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import (
    TextAnalyticsClient,
    RecognizeEntitiesAction,
    AnalyzeSentimentAction,
    RecognizePiiEntitiesAction,
    ExtractKeyPhrasesAction,
)
import azure.cognitiveservices.speech as speechsdk

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

@app.route("/askAgent", methods=["POST"])
def askAgent():
    postBody=request.json["postBody"]
 
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("AGENTQA_URL")

        data = postBody
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /askAgent")
        return jsonify({"error": str(e)}), 500

@app.route("/smartAgent", methods=["POST"])
def smartAgent():
    postBody=request.json["postBody"]
 
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SMARTAGENT_URL")

        data = postBody
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /smartAgent")
        return jsonify({"error": str(e)}), 500
    
@app.route("/askTaskAgent", methods=["POST"])
def askTaskAgent():
    postBody=request.json["postBody"]
 
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("TASKAGENTQA_URL")

        data = postBody
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /askTaskAgent")
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

@app.route("/summaryAndQa", methods=["POST"])
def summaryAndQa():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    embeddingModelType=request.json["embeddingModelType"]
    requestType=request.json["requestType"]
    chainType=request.json["chainType"]
    postBody=request.json["postBody"]
    
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SUMMARYQA_URL")

        data = postBody
        params = {'indexType': indexType, "indexNs": indexNs, 'embeddingModelType': embeddingModelType, "requestType": requestType,
                  'chainType': chainType  }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /summaryAndQa")
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
    embeddingModelType = request.json["embeddingModelType"]
    postBody=request.json["postBody"]

    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SQLCHAT_URL")

        data = postBody
        params = {'question': question, 'topK': top, 'embeddingModelType': embeddingModelType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /sqlChat")
        return jsonify({"error": str(e)}), 500

@app.route("/sqlChain", methods=["POST"])
def sqlChain():
    question=request.json["question"]
    top=request.json["top"]
    embeddingModelType=request.json["embeddingModelType"]
    postBody=request.json["postBody"]

    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SQLCHAIN_URL")

        data = postBody
        params = {'question': question, 'topK': top, 'embeddingModelType': embeddingModelType }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /sqlChain")
        return jsonify({"error": str(e)}), 500
    
@app.route("/processDoc", methods=["POST"])
def processDoc():
    indexType=request.json["indexType"]
    indexName=request.json["indexName"]
    multiple=request.json["multiple"]
    loadType=request.json["loadType"]
    existingIndex=request.json["existingIndex"]
    existingIndexNs=request.json["existingIndexNs"]
    embeddingModelType=request.json["embeddingModelType"]
    textSplitter=request.json["textSplitter"]
    postBody=request.json["postBody"]
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("DOCGENERATOR_URL")

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "multiple": multiple , "loadType": loadType,
                  "existingIndex": existingIndex, "existingIndexNs": existingIndexNs, "embeddingModelType": embeddingModelType,
                  "textSplitter": textSplitter}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /processDoc")
        return jsonify({"error": str(e)}), 500

@app.route("/processSummary", methods=["POST"])
def processSummary():
    multiple=request.json["multiple"]
    loadType=request.json["loadType"]
    embeddingModelType=request.json["embeddingModelType"]
    chainType=request.json["chainType"]
    postBody=request.json["postBody"]
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("PROCESSSUMMARY_URL")

        data = postBody
        params = { "multiple": multiple , "loadType": loadType, "embeddingModelType": embeddingModelType, "chainType": chainType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /processSummary")
        return jsonify({"error": str(e)}), 500
    
@app.route("/convertCode", methods=["POST"])
def convertCode():
    inputLanguage=request.json["inputLanguage"]
    outputLanguage=request.json["outputLanguage"]
    modelName=request.json["modelName"]
    embeddingModelType=request.json["embeddingModelType"]
    postBody=request.json["postBody"]
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("CONVERTCODE_URL")

        data = postBody
        params = {'inputLanguage': inputLanguage, "outputLanguage": outputLanguage, "modelName": modelName , 
                  "embeddingModelType": embeddingModelType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /convertCode")
        return jsonify({"error": str(e)}), 500

@app.route("/promptGuru", methods=["POST"])
def promptGuru():
    task=request.json["task"]
    modelName=request.json["modelName"]
    embeddingModelType=request.json["embeddingModelType"]
    postBody=request.json["postBody"]
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("PROMPTGURU_URL")

        data = postBody
        params = {'task': task, "modelName": modelName , 
                  "embeddingModelType": embeddingModelType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /promptGuru")
        return jsonify({"error": str(e)}), 500
    
@app.route("/verifyPassword", methods=["POST"])
def verifyPassword():
    passType=request.json["passType"]
    password=request.json["password"]
    postBody=request.json["postBody"]

    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("VERIFYPASS_URL")

        data = postBody
        params = {'passType': passType, "password": password}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /verifyPassword")
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
                    "qa": blob.metadata["qa"],
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

@app.route("/indexManagement", methods=["POST"])
def indexManagement():
   
    try:
        indexType=request.json["indexType"]
        indexName=request.json["indexName"]
        blobName=request.json["blobName"]
        indexNs=request.json["indexNs"]
        operation=request.json["operation"]    
        postBody=request.json["postBody"]

        headers = {'content-type': 'application/json'}
        url = os.environ.get("INDEXMANAGEMENT_URL")

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "blobName": blobName , "indexNs": indexNs, "operation": operation}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)

    except Exception as e:
        logging.exception("Exception in /indexManagement")
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
        blobContainer = blobClient.get_blob_client(container=containerName, blob=fileName)
        #blob_client.upload_blob(bytes_data,overwrite=True, content_settings=ContentSettings(content_type=content_type))
        blobContainer.upload_blob(fileContent, overwrite=True, content_settings=ContentSettings(content_type=contentType))
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
        blobClient.set_blob_metadata(metadata={"embedded": "false", 
                                        "indexName": "",
                                        "namespace": "", 
                                        "qa": "No Qa Generated",
                                        "summary": "No Summary Created", 
                                        "indexType": ""})
        #jsonDict = json.dumps(blobJson)
        return jsonify({'message': 'File uploaded successfully'}), 200
    except Exception as e:
        logging.exception("Exception in /uploadBinaryFile")
        return jsonify({"error": str(e)}), 500

@app.route("/uploadSummaryBinaryFile", methods=["POST"])
def uploadSummaryBinaryFile():
   
    try:
        if 'file' not in request.files:
            return jsonify({'message': 'No file in request'}), 400
        
        file = request.files['file']
        fileName = file.filename
        blobName = os.path.basename(fileName)

        url = os.environ.get("BLOB_CONNECTION_STRING")
        summaryContainerName = os.environ.get("BLOB_SUMMARY_CONTAINER_NAME")
        blobServiceClient = BlobServiceClient.from_connection_string(url)
        containerClient = blobServiceClient.get_container_client(summaryContainerName)
        blobClient = containerClient.get_blob_client(blobName)
        #blob_client.upload_blob(bytes_data,overwrite=True, content_settings=ContentSettings(content_type=content_type))
        blobClient.upload_blob(file.read(), overwrite=True)
        return jsonify({'message': 'File uploaded successfully'}), 200
    except Exception as e:
        logging.exception("Exception in /uploadSummaryBinaryFile")
        return jsonify({"error": str(e)}), 500

# Serve content files from blob storage from within the app to keep the example self-contained. 
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.
#@app.route("/content/<path>")
@app.route('/content/', defaults={'path': '<path>'})
@app.route('/content/<path:path>')
def content_file(path):
    url = os.environ.get("BLOB_CONNECTION_STRING")
    containerName = os.environ.get("BLOB_CONTAINER_NAME")
    blobClient = BlobServiceClient.from_connection_string(url)
    logging.info(f"Getting blob {path}")
    blobContainer = blobClient.get_container_client(container=containerName)
    blob = blobContainer.get_blob_client(path).download_blob()
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return blob.readall(), 200, {"Content-Type": mime_type, "Content-Disposition": f"inline; filename={path}"}
    

@app.route("/secsearch", methods=["POST"])
def secsearch():
    indexType=request.json["indexType"]
    indexName=request.json["indexName"]
    question=request.json["question"]
    top=request.json["top"]
    embeddingModelType=request.json["embeddingModelType"]
    postBody=request.json["postBody"]
  
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SECSEARCH_URL")

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "question": question, "top": top, "embeddingModelType": embeddingModelType }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /secsearch")
        return jsonify({"error": str(e)}), 500

@app.route("/speechToken", methods=["POST"])
def speechToken():
  
    try:
        headers = { 'Ocp-Apim-Subscription-Key': os.environ.get("SPEECH_KEY"), 'content-type': 'application/x-www-form-urlencoded'}
        url = 'https://' + os.environ.get("SPEECH_REGION") + '.api.cognitive.microsoft.com/sts/v1.0/issueToken'
        resp = requests.post(url, headers=headers)
        accessToken = str(resp.text)
        return jsonify({"Token" : accessToken, "Region": os.environ.get("SPEECH_REGION")})
    except Exception as e:
        logging.exception("Exception in /speechToken")
        return jsonify({"error": str(e)}), 500

@app.route("/textAnalytics", methods=["POST"])
def textAnalytics():
  
    try:
        credential = AzureKeyCredential(os.environ.get("TEXTANALYTICS_KEY"))
        taClient = TextAnalyticsClient(endpoint="https://" + os.environ.get("TEXTANALYTICS_REGION") + ".api.cognitive.microsoft.com/", credential=credential)
        documentText=request.json["documentText"]
        if (len(documentText) > 0):
            documents = []
            documents.append(documentText)

            headers = { 'content-type': 'application/json'}

            poller = taClient.begin_analyze_actions(
                documents,
                display_name="Speech Analytics",
                actions=[
                    RecognizeEntitiesAction(),
                    AnalyzeSentimentAction(),
                    RecognizePiiEntitiesAction(),
                    ExtractKeyPhrasesAction(),
                ]
            )
            docResults = poller.result()
            entities = ''
            piiEntities = ""

            for doc, action_results in zip(documents, docResults):
                for result in action_results:
                    if result.kind == "EntityRecognition":
                        for entity in result.entities:
                            entities = entities + "......Entity: " + entity.text + ".........Category: " + entity.category
                    elif result.kind == "PiiEntityRecognition":
                            for entity in result.entities:
                                piiEntities = piiEntities + "......Entity: " + entity.text + ".........Category: " + entity.category
                    elif result.kind == "KeyPhraseExtraction":
                        keyPhrases = ' '.join(result.key_phrases)
                    elif result.kind == "SentimentAnalysis":
                        sentiment = 'Overall sentiment: ' + result.sentiment +  ' Scores: positive=' + str(result.confidence_scores.positive) + " neutral=" + str(result.confidence_scores.neutral) + " negative=" + str(result.confidence_scores.negative)
            nlpText = ''
            if len(keyPhrases.strip()) > 0:
                nlpText = 'Key Phrases: ' + keyPhrases + '\n'
            nlpText = nlpText + sentiment + '\n'
            if len(entities.strip()) > 0:
                nlpText =  nlpText +  "Entities : " + entities + '\n' 
            if len(piiEntities.strip()) > 0:
                nlpText = nlpText + "PII Entities : " + piiEntities + '\n'

        else:
            nlpText = ''
        return jsonify({"TextAnalytics" : nlpText})
    except Exception as e:
        logging.exception("Exception in /textAnalytics")
        return jsonify({"error": str(e)}), 500

@app.route("/summarizer", methods=["POST"])
def summarizer():
    docType=request.json["docType"]
    chainType=request.json["chainType"]
    promptName=request.json["promptName"]
    promptType=request.json["promptType"]
    postBody=request.json["postBody"]
     
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("SUMMARIZER_URL")

        data = postBody
        params = {'docType': docType, "chainType": chainType, "promptName": promptName, "promptType": promptType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /summarizer")
        return jsonify({"error": str(e)}), 500

@app.route("/speech", methods=["POST"])
def speech():
    text = request.json["text"]
    try:
        speechKey = os.environ.get("SPEECH_KEY")
        speechRegion = os.environ.get("SPEECH_REGION")
        speech_config = speechsdk.SpeechConfig(subscription=speechKey, region=speechRegion)
        speech_config.speech_synthesis_voice_name='en-US-SaraNeural'
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        return result.audio_data, 200, {"Content-Type": "audio/wav"}
    except Exception as e:
        logging.exception("Exception in /speech")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()

from flask import Flask, request, jsonify, make_response, Response
import requests
import json
from dotenv import load_dotenv
import os
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
import mimetypes
from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.cosmos import CosmosClient, PartitionKey
from Utilities.fmp import *
from distutils.util import strtobool
from Utilities.ChatGptStream import *

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

    #print(f"combinedParams: {json.dumps(combinedParams)}")
    
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

def formatNdJson(r):
    for data in r:
        yield json.dumps(data).replace("\n", "\\n") + "\n"

@app.route("/chatStream", methods=["POST"])
def chatStream():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    postBody=request.json["postBody"]
 
    logging.info(f"indexType: {indexType}")
    logging.info(f"indexNs: {indexNs}")
    
    try:

        OpenAiKey = os.environ['OpenAiKey']
        OpenAiVersion = os.environ['OpenAiVersion']
        OpenAiChat = os.environ['OpenAiChat']
        OpenAiEndPoint = os.environ['OpenAiEndPoint']

        if "OpenAiChat16k" in os.environ: 
            OpenAiChat16k = os.getenv('OpenAiChat16k')
        else:
            OpenAiChat16k = "chat16k"

        if "OpenAiApiKey" in os.environ: 
            OpenAiApiKey = os.getenv('OpenAiApiKey')
        else:
            OpenAiApiKey = ""

        if "SEARCHKEY" in os.environ: 
            SearchKey = os.environ['SEARCHKEY']
        else:
            SearchKey = ""

        if "SEARCHSERVICE" in os.environ: 
            SearchService = os.environ['SEARCHSERVICE']
        else:
            SearchService = ""

        if "OpenAiEmbedding" in os.environ: 
            OpenAiEmbedding = os.environ['OpenAiEmbedding']
        else:
            OpenAiEmbedding = "embedding"

        if "RedisAddress" in os.environ: 
            RedisAddress = os.environ['RedisAddress']
        else:
            RedisAddress = ""

        if "RedisPort" in os.environ: 
            RedisPort = os.environ['RedisPort']
        else:
            RedisPort = ""

        if "RedisPassword" in os.environ: 
            RedisPassword = os.environ['RedisPassword']
        else:
            RedisPassword = "embedding"

        if "PineconeEnv" in os.environ: 
            PineconeEnv = os.environ['PineconeEnv']
        else:
            PineconeEnv = ""

        if "PineconeKey" in os.environ: 
            PineconeKey = os.environ['PineconeKey']
        else:
            PineconeKey = ""

        if "VsIndexName" in os.environ: 
            VsIndexName = os.environ['VsIndexName']
        else:
            VsIndexName = ""

        # data = postBody
        # params = {'indexType': indexType, "indexNs": indexNs }
        # resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        chatStream = ChatGptStream(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiChat, OpenAiChat16k, OpenAiApiKey, OpenAiEmbedding,
                                    SearchService, SearchKey, RedisAddress, RedisPort, RedisPassword,
                                    PineconeKey, PineconeEnv, VsIndexName)
        r = chatStream.run(indexType=indexType, indexNs=indexNs, postBody=postBody)
        return Response(formatNdJson(r), mimetype='text/event-stream')
    except Exception as e:
        logging.exception("Exception in /chatStream")
        return jsonify({"error": str(e)}), 500

@app.route("/chatGpt", methods=["POST"])
def chatGpt():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    postBody=request.json["postBody"]
 
    logging.info(f"indexType: {indexType}")
    logging.info(f"indexNs: {indexNs}")
    
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("CHATGPT_URL")

        data = postBody
        params = {'indexType': indexType, "indexNs": indexNs }
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /chatGpt")
        return jsonify({"error": str(e)}), 500
    
@app.route("/getAllSessions", methods=["POST"])
def getAllSessions():
    indexType=request.json["indexType"]
    feature=request.json["feature"]
    type=request.json["type"]
    
    try:
        CosmosEndPoint = os.environ.get("COSMOSENDPOINT")
        CosmosKey = os.environ.get("COSMOSKEY")
        CosmosDb = os.environ.get("COSMOSDATABASE")
        CosmosContainer = os.environ.get("COSMOSCONTAINER")

        cosmosClient = CosmosClient(url=CosmosEndPoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDb)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)

        cosmosQuery = "SELECT c.sessionId, c.name, c.indexId FROM c WHERE c.type = @type and c.feature = @feature and c.indexType = @indexType"
        params = [dict(name="@type", value=type), 
                  dict(name="@feature", value=feature), 
                  dict(name="@indexType", value=indexType)]
        results = cosmosContainer.query_items(query=cosmosQuery, parameters=params, enable_cross_partition_query=True)
        items = [item for item in results]
        #output = json.dumps(items, indent=True)
        return jsonify(items)
    except Exception as e:
        logging.exception("Exception in /getAllSessions")
        return jsonify({"error": str(e)}), 500
        
@app.route("/getAllIndexSessions", methods=["POST"])
def getAllIndexSessions():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    feature=request.json["feature"]
    type=request.json["type"]
    
    try:
        CosmosEndPoint = os.environ.get("COSMOSENDPOINT")
        CosmosKey = os.environ.get("COSMOSKEY")
        CosmosDb = os.environ.get("COSMOSDATABASE")
        CosmosContainer = os.environ.get("COSMOSCONTAINER")

        cosmosClient = CosmosClient(url=CosmosEndPoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDb)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)

        cosmosQuery = "SELECT c.sessionId, c.name FROM c WHERE c.type = @type and c.feature = @feature and c.indexType = @indexType and c.indexId = @indexNs"
        params = [dict(name="@type", value=type), 
                  dict(name="@feature", value=feature), 
                  dict(name="@indexType", value=indexType), 
                  dict(name="@indexNs", value=indexNs)]
        results = cosmosContainer.query_items(query=cosmosQuery, parameters=params, enable_cross_partition_query=True)
        items = [item for item in results]
        #output = json.dumps(items, indent=True)
        return jsonify(items)
    except Exception as e:
        logging.exception("Exception in /getAllIndexSessions")
        return jsonify({"error": str(e)}), 500
    
@app.route("/getIndexSession", methods=["POST"])
def getIndexSession():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    sessionName=request.json["sessionName"]
    
    try:
        CosmosEndPoint = os.environ.get("COSMOSENDPOINT")
        CosmosKey = os.environ.get("COSMOSKEY")
        CosmosDb = os.environ.get("COSMOSDATABASE")
        CosmosContainer = os.environ.get("COSMOSCONTAINER")

        cosmosClient = CosmosClient(url=CosmosEndPoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDb)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)

        cosmosQuery = "SELECT c.id, c.type, c.sessionId, c.name, c.chainType, \
         c.feature, c.indexId, c.IndexType, c.IndexName, c.llmModel, \
          c.timestamp, c.tokenUsed, c.embeddingModelType FROM c WHERE c.name = @sessionName and c.indexType = @indexType and c.indexId = @indexNs"
        params = [dict(name="@sessionName", value=sessionName), 
                  dict(name="@indexType", value=indexType), 
                  dict(name="@indexNs", value=indexNs)]
        results = cosmosContainer.query_items(query=cosmosQuery, parameters=params, enable_cross_partition_query=True,
                                              max_item_count=1)
        sessions = [item for item in results]
        return jsonify(sessions)
    except Exception as e:
        logging.exception("Exception in /getIndexSession")
        return jsonify({"error": str(e)}), 500
    
@app.route("/deleteIndexSession", methods=["POST"])
def deleteIndexSession():
    indexType=request.json["indexType"]
    indexNs=request.json["indexNs"]
    sessionName=request.json["sessionName"]
    
    try:
        CosmosEndPoint = os.environ.get("COSMOSENDPOINT")
        CosmosKey = os.environ.get("COSMOSKEY")
        CosmosDb = os.environ.get("COSMOSDATABASE")
        CosmosContainer = os.environ.get("COSMOSCONTAINER")

        cosmosClient = CosmosClient(url=CosmosEndPoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDb)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)

        cosmosQuery = "SELECT c.sessionId FROM c WHERE c.name = @sessionName and c.indexType = @indexType and c.indexId = @indexNs"
        params = [dict(name="@sessionName", value=sessionName), 
                  dict(name="@indexType", value=indexType), 
                  dict(name="@indexNs", value=indexNs)]
        results = cosmosContainer.query_items(query=cosmosQuery, parameters=params, enable_cross_partition_query=True,
                                              max_item_count=1)
        sessions = [item for item in results]
        sessionData = json.loads(json.dumps(sessions))[0]
        cosmosAllDocQuery = "SELECT * FROM c WHERE c.sessionId = @sessionId"
        params = [dict(name="@sessionId", value=sessionData['sessionId'])]
        allDocs = cosmosContainer.query_items(query=cosmosAllDocQuery, parameters=params, enable_cross_partition_query=True)
        for i in allDocs:
            cosmosContainer.delete_item(i, partition_key=i["sessionId"])
        
        #deleteQuery = "SELECT c._self FROM c WHERE c.sessionId = '" + sessionData['sessionId'] + "'"
        #result = cosmosContainer.scripts.execute_stored_procedure(sproc="bulkDeleteSproc",params=[deleteQuery], partition_key=cosmosKey)
        #print(result)
        
        #cosmosContainer.delete_all_items_by_partition_key(sessionData['sessionId'])
        return jsonify(sessions)
    except Exception as e:
        logging.exception("Exception in /deleteIndexSession")
        return jsonify({"error": str(e)}), 500
    
@app.route("/renameIndexSession", methods=["POST"])
def renameIndexSession():
    oldSessionName=request.json["oldSessionName"]
    newSessionName=request.json["newSessionName"]
    
    try:
        CosmosEndPoint = os.environ.get("COSMOSENDPOINT")
        CosmosKey = os.environ.get("COSMOSKEY")
        CosmosDb = os.environ.get("COSMOSDATABASE")
        CosmosContainer = os.environ.get("COSMOSCONTAINER")

        cosmosClient = CosmosClient(url=CosmosEndPoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDb)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)

        cosmosQuery = "SELECT * FROM c WHERE c.name = @sessionName and c.type = 'Session'"
        params = [dict(name="@sessionName", value=oldSessionName)]
        results = cosmosContainer.query_items(query=cosmosQuery, parameters=params, enable_cross_partition_query=True,
                                              max_item_count=1)
        sessions = [item for item in results]
        sessionData = json.loads(json.dumps(sessions))[0]
        #selfId = sessionData['_self']
        sessionData['name'] = newSessionName
        cosmosContainer.replace_item(item=sessionData, body=sessionData)
        return jsonify(sessions)
    except Exception as e:
        logging.exception("Exception in /renameIndexSession")
        return jsonify({"error": str(e)}), 500

@app.route("/getIndexSessionDetail", methods=["POST"])
def getIndexSessionDetail():
    sessionId=request.json["sessionId"]
    
    try:
        CosmosEndPoint = os.environ.get("COSMOSENDPOINT")
        CosmosKey = os.environ.get("COSMOSKEY")
        CosmosDb = os.environ.get("COSMOSDATABASE")
        CosmosContainer = os.environ.get("COSMOSCONTAINER")

        cosmosClient = CosmosClient(url=CosmosEndPoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDb)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)

        cosmosQuery = "SELECT c.role, c.content FROM c WHERE c.sessionId = @sessionId and c.type = 'Message' ORDER by c._ts ASC"
        params = [dict(name="@sessionId", value=sessionId)]
        results = cosmosContainer.query_items(query=cosmosQuery, parameters=params, enable_cross_partition_query=True)
        items = [item for item in results]
        #output = json.dumps(items, indent=True)
        return jsonify(items)
    except Exception as e:
        logging.exception("Exception in /getIndexSessionDetail")
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
    chunkSize=request.json["chunkSize"]
    chunkOverlap=request.json["chunkOverlap"]
    promptType=request.json["promptType"]
    deploymentType=request.json["deploymentType"]
    postBody=request.json["postBody"]
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ.get("DOCGENERATOR_URL")

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "multiple": multiple , "loadType": loadType,
                  "existingIndex": existingIndex, "existingIndexNs": existingIndexNs, "embeddingModelType": embeddingModelType,
                  "textSplitter": textSplitter, "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                  "promptType": promptType, "deploymentType": deploymentType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        jsonDict = json.loads(resp.text)
        #return json.dumps(jsonDict)
        return jsonify(jsonDict)
    except Exception as e:
        logging.exception("Exception in /processDoc")
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
                try:
                    promptType = blob.metadata["promptType"]
                except:
                    promptType = "generic"
                
                try:
                    chunkSize = blob.metadata["chunkSize"]
                except:
                    chunkSize = "1500"

                try:
                    chunkOverlap = blob.metadata["chunkOverlap"]
                except:
                    chunkOverlap = "0"

                try:
                    singleFile = bool(strtobool(str(blob.metadata["singleFile"])))
                except:
                    singleFile = False

                blobJson.append({
                    "embedded": blob.metadata["embedded"],
                    "indexName": blob.metadata["indexName"],
                    "namespace":blob.metadata["namespace"],
                    "qa": blob.metadata["qa"],
                    "summary":blob.metadata["summary"],
                    "name":blob.name,
                    "indexType":blob.metadata["indexType"],
                    "promptType": promptType,
                    "chunkSize": chunkSize,
                    "chunkOverlap": chunkOverlap,
                    "singleFile": singleFile,
                })
            except Exception as e:
                pass

        #jsonDict = json.dumps(blobJson)
        return jsonify({"values" : blobJson})
    except Exception as e:
        logging.exception("Exception in /refreshIndex")
        return jsonify({"error": str(e)}), 500

@app.route("/getDocumentList", methods=["GET"])
def getDocumentList():
   
    try:
        SearchService = os.environ.get("SEARCHSERVICE")
        SearchKey = os.environ.get("SEARCHKEY")
        searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name="evaluatordocument",
        credential=AzureKeyCredential(SearchKey))
        try:
            r = searchClient.search(  
                search_text="",
                select=["documentId", "documentName", "sourceFile"],
                include_total_count=True
            )
            documentList = []
            for document in r:
                try:
                    documentList.append({
                        "documentId": document['documentId'],
                        "documentName": document['documentName'],
                        "sourceFile": document['sourceFile']
                    })
                except Exception as e:
                    pass
            return jsonify({"values" : documentList})
        except Exception as e:
            logging.exception("Exception in /getDocumentList")
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        logging.exception("Exception in /getDocumentList")
        return jsonify({"error": str(e)}), 500
    
@app.route("/refreshQuestions", methods=["POST"])
def refreshQuestions():
   
    kbIndexName = os.environ.get("KBINDEXNAME")
    SearchService = os.environ.get("SEARCHSERVICE")
    SearchKey = os.environ.get("SEARCHKEY")
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=kbIndexName,
        credential=AzureKeyCredential(SearchKey))
    
    indexType=request.json["indexType"]
    indexName=request.json["indexName"]

    try:
        r = searchClient.search(  
            search_text="",
            filter="indexType eq '" + indexType + "' and indexName eq '" + indexName + "'",
            select=["question"],
            include_total_count=True
        )
        questionsList = []
        for question in r:
            try:
                questionsList.append({
                    "question": question['question'],
                })
            except Exception as e:
                pass

        #jsonDict = json.dumps(blobJson)
        return jsonify({"values" : questionsList})
    except Exception as e:
        logging.exception("Exception in /refreshQuestions")
        return jsonify({"error": str(e)}), 500

@app.route("/refreshIndexQuestions", methods=["POST"])
def refreshIndexQuestions():
   
    kbIndexName = os.environ.get("KBINDEXNAME")
    SearchService = os.environ.get("SEARCHSERVICE")
    SearchKey = os.environ.get("SEARCHKEY")
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=kbIndexName,
        credential=AzureKeyCredential(SearchKey))
    
    indexType=request.json["indexType"]

    try:
        r = searchClient.search(  
            search_text="",
            filter="indexType eq '" + indexType + "'",
            select=["id", "question", "indexType", "indexName"],
            include_total_count=True
        )
        logging.info(r.get_count())
        questionsList = []
        for question in r:
            try:
                questionsList.append({
                    "id": question['id'],
                    "question": question['question'],
                    "indexType": question['indexType'],
                    "indexName": question['indexName'],
                })
            except Exception as e:
                pass

        #jsonDict = json.dumps(blobJson)
        return jsonify({"values" : questionsList})
    except Exception as e:
        logging.exception("Exception in /refreshIndexQuestions")
        return jsonify({"error": str(e)}), 500

@app.route("/kbQuestionManagement", methods=["POST"])
def kbQuestionManagement():
   
    kbIndexName = os.environ.get("KBINDEXNAME")
    SearchService = os.environ.get("SEARCHSERVICE")
    SearchKey = os.environ.get("SEARCHKEY")
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=kbIndexName,
        credential=AzureKeyCredential(SearchKey))
    
    documentsToDelete=request.json["documentsToDelete"]

    try:
        r = searchClient.delete_documents(documents=documentsToDelete)
        questionsList = []
        questionsList.append({
            "result": "success",
        })
        #jsonDict = json.dumps(blobJson)
        return jsonify({"values" : questionsList})
    except Exception as e:
        logging.exception("Exception in /kbQuestionManagement")
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
    logging.info(f"Getting blob {path.strip()} from container {containerName}")
    blobContainer = blobClient.get_container_client(container=containerName)
    blob = blobContainer.get_blob_client(path.strip()).download_blob()
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path.strip())[0] or "application/octet-stream"
    return blob.readall(), 200, {"Content-Type": mime_type, "Content-Disposition": f"inline; filename={path}"}
    
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
    app.run(port=5002)

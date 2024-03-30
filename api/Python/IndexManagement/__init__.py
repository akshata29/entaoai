import logging, json, os
import azure.functions as func
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores.milvus import Milvus
from pinecone import Pinecone
from langchain_community.document_loaders.pdf import PDFMinerLoader
from langchain_community.vectorstores.redis import Redis
#from langchain.vectorstores import Weaviate
from Utilities.azureBlob import upsertMetadata, getBlob, getAllBlobs, getSasToken, getFullPath
from Utilities.cogSearch import createSearchIndex, createSections, indexSections, deleteSearchIndex
from azure.storage.blob import BlobClient
from Utilities.envVars import *

try:
    redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
except:
    logging.error("Chroma or Redis not configured.  Ignoring.")

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        indexType = req.params.get('indexType')
        indexName = req.params.get('indexName')
        blobName = req.params.get('blobName')
        indexNs = req.params.get('indexNs')
        if (indexNs == None or indexNs == 'null'):
            indexNs = ''
        operation = req.params.get('operation')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        if len(PineconeKey) > 10 and len(PineconeEnv) > 10:
            os.environ["PINECONE_API_KEY"] = PineconeKey
            pc = Pinecone(api_key=PineconeKey, host=PineconeEnv)
        result = ComposeResponse(indexType, indexName, blobName, indexNs, operation, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexType, indexName, blobName, indexNs, operation, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, indexName,  blobName, indexNs, operation, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def IndexManagement(indexType, indexName, blobName, indexNs, operation, record):
    try:
        if operation == "delete":
            logging.info("Deleting index " + indexNs)
            if indexType == "pinecone":
                if (indexNs != '' or indexNs != None):
                    pc = Pinecone(api_key=PineconeKey)
                    index = Pinecone.Index(pc, name=VsIndexName)
                    index.delete(delete_all=True, namespace=indexNs)
            elif indexType == "redis":
                Redis.drop_index(index_name=indexNs, delete_documents=True, redis_url=redisUrl)
            elif indexType == "cogsearch" or indexType == "cogsearchvs":
                deleteSearchIndex(indexNs)
            blobList = getAllBlobs(OpenAiDocConnStr, OpenAiDocContainer)
            for blob in blobList:
                try:
                    if (blob.metadata['indexName'] == indexName):
                        logging.info("Deleting blob " + blob.name)
                        blobClient = BlobClient.from_connection_string(conn_str=OpenAiDocConnStr, container_name=OpenAiDocContainer, blob_name=blob.name)
                        blobClient.delete_blob()
                except:
                    continue
            return "Success"
        elif operation == "update":
            return "Success"
    except Exception as e:
        logging.error(e)
        return func.HttpResponse(
            "Error getting files",
            status_code=500
        )

def TransformValue(indexType, indexName, blobName, indexNs, operation, record):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:
        assert ('data' in record), "'data' field is required."
        data = record['data']
        assert ('text' in data), "'text' field is required in 'data' object."

    except KeyError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "KeyError:" + error.args[0] }   ]
            })
    except AssertionError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "AssertionError:" + error.args[0] }   ]
            })
    except SystemError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "SystemError:" + error.args[0] }   ]
            })

    try:
        # Getting the items from the values/data/text
        value = data['text']
        logging.info("Value: " + value)
        logging.info("Index Type: " + indexType)
        logging.info("Index Name: " + indexName)
        logging.info("Blob Name: " + blobName)
        logging.info("Index Namespace: " + indexNs)
        logging.info("Operation: " + operation)

        indexResponse = IndexManagement(indexType, indexName, blobName, indexNs, operation, value)

        return ({
            "recordId": recordId,
            "data": {
                "error": indexResponse
                    }
            })

    except:
        return (
            {
            "recordId": recordId,
                "data": {
                "error": "Could not process the request"
                    }
            })

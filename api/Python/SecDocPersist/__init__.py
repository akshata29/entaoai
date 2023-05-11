import logging, json, os
import azure.functions as func
import openai
import os
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import numpy as np
from Utilities.redisIndex import createRedisIndex, chunkAndEmbed
from Utilities.azureBlob import upsertMetadata, getBlob, getAllBlobs
from Utilities.envVars import *

redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort

def GetAllFiles():
    # Get all files in the container from Azure Blob Storage
    # Create the BlobServiceClient object
    blobList = getAllBlobs(OpenAiDocConnStr, SecDocContainer)
    files = []
    for file in blobList:
        if (file.metadata == None):
            files.append({
            "filename" : file.name,
            "embedded": "false",
            })
        else:
            files.append({
                "filename" : file.name,
                "embedded": file.metadata["embedded"] if "embedded" in file.metadata else "false",
                })
    logging.info(f"Found {len(files)} files in the container")
    return files

def PersistSecDocs(indexType, indexName,  value):
    logging.info("Embedding text")
    try:
        logging.info("Loading OpenAI")
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"
      
        filesData = GetAllFiles()
        filesData = list(filter(lambda x : x['embedded'] == "false", filesData))
        logging.info(filesData)
        filesData = list(map(lambda x: {'filename': x['filename']}, filesData))

        logging.info(f"Found {len(filesData)} files to embed")
        for file in filesData:
            fileName = file['filename']
            readBytes = getBlob(OpenAiDocConnStr, SecDocContainer, fileName)
            # downloadPath = os.path.join(tempfile.gettempdir(), fileName)
            # os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
            # try:
            #     with open(downloadPath, "wb") as file:
            #         file.write(readBytes)
            # except Exception as e:
            #     logging.error(e)

            # logging.info("File created " + downloadPath)
            secDoc = json.loads(readBytes.decode("utf-8"))
            distanceMetrics = ("COSINE")
            cik = TextField(name="cik")
            company = TextField(name="company")
            filing_type = TextField(name="filing_type")
            filing_date = TextField(name="filing_date")
            period_of_report = TextField(name="period_of_report")
            sic = TextField(name="sic")
            state_of_inc = TextField(name="state_of_inc")
            state_location = TextField(name="state_location")
            fiscal_year_end = TextField(name="fiscal_year_end")
            filing_html_index = TextField(name="filing_html_index")
            htm_filing_link = TextField(name="htm_filing_link")
            complete_text_filing_link = TextField(name="complete_text_filing_link")
            filename = TextField(name="filename")
            metadata = TextField(name="metadata")
            # For now we will combine Item 1, 1A, 7, 7A into a single field "content"
            # item_1 = TextField(name="item_1")
            # item_1A = TextField(name="item_1A")
            # item_1B = TextField(name="item_1B")
            # item_2 = TextField(name="item_2")
            # item_3 = TextField(name="item_3")
            # item_4 = TextField(name="item_4")
            # item_5 = TextField(name="item_5")
            # item_6 = TextField(name="item_6")
            # item_7 = TextField(name="item_7")
            # item_7A = TextField(name="item_7A")
            # item_8 = TextField(name="item_8")
            # item_9 = TextField(name="item_9")
            # item_9A = TextField(name="item_9A")
            # item_9B = TextField(name="item_9B")
            # item_10 = TextField(name="item_10")
            # item_11 = TextField(name="item_11")
            # item_12 = TextField(name="item_12")
            # item_13 = TextField(name="item_13")
            # item_14 = TextField(name="item_14")
            # item_15 = TextField(name="item_15")
            # item1Embedding = VectorField("item1_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item1AEmbedding = VectorField("item1A_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item7Embedding = VectorField("item7_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item7AEmbedding = VectorField("item7A_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item8Embedding = VectorField("item8_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # fields = [cik, company, filing_type, filing_date, period_of_report, sic, state_of_inc, state_location, 
            #          fiscal_year_end, filing_html_index, htm_filing_link, complete_text_filing_link, filename,
            #          item_1, item_1A, item_1B, item_2, item_3, item_4, item_5, item_6, item_7, item_7A, item_8, item_9, 
            #          item_9A, item_9B, item_10, item_11, item_12, item_13, item_14, item_15, item1Embedding,
            #          item1AEmbedding, item7Embedding, item7AEmbedding, item8Embedding]
            
            content = TextField(name="content")
            contentEmbedding = VectorField("content_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            fields = [cik, company, filing_type, filing_date, period_of_report, sic, state_of_inc, state_location, 
                    fiscal_year_end, filing_html_index, htm_filing_link, complete_text_filing_link, filename,
                    content, contentEmbedding, metadata]
            logging.info("Create index")
            redisClient = createRedisIndex(fields, indexName)
            logging.info("Index created")
            logging.info("Embedding")
            chunkAndEmbed(redisClient, indexName, secDoc, OpenAiEmbedding)
            logging.info("Embedding complete")
            #redisConnection = Redis(redis_url=redisUrl, index_name=uResultNs.hex, embedding_function=embeddings)
            #Redis.from_documents(docs, embeddings, redis_url=redisUrl, index_name=uResultNs.hex)
            #logging.info("Upsert metadata")
            metadata = {'embedded': 'true', 'indexType': indexType, "indexName": indexName}
            upsertMetadata(OpenAiDocConnStr, SecDocContainer, fileName, metadata)
            #metadata = {'summary': summary, 'qa': qa}
            #upsertMetadata(fileName, metadata)
            #logging.info("Sleeping")
        return "Success"
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(indexType, indexName, record):
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

        summaryResponse = PersistSecDocs(indexType, indexName, value)
        return ({
            "recordId": recordId,
            "data": {
                "text": summaryResponse
                    }
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

def ComposeResponse(indexType, indexName, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, indexName, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

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
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(indexType, indexName, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )


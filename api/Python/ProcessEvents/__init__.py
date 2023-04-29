import logging
import azure.functions as func
import os
from azure.storage.blob import BlobServiceClient, ContentSettings
import requests
import json

def main(processFile: func.InputStream, context: func.Context):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {processFile.name}\n"
                 f"Blob Size: {processFile.length} bytes")
    
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    blobName = os.path.basename(processFile.name)
    # Upload the File to regular Blob Storage
    url = os.environ['OpenAiDocStorConnString']
    containerName = os.environ['OpenAiDocContainer']
    blobServiceClient = BlobServiceClient.from_connection_string(url)
    containerClient = blobServiceClient.get_container_client(containerName)
    blobClient = containerClient.get_blob_client(blobName)
    blobClient.upload_blob(processFile.read(), overwrite=True)
    blobClient.set_blob_metadata(metadata={"embedded": "false", 
                                    "indexName": "", 
                                    "namespace": "", 
                                    "qa": "No Qa Generated",
                                    "name":blobName,
                                    "summary": "No Summary Created", 
                                    "indexType": ""})

    # Process the File with via DocGenerator
    indexType="pinecone" # For now hardcoded
    indexName=processFile.name
    multiple="false" # Because the files events are triggered into functions one at a time, we can assume that this is always false
    loadType="files"

    postBody={
        "values": [
          {
            "recordId": 0,
            "data": {
              "text": [{"path":blobName}],
              "blobConnectionString": "",
              "blobContainer" : "",
              "blobPrefix" : "",
              "blobName" : "",
              "s3Bucket": "s3Bucket",
              "s3Key" : "",
              "s3AccessKey" : "",
              "s3SecretKey" : "",
              "s3Prefix" : ""
            }
          }
        ]
      }
   
    try:
        headers = {'content-type': 'application/json'}
        url = os.environ['DOCGENERATOR_URL']

        data = postBody
        params = {'indexType': indexType, "indexName": indexName, "multiple": multiple , "loadType": loadType}
        resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
    except Exception as e:
        logging.exception("Exception in /processDoc")
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

import logging
import azure.functions as func
import os
from azure.storage.blob import BlobServiceClient, ContentSettings
import requests
import json

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")
    
    try:
      blobName = req.params.get('fileName')
      # Upload the File to regular Blob Storage
      url = os.environ['OpenAiDocStorConnString']
      containerName = os.environ['OpenAiDocContainer']
      blobServiceClient = BlobServiceClient.from_connection_string(url)
      containerClient = blobServiceClient.get_container_client(containerName)
      blobClient = containerClient.get_blob_client(blobName)
      logging.info("Set Blob Metadata")
      blobClient.set_blob_metadata(metadata={"embedded": "false", 
                                      "indexName": blobName, 
                                      "namespace": "", 
                                      "qa": "No Qa Generated",
                                      "summary": "No Summary Created", 
                                      "indexType": ""})

      # Process the File with via DocGenerator
      indexType="pinecone" # For now hardcoded
      indexName=blobName
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
      
      headers = {'content-type': 'application/json'}
      url = os.environ['DOCGENERATOR_URL']

      data = postBody
      params = {"indexType": indexType, "indexName": indexName, "multiple": multiple, "loadType": loadType,
                "existingIndex": "false", "existingIndexNs": "", "embeddingModelType": "openai", "textSplitter": "recursive"}
      logging.info("Call Doc Generator")
      resp = requests.post(url, params=params, data=json.dumps(data), headers=headers)
      logging.info("Doc Generator Response")
      return func.HttpResponse(json.dumps(resp.json()), status_code=200)
    except Exception as e:
        logging.exception("Exception in /processDoc")
        return func.HttpResponse(
              "Invalid body",
              status_code=400
        )

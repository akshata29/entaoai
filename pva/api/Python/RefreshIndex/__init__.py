from azure.storage.blob import BlobServiceClient, ContentSettings
import logging, json, os
import azure.functions as func

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        url = os.environ['BLOB_CONNECTION_STRING']
        containerName = os.environ['BLOB_CONTAINER_NAME'] 
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
                logging.info(blobJson)
            except Exception as e:
                pass

        return func.HttpResponse(json.dumps(blobJson), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    

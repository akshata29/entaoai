import logging, json, os
import azure.functions as func
from Utilities.envVars import *

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        passType = req.params.get('passType')
        password = req.params.get('password')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:

        result = ComposeResponse(passType, password, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(passType, password,  jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(passType, password, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(passType, password, record):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None
    
    try:
        # Getting the items from the values/data/text
        if (passType == 'upload'):
            if (UploadPassword.strip() == ''): 
                return (
                    {
                    "recordId": recordId,
                     "data": {
                            "error": "Upload Password is not set"
                        }
                    })
            if (password.strip() != UploadPassword.strip()):
                return (
                    {
                    "recordId": recordId,
                     "data": {
                            "error": "Upload Password is incorrect"
                        }
                    })
        elif (passType == 'admin'):
            if (AdminPassword.strip() == ''): 
                return (
                    {
                    "recordId": recordId,
                     "data": {
                            "error": "Admin Password is not set"
                        }
                    })
            if (password.strip() != AdminPassword.strip()):
                return (
                    {
                    "recordId": recordId,
                     "data": {
                            "error": "Admin Password is incorrect"
                        }
                    })
        return (
                    {
                    "recordId": recordId,
                     "data": {
                            "error": "Success"
                        }
                    })
    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

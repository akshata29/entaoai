import logging, json, os
import azure.functions as func
from Utilities.envVars import *
import azure.durable_functions as df
from urllib.parse import urlparse

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    try:
        urlSchema = urlparse(req.url).scheme
        urlHost = req.headers.get("host")
        # Parameters
        embeddingModelType = req.params.get('embeddingModelType')
        fileName = req.params.get('fileName')
        retrieverType = req.params.get('retrieverType')
        promptStyle = req.params.get('promptStyle')
        totalQuestions = req.params.get('totalQuestions')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:

        result = await ComposeResponse(embeddingModelType, fileName, retrieverType, promptStyle, totalQuestions, starter, urlSchema, 
                                       urlHost, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

async def ComposeResponse(embeddingModelType, fileName, retrieverType, promptStyle, totalQuestions, starter, urlSchema, urlHost, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = await TransformValue(embeddingModelType, fileName, retrieverType, promptStyle, totalQuestions, starter, urlSchema, urlHost, 
                                            value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def buildApiUrl(scheme, host, instanceId):
    return f"{scheme}://{host}/api/EvaluatorStatus/{instanceId}"

async def TransformValue(embeddingModelType, fileName, retrieverType, promptStyle, totalQuestions, starter, urlSchema, urlHost, 
                         record):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None
    
    try:
        data = record['data']
        client = df.DurableOrchestrationClient(starter)
        parameters = {
        "embeddingModelType": embeddingModelType,
        "fileName": fileName,
        "retrieverType": retrieverType,
        "promptStyle": promptStyle,
        "totalQuestions":totalQuestions,
        "splitMethods": data['splitMethods'],
        "chunkSizes": data['chunkSizes'],
        "overlaps": data['overlaps'],
        "record": record
        }
        instanceId = await client.start_new('EvaluatorCore', None, parameters)
        statusUri = buildApiUrl(urlSchema, urlHost, instanceId)
        return (
                    {
                    "recordId": recordId,
                     "data": {
                            "statusUri": statusUri,
                            "error": "Success"
                        }
                    })
    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

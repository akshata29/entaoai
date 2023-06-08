import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI, OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
from langchain.document_loaders import (
    PDFMinerLoader,
    UnstructuredFileLoader,
)
import os
from langchain.document_loaders import PDFMinerLoader
import time
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from Utilities.azureBlob import getBlob, getFullPath
from typing import List
from Utilities.envVars import *
#from langchain.document_loaders import JSONLoader

def GetAllFiles(filesToProcess):
    files = []
    convertedFiles = {}
    for file in filesToProcess:
        files.append({
            "filename" : file['path'],
            "converted": False,
            "embedded": False,
            "converted_path": ""
            })
    logging.info(f"Found {len(files)} files in the container")
    for file in files:
        convertedFileName = f"converted/{file['filename']}.zip"
        if convertedFileName in convertedFiles:
            file['converted'] = True
            file['converted_path'] = convertedFiles[convertedFileName]

    logging.info(files)
    return files
    #return []

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        chainType = req.params.get('chainType')
        loadType = req.params.get('loadType')
        multiple = req.params.get('multiple')
        embeddingModelType=req.params.get("embeddingModelType")
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        logging.info("Embedding Model Type: %s", embeddingModelType)
        result = ComposeResponse(chainType, loadType, multiple, embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(chainType, loadType,  multiple, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(chainType, loadType, multiple,embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def summarizeDoc(docs, chainType, embeddingModelType):

    if embeddingModelType == "azureopenai":
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"
        llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiKey,
                max_tokens=1000,
                batch_size=10)
    elif embeddingModelType == "openai":
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07' 
        openai.api_key = OpenAiApiKey
        llm = OpenAI(temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiApiKey,
                verbose=True,
                max_tokens=1000)
    elif embeddingModelType == "local":
        return "Local not supported"

    try:
        promptTemplate = """Write a concise summary of the following:


        {text}
        
        """
        summaryPrompt = PromptTemplate(template=promptTemplate, input_variables=["text"])
        if chainType == "stuff":
            summaryChain = load_summarize_chain(llm, chain_type=chainType)
            summary = summaryChain.run(docs)
        else:
            summaryChain = load_summarize_chain(llm, chain_type=chainType, return_intermediate_steps=True)
            summary = summaryChain({"input_documents": docs}, return_only_outputs=True)
        logging.info("Document Summary completed")
    except Exception as e:
        logging.info("Exception during summary" + str(e))
        summary = str(e)
        pass
    return summary

def blobLoad(blobConnectionString, blobContainer, blobName):
    readBytes  = getBlob(blobConnectionString, blobContainer, blobName)
    downloadPath = os.path.join(tempfile.gettempdir(), blobName)
    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
    try:
        with open(downloadPath, "wb") as file:
            file.write(readBytes)
    except Exception as e:
        logging.error(e)

    logging.info("File created " + downloadPath)
    if (blobName.endswith(".pdf")):
        loader = PDFMinerLoader(downloadPath)
    elif (blobName.endswith(".docx") or blobName.endswith(".doc")):
        loader = UnstructuredWordDocumentLoader(downloadPath)

    #loader = UnstructuredFileLoader(downloadPath)
    rawDocs = loader.load()

    fullPath = getFullPath(blobConnectionString, blobContainer, blobName)
    for doc in rawDocs:
        doc.metadata['source'] = fullPath
    return rawDocs

def Embed(chainType, loadType, multiple, embeddingModelType, value):
    logging.info("Embedding Data")
    try:
        logging.info("Loading Embedding Model " + embeddingModelType)

        if (loadType == "files"):
            try:
                filesData = GetAllFiles(value)
                filesData = list(filter(lambda x : not x['embedded'], filesData))
                filesData = list(map(lambda x: {'filename': x['filename']}, filesData))

                logging.info(f"Found {len(filesData)} files to embed")
                for file in filesData:
                    logging.info(f"Adding {file['filename']} to Process")
                    fileName = file['filename']
                    # Check the file extension
                    if fileName.endswith('.txt'):
                        logging.info("Embedding text file")
                        readBytes  = getBlob(OpenAiDocConnStr, OpenAiSummaryContainer, fileName)
                        fileContent = readBytes.decode('utf-8')
                        downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                        os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                        try:
                            with open(downloadPath, "wb") as file:
                                file.write(bytes(fileContent, 'utf-8'))
                        except Exception as e:
                            errorMessage = str(e)
                            logging.error(e)
                            return {"data_points": '', "answer": errorMessage, 
                                "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}

                        logging.info("File created")
                        loader = UnstructuredFileLoader(downloadPath)
                        rawDocs = loader.load()
                        textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                        docs = textSplitter.split_documents(rawDocs)
                        logging.info("Docs " + str(len(docs)))
                    elif fileName.endswith('.csv'):
                        # for CSV, all we want to do is set the metadata
                        # so that we can use the appropriate CSV/Pandas/Spark agent for QA and Chat
                        # and/or the Smart Agent
                        logging.info("Processing CSV File")
                    # elif fileName.endswith('.json'):
                    #     readBytes  = getBlob(OpenAiDocConnStr, OpenAiSummaryContainer, fileName)
                    #     fileContent = readBytes.decode('utf-8')
                    #     downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                    #     os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                    #     try:
                    #         with open(downloadPath, "wb") as file:
                    #             file.write(bytes(fileContent, 'utf-8'))
                    #     except Exception as e:
                    #         errorMessage = str(e)
                    #         logging.error(e)
                    #         return {"data_points": '', "answer": errorMessage, 
                    #             "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
                    #     logging.info("File created")

                    #     loader = JSONLoader(file_path=downloadPath, jq_schema='.[]')
                    #     rawDocs = loader.load()
                    #     textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                    #     docs = textSplitter.split_documents(rawDocs)
                    #     logging.info("Docs " + str(len(docs)))
                    else:
                        try:
                            logging.info("Embedding Non-text file")
                            docs = []
                            rawDocs = blobLoad(OpenAiDocConnStr, OpenAiSummaryContainer, fileName)
                            textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                            docs = textSplitter.split_documents(rawDocs)
                            logging.info("Docs " + str(len(docs)))
                        except Exception as e:
                            logging.info(e)
                            errorMessage = str(e)
                            return {"data_points": '', "answer": errorMessage, 
                                "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
                    logging.info("Perform Summarization and QA")
                    summary = summarizeDoc(docs, chainType, embeddingModelType)
                    if (chainType == "stuff"):
                        return {"data_points": '', "answer": summary, 
                            "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
                    else:
                        return {"data_points": summary['intermediate_steps'], "answer": summary['output_text'], 
                            "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
            except Exception as e:
                errorMessage = str(e)
                return {"data_points": '', "answer": errorMessage, 
                            "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}

    except Exception as e:
        logging.error(e)
        errorMessage = str(e)
        return errorMessage
        #return func.HttpResponse("Error getting files",status_code=500)

def TransformValue(chainType, loadType, multiple,embeddingModelType, record):
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
        summaryResponse = Embed(chainType, loadType, multiple,embeddingModelType, value)
        return ({
            "recordId": recordId,
            "data": summaryResponse
            })
    
    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

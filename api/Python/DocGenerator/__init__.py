import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI, OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import uuid
from langchain.document_loaders import (
    PDFMinerLoader,
    UnstructuredFileLoader,
)
import os
from langchain.vectorstores import Pinecone
from langchain.vectorstores import Milvus
import pinecone
from langchain.document_loaders import PDFMinerLoader
import time
from langchain.vectorstores.redis import Redis
from langchain.document_loaders import WebBaseLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from Utilities.azureBlob import upsertMetadata, getBlob, getAllBlobs, getSasToken, getFullPath
from Utilities.cogSearch import createSearchIndex, createSections, indexSections
from langchain.document_loaders import AzureBlobStorageFileLoader
from langchain.document_loaders import AzureBlobStorageContainerLoader
from azure.storage.blob import BlobClient
from azure.storage.blob import ContainerClient
import boto3
#import chromadb
#from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
#from chromadb.config import Settings
#from langchain.vectorstores import Chroma
#from sentence_transformers import SentenceTransformer
from typing import List

OpenAiKey = os.environ['OpenAiKey']
OpenAiVersion = os.environ['OpenAiVersion']
OpenAiDavinci = os.environ['OpenAiDavinci']
OpenAiService = os.environ['OpenAiService']
OpenAiDocStorName = os.environ['OpenAiDocStorName']
OpenAiDocStorKey = os.environ['OpenAiDocStorKey']
OpenAiDocConnStr = f"DefaultEndpointsProtocol=https;AccountName={OpenAiDocStorName};AccountKey={OpenAiDocStorKey};EndpointSuffix=core.windows.net"
OpenAiDocContainer = os.environ['OpenAiDocContainer']
PineconeEnv = os.environ['PineconeEnv']
PineconeKey = os.environ['PineconeKey']
VsIndexName = os.environ['VsIndexName']
RedisAddress = os.environ['RedisAddress']
RedisPassword = os.environ['RedisPassword']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
RedisPort = os.environ['RedisPort']
UploadPassword = os.environ['UploadPassword'] or ''
AdminPassword = os.environ['AdminPassword'] or ''
ChromaUrl = os.environ['ChromaUrl'] or ''
ChromaPort = os.environ['ChromaPort'] or '8000'
OpenAiApiKey = os.environ['OpenAiApiKey']
#OpenAiOrg = os.environ['OpenAiOrg']

try:
    redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
    # chromaClient = chromadb.Client(Settings(
    #         chroma_api_impl="rest",
    #         chroma_server_host=ChromaUrl,
    #         chroma_server_http_port=ChromaPort))
    # chromaClient.heartbeat()
    # logging.info("Successfully connected to Chroma DB. Collections found: %s",chromaClient.list_collections())
except:
    logging.info("Chroma dn Redis not configured")
    
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
        indexType = req.params.get('indexType')
        loadType = req.params.get('loadType')
        multiple = req.params.get('multiple')
        indexName = req.params.get('indexName')
        existingIndex=req.params.get("existingIndex")
        existingIndexNs=req.params.get("existingIndexNs")
        embeddingModelType=req.params.get("embeddingModelType")
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        try:
            pinecone.init(
                api_key=PineconeKey,  # find at app.pinecone.io
                environment=PineconeEnv  # next to api key in console
            )
        except:
            logging.info("Pinecone already initialized")

        logging.info("Embedding Model Type: %s", embeddingModelType)
        result = ComposeResponse(indexType, loadType, multiple, indexName, existingIndex, existingIndexNs, 
                                 embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexType, loadType,  multiple, indexName, existingIndex, existingIndexNs, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, loadType,  multiple, indexName, existingIndex, existingIndexNs, embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def summarizeGenerateQa(docs, embeddingModelType):

    if embeddingModelType == "azureopenai":
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"
        llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiKey,
                max_tokens=1024,
                batch_size=10)
    elif embeddingModelType == "openai":
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07' 
        openai.api_key = OpenAiApiKey
        llm = OpenAI(temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiApiKey,
                verbose=True,
                max_tokens=1024)
    elif embeddingModelType == "local":
        return "Local not supported", "Local not supported"

    try:
        summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
        summary = summaryChain.run(docs)
        logging.info("Document Summary completed")
    except Exception as e:
        logging.info("Exception during summary" + str(e))
        summary = 'No summary generated'
        pass

    template = """Given the following extracted parts of a long document, recommend between 1-5 sample questions.

            =========
            {summaries}
            =========
            """
    try:
        qaPrompt = PromptTemplate(template=template, input_variables=["summaries"])
        qaChain = load_qa_with_sources_chain(llm, chain_type='stuff', prompt=qaPrompt)
        answer = qaChain({"input_documents": docs[:5], "question": ''}, return_only_outputs=True)
        logging.info("Document QA completed")
        qa = answer['output_text'].replace('\nSample Questions: \n', '').replace('\nSample Questions:\n', '').replace('\n', '\\n')
    except Exception as e:
        logging.info("Exception during QA" + str(e))
        qa = 'No Sample QA generated'
        pass
    #qa = qa.decode('utf8')
    return qa, summary

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
    loader = PDFMinerLoader(downloadPath)
    #loader = UnstructuredFileLoader(downloadPath)
    rawDocs = loader.load()

    fullPath = getFullPath(blobConnectionString, blobContainer, blobName)
    for doc in rawDocs:
        doc.metadata['source'] = fullPath
    return rawDocs

def s3Load(bucket, key, s3Client):
    downloadPath = os.path.join(tempfile.gettempdir(), key)
    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
    s3Client.download_file(bucket, key, downloadPath)
    logging.info("File created " + downloadPath)
    loader = PDFMinerLoader(downloadPath)
    rawDocs = loader.load()
    return rawDocs

def storeIndex(indexType, docs, fileName, nameSpace, embeddingModelType):
    if embeddingModelType == "azureopenai":
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"
        embeddings = OpenAIEmbeddings(model=OpenAiEmbedding,
                chunk_size=1,
                openai_api_key=OpenAiKey)
    elif embeddingModelType == "openai":
        #openai.debug = True
        #openai.log = 'debug'
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07' 
        openai.api_key = OpenAiApiKey
        embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)
    elif embeddingModelType == "local":
        #embeddings = LocalHuggingFaceEmbeddings("all-mpnet-base-v2")
        return

    logging.info("Store the index in " + indexType + " and name : " + nameSpace)
    if indexType == 'pinecone':
        Pinecone.from_documents(docs, embeddings, index_name=VsIndexName, namespace=nameSpace)
    elif indexType == "redis":
        Redis.from_documents(docs, embeddings, redis_url=redisUrl, index_name=nameSpace)
    elif indexType == "cogsearch":
        createSearchIndex(nameSpace)
        indexSections(fileName, nameSpace, docs)
    elif indexType == "chroma":
        logging.info("Chroma Client: " + str(docs))
        #Chroma.from_documents(docs, embeddings, collection_name=nameSpace, client=chromaClient, embedding_function=embeddings)
    elif indexType == 'milvus':
        milvus = Milvus(connection_args={"host": "127.0.0.1", "port": "19530"},
                        collection_name=VsIndexName, text_field="text", embedding_function=embeddings)
        Milvus.from_documents(docs,embeddings)

def Embed(indexType, loadType, multiple, indexName,  value,  blobConnectionString,
                                blobContainer, blobPrefix, blobName, s3Bucket, s3Key, s3AccessKey,
                                s3SecretKey, s3Prefix, existingIndex, existingIndexNs,
                                embeddingModelType):
    logging.info("Embedding Data")
    try:
        logging.info("Loading Embedding Model " + embeddingModelType)

        uResultNs = uuid.uuid4()
        
        if (existingIndex == "true"):
            indexGuId = existingIndexNs
        else:
            indexGuId = uResultNs.hex
        logging.info("Index will be created as " + indexGuId)

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
                        readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                        fileContent = readBytes.decode('utf-8')
                        downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                        os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                        try:
                            with open(downloadPath, "wb") as file:
                                file.write(bytes(fileContent, 'utf-8'))
                        except Exception as e:
                            logging.error(e)

                        logging.info("File created")
                        textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                        loader = UnstructuredFileLoader(downloadPath)
                        rawDocs = loader.load()
                        docs = textSplitter.split_documents(rawDocs)
                        logging.info("Docs " + str(len(docs)))
                        storeIndex(indexType, docs, fileName, indexGuId, embeddingModelType)
                    else:
                        try:
                            logging.info("Embedding Non-text file")
                            rawDocs = blobLoad(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                            textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                            docs = []
                            docs = textSplitter.split_documents(rawDocs)
                            storeIndex(indexType, docs, fileName, indexGuId, embeddingModelType)
                        except Exception as e:
                            logging.info(e)
                            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, {'embedded': 'false', 'indexType': indexType})
                            return "Error"
                    logging.info("Perform Summarization and QA")
                    qa, summary = summarizeGenerateQa(docs, embeddingModelType)
                    logging.info("Upsert metadata")
                    metadata = {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, "indexName": indexName.replace("-", "_")}
                    upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                    try:
                        metadata = {'summary': summary.replace("-", "_"), 'qa': qa.replace("-", "_")}
                        upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                    except:
                        pass
                    logging.info("Sleeping")
                    time.sleep(5)
                return "Success"
            except Exception as e:
                return "Error"
        elif (loadType == "webpages"):
            try:
                allDocs = []
                logging.info(value)
                for webPage in value:
                    logging.info("Processing Webpage at " + webPage)
                    textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                    docs = []
                    loader = WebBaseLoader(webPage)
                    rawDocs = loader.load()
                    docs = textSplitter.split_documents(rawDocs)
                    allDocs = allDocs + docs
                    storeIndex(indexType, docs, indexName + ".txt", indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(allDocs, embeddingModelType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, "indexName": indexName})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.info(e)
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                return "Error"
        elif (loadType == "adlscontainer"):
            try:
                logging.info("Embedding Azure Blob Container")
                container = ContainerClient.from_connection_string(
                    conn_str=blobConnectionString, container_name=blobContainer
                )
                rawDocs = []
                blobList = container.list_blobs(name_starts_with=blobPrefix)
                for blob in blobList:
                    logging.info("Process Blob : " + blob.name)
                    blobDocs = blobLoad(blobConnectionString, blobContainer, blob.name)
                    rawDocs.extend(blobDocs)
                textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = []
                docs = textSplitter.split_documents(rawDocs)
                storeIndex(indexType, docs, indexName, indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs, embeddingModelType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, "indexName": indexName})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                return "Error"
        elif (loadType == "adlsfile"):
            try:
                logging.info("Embedding Azure Blob File")
                rawDocs = blobLoad(blobConnectionString, blobContainer, blobName)
                textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = []
                docs = textSplitter.split_documents(rawDocs)
                storeIndex(indexType, docs, blobName, indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs, embeddingModelType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, "indexName": indexName})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.info(e)
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                return "Error"
        elif (loadType == "s3Container"):
            try:
                logging.info("Embedding S3 Bucket Container")
                s3Client = boto3.client( 's3', aws_access_key_id=s3AccessKey, aws_secret_access_key=s3SecretKey)
                s3Resource = boto3.resource('s3',
                    aws_access_key_id = s3AccessKey,
                    aws_secret_access_key = s3SecretKey
                )
                myBucket = s3Resource.Bucket(s3Bucket)
                rawDocs = []
                for blob in myBucket.objects.filter(Prefix=s3Prefix):
                    logging.info("Process Blob : " + blob.key)
                    blobDocs = s3Load(s3Bucket, blob.key, s3Client)
                    rawDocs.extend(blobDocs)
                textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = []
                docs = textSplitter.split_documents(rawDocs)
                storeIndex(indexType, docs, indexName, indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs, embeddingModelType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, "indexName": indexName})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"            
            except Exception as e:
                logging.info(e)
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                return "Error"
        elif (loadType == "s3file"):
            try:
                logging.info("Embedding S3 Bucket File")
                s3Client = boto3.client( 's3', aws_access_key_id=s3AccessKey, aws_secret_access_key=s3SecretKey)
                rawDocs = s3Load(s3Bucket, s3Key, s3Client)
                textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = []
                docs = textSplitter.split_documents(rawDocs)
                storeIndex(indexType, docs, blobName, indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs, embeddingModelType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, "indexName": indexName})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.info(e)
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                return "Error"
    except Exception as e:
        logging.error(e)
        return func.HttpResponse(
            "Error getting files",
            status_code=500
        )

def TransformValue(indexType, loadType,  multiple, indexName, existingIndex, existingIndexNs, embeddingModelType, record):
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
        blobConnectionString = data['blobConnectionString']
        blobContainer = data['blobContainer']
        blobPrefix = data['blobPrefix']
        blobName = data['blobName']
        s3Bucket = data['s3Bucket']
        s3Key = data['s3Key']
        s3AccessKey = data['s3AccessKey']
        s3SecretKey = data['s3SecretKey']
        s3Prefix = data['s3Prefix']

        summaryResponse = Embed(indexType, loadType,  multiple, indexName, value, blobConnectionString,
                                blobContainer, blobPrefix, blobName, s3Bucket, s3Key, s3AccessKey,
                                s3SecretKey, s3Prefix, existingIndex, existingIndexNs, embeddingModelType)
        return ({
            "recordId": recordId,
            "data": {
                "error": summaryResponse
                    }
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

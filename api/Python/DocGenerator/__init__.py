import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import OpenAI, AzureOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import uuid
from langchain.document_loaders import (
    PDFMinerLoader,
    PyMuPDFLoader,
    UnstructuredFileLoader,
    UnstructuredPDFLoader,
)
import os
from langchain.vectorstores import Pinecone
from langchain.vectorstores import Milvus
import pinecone
from langchain.document_loaders import PDFMinerLoader
from pymilvus import connections
from pymilvus import CollectionSchema, FieldSchema, DataType, Collection
from pymilvus import utility
import time
from langchain.vectorstores.redis import Redis
from langchain.document_loaders import WebBaseLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import numpy as np
from typing import Any, Callable, Dict, List, Optional
from langchain.vectorstores import Weaviate
from langchain.docstore.document import Document
from Utilities.redisIndex import performRedisSearch
from Utilities.azureBlob import upsertMetadata, getBlob, getAllBlobs
from Utilities.cogSearch import createSearchIndex, createSections, indexSections

OpenAiKey = os.environ['OpenAiKey']
OpenAiApiKey = os.environ['OpenAiApiKey']
OpenAiEndPoint = os.environ['OpenAiEndPoint']
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
WeaviateUrl = os.environ['WeaviateUrl']
RedisPort = os.environ['RedisPort']

redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort

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
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        pinecone.init(
            api_key=PineconeKey,  # find at app.pinecone.io
            environment=PineconeEnv  # next to api key in console
        )

        # Once we can get the Milvus index running in Azure, we can use this

        # connections.connect(
        #   alias="default",
        #   host='127.0.0.1',
        #   port='19530'
        # )
        # if not utility.has_collection(VsIndexName):
        #   pkId = FieldSchema(name="pkId", dtype=DataType.INT64, is_primary=True)
        #   source = FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500)
        #   text = FieldSchema(name="text",dtype=DataType.VARCHAR,max_length=1500)
        #   id = FieldSchema(name="id",dtype=DataType.INT64)
        #   embed = FieldSchema(name="embed",dtype=DataType.FLOAT_VECTOR,dim=1536)
        #   schema = CollectionSchema(
        #     fields=[pkId, source, text, id, embed],
        #     description="Open AI Documents"
        #   )
        #   collectionName = VsIndexName
        #   collection = Collection(name=collectionName, schema=schema, using='default')
        #   indexParam = {
        #     "metric_type":"L2",
        #     "index_type":"HNSW",
        #     "params":{"M":8, "efConstruction":64}
        #   }
        #   collection.create_index(field_name="embed", index_params=indexParam)
        #   collection.load()

        result = ComposeResponse(indexType, loadType, multiple, indexName, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexType, loadType,  multiple, indexName, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, loadType,  multiple, indexName, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def summarizeGenerateQa(docs):
    llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiKey,
                max_tokens=1024,
                batch_size=10)
    try:
        summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
        summary = summaryChain.run(docs)
        logging.info("Document Summary completed")
    except Exception as e:
        logging.info(e)
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
        qa = answer['output_text'].replace('\nSample Questions: \n', '').replace('\nSample Questions:\n', '').replace('\n', '\\n')
    except Exception as e:
        logging.info(e)
        qa = 'No Sample QA generated'
    #qa = qa.decode('utf8')
    return qa, summary
        
def Embed(indexType, loadType, multiple, indexName,  value):
    logging.info("Embedding text")
    try:
      logging.info("Loading OpenAI")
      openai.api_type = "azure"
      openai.api_key = OpenAiKey
      openai.api_version = OpenAiVersion
      openai.api_base = f"https://{OpenAiService}.openai.azure.com"
      uResultNs = uuid.uuid4()
      logging.info("Index will be created as " + uResultNs.hex)

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
                    #embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)
                    embeddings = OpenAIEmbeddings(document_model_name=OpenAiEmbedding,
                                                    chunk_size=1,
                                                    openai_api_key=OpenAiKey)
                    if indexType == 'pinecone':
                        Pinecone.from_documents(docs, embeddings, index_name=VsIndexName, namespace=uResultNs.hex)
                    elif indexType == "redis":
                        redisConnection = Redis(redis_url=redisUrl, index_name=uResultNs.hex, embedding_function=embeddings)
                        Redis.from_documents(docs, embeddings, redis_url=redisUrl, index_name=uResultNs.hex)
                    elif indexType == "cogsearch":
                        createSearchIndex(uResultNs.hex)
                        indexSections(fileName, uResultNs.hex, docs)
                    elif indexType == 'milvus':
                        milvus = Milvus(connection_args={"host": "127.0.0.1", "port": "19530"},
                                        collection_name=VsIndexName, text_field="text", embedding_function=embeddings)
                        Milvus.from_documents(docs,embeddings)
                    # Embed the file
                    #data = chunk_and_embed(fileContent, fileName)
                    # Set the document in Redis
                    #set_document(data)
                else:
                    logging.info("Embedding Non-text file")
                    readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                    downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                    try:
                        with open(downloadPath, "wb") as file:
                            file.write(readBytes)
                    except Exception as e:
                        logging.error(e)

                    logging.info("File created " + downloadPath)
                    textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                    docs = []
                    loader = PDFMinerLoader(downloadPath)
                    #loader = PyMuPDFLoader(downloadPath)
                    rawDocs = loader.load()
                    docs = textSplitter.split_documents(rawDocs)
                    #embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)
                    embeddings = OpenAIEmbeddings(document_model_name=OpenAiEmbedding,
                                                    chunk_size=1,
                                                    openai_api_key=OpenAiKey)
                    if indexType == 'pinecone': 
                        pineconeDb = Pinecone.from_documents(docs, embeddings, index_name=VsIndexName, namespace=uResultNs.hex)
                    elif indexType == "redis":
                        redisConnection = Redis(redis_url=redisUrl, index_name=uResultNs.hex, embedding_function=embeddings)
                        Redis.from_documents(docs, embeddings, redis_url=redisUrl, index_name=uResultNs.hex)
                    elif indexType == "cogsearch":
                        createSearchIndex(uResultNs.hex)
                        indexSections(fileName, uResultNs.hex, docs)
                    elif indexType == 'milvus':
                        milvusDb = Milvus.from_documents(docs,embeddings)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs)
                logging.info("Upsert metadata")
                metadata = {'embedded': 'true', 'namespace': uResultNs.hex, 'indexType': indexType, "indexName": indexName}
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                metadata = {'summary': summary, 'qa': qa}
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                logging.info("Sleeping")
                time.sleep(5)
            return "Success"
        except Exception as e:
            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
            return "Error"
      elif (loadType == "webpages"):
        try:
            allDocs = []
            for webPage in value:
                logging.info("Processing Webpage at " + webPage)
                textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
                docs = []
                loader = WebBaseLoader(webPage)
                rawDocs = loader.load()
                docs = textSplitter.split_documents(rawDocs)
                embeddings = OpenAIEmbeddings(document_model_name=OpenAiEmbedding,
                                                chunk_size=1,
                                                openai_api_key=OpenAiKey)
                allDocs = allDocs + docs
                if indexType == 'pinecone':
                    pineconeDb = Pinecone.from_documents(docs, embeddings, index_name=VsIndexName, namespace=uResultNs.hex)
                elif indexType == "redis":
                    Redis.from_documents(docs, embeddings, redis_url=redisUrl, index_name=uResultNs.hex)
                elif indexType == "cogsearch":
                    createSearchIndex(uResultNs.hex)
                    indexSections(fileName, uResultNs.hex, docs)
                elif indexType == "weaviate":
                    try:
                        import weaviate
                        client = weaviate.Client(url=WeaviateUrl)
                        weaviate = Weaviate(client, index_name=uResultNs.hex, text_key="content")
                        texts = [d.page_content for d in docs]
                        metadatas = [d.metadata for d in docs]
                        weaviate.add_texts(texts, metadatas)
                        #weaviate.from_documents(docs, embeddings)
                    except Exception as e:
                        logging.info(e)

                elif indexType == 'milvus':
                    milvusDb = Milvus.from_documents(docs,embeddings)
            logging.info("Perform Summarization and QA")
            qa, summary = summarizeGenerateQa(allDocs)
            logging.info("Upsert metadata")
            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': uResultNs.hex, 'indexType': indexType, "indexName": indexName})
            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
            return "Success"
        except Exception as e:
            logging.info(e)
            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
            return "Error"
      elif (loadType == "iFixIt"):
        logging.info("Embedding iFixIt")
        return "Success"
    
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(indexType, loadType,  multiple, indexName, record):
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

        summaryResponse = Embed(indexType, loadType,  multiple, indexName, value)
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

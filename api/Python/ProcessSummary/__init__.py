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
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from Utilities.pibCopilot import createSearchIndex, indexSections, findSummaryInIndex, performCogSearch, mergeDocs, createProspectusSummary, findTopicSummaryInIndex
from langchain.docstore.document import Document
import uuid
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from Utilities.redisIndex import performRedisSearch

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
        indexNs = req.params.get('indexNs')
        indexType = req.params.get('indexType')
        existingSummary = req.params.get('existingSummary')
        logging.info(f'indexNs: {indexNs}')
        logging.info(f'indexType: {indexType}')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(indexNs, indexType, existingSummary, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexNs, indexType, existingSummary, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexNs, indexType, existingSummary, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def summarizeTopic(llm, query, promptTemplate, embeddings, embeddingModelType, indexNs, indexType, topK):
    if indexType == 'pinecone':
        try:
            pinecone.init(
                api_key=PineconeKey,  # find at app.pinecone.io
                environment=PineconeEnv  # next to api key in console
            )
            vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
            docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
            #resultsDoc = docRetriever.get_relevant_documents(query)
            resultsDoc = vectorDb.similarity_search(query, k=topK)
        except Exception as e:
            logging.info(f"Error: {e}")
            resultsDoc = [Document(page_content="No results found")]
        logging.info(f"Found {len(resultsDoc)} Pinecone results")
    elif indexType == 'cogsearchvs':                
        r = performCogSearch(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, OpenAiEmbedding, query, indexNs, topK)
        if r == None:
            resultsDoc = [Document(page_content="No results found")]
        else :
            resultsDoc = [
                    Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                    for doc in r
                    ]
        logging.info(f"Found {len(resultsDoc)} Cog Search results")
    elif indexType == "redis":
        try:
            returnField = ["metadata", "content", "vector_score"]
            vectorField = "content_vector"
            results = performRedisSearch(query, indexNs, topK, returnField, vectorField, embeddingModelType)
            resultsDoc = [
                    Document(page_content=result.content, metadata=json.loads(result.metadata))
                    for result in results.docs
            ]
        except:
            logging.info(f"Error: {e}")
            resultsDoc = [Document(page_content="No results found")]
        logging.info(f"Found {len(resultsDoc)} Redis results")
    
    if len(resultsDoc) == 0:
        return "I don't know"
    else:
        customPrompt = PromptTemplate(template=promptTemplate, input_variables=["text"])
        chainType = "map_reduce"
        summaryChain = load_summarize_chain(llm, chain_type=chainType, return_intermediate_steps=True, 
                                            map_prompt=customPrompt, combine_prompt=customPrompt)
        summary = summaryChain({"input_documents": resultsDoc}, return_only_outputs=True)
        outputAnswer = summary['output_text']
        return outputAnswer 

def processTopicSummary(llm, fileName, indexNs, indexType, prospectusSummaryIndexName, embeddings, embeddingModelType, selectedTopics, 
                        summaryPromptTemplate, topK, existingSummary):
    # r = findFileInIndex(SearchService, SearchKey, prospectusIndexName, fileName)
    # if r.get_count() == 0:
    #     rawDocs = blobLoad(OpenAiDocConnStr, OpenAiDocContainer, fileName)
    #     textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(8000), chunk_overlap=int(1000))
    #     docs = textSplitter.split_documents(rawDocs)
    #     logging.info("Docs " + str(len(docs)))
    #     createSearchIndex(SearchService, SearchKey, prospectusIndexName)
    #     indexSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType,
    #                    OpenAiEmbedding, fileName, prospectusIndexName, docs)
    # else:
    #     logging.info('Found existing data')

    createProspectusSummary(SearchService, SearchKey, prospectusSummaryIndexName)
    topicSummary = []
    logging.info(f"Existing Summary: {existingSummary}")
    if existingSummary == "true":
        logging.info(f"Found existing summary")
        r = findSummaryInIndex(SearchService, SearchKey, prospectusSummaryIndexName, fileName, 'prospectus')
        for s in r:
            topicSummary.append(
                {
                    'id' : s['id'],
                    'fileName': s['fileName'],
                    'docType': s['docType'],
                    'topic': s['topic'],
                    'summary': s['summary']
                })
    else:
        for topic in selectedTopics:
            r = findTopicSummaryInIndex(SearchService, SearchKey, prospectusSummaryIndexName, fileName, 'prospectus', topic)
            if r.get_count() == 0:
                logging.info(f"Summarize on Topic: {topic}")
                answer = summarizeTopic(llm, topic, summaryPromptTemplate, embeddings, embeddingModelType, indexNs, indexType, topK)
                if "I don't know" not in answer:
                    topicSummary.append({
                        'id' : str(uuid.uuid4()),
                        'fileName': fileName,
                        'docType': 'prospectus',
                        'topic': topic,
                        'summary': answer
                })
            else:
                for s in r:
                    topicSummary.append(
                        {
                            'id' : s['id'],
                            'fileName': s['fileName'],
                            'docType': s['docType'],
                            'topic': s['topic'],
                            'summary': s['summary']
                        })
        mergeDocs(SearchService, SearchKey, prospectusSummaryIndexName, topicSummary)
    return topicSummary

def summarizeTopics(indexNs, indexType, existingSummary, overrides):
    prospectusSummaryIndexName = 'summary'

    embeddingModelType = overrides.get("embeddingModelType") or 'azureopenai'
    selectedTopics = overrides.get("topics") or []
    summaryPromptTemplate = overrides.get("promptTemplate") or ''
    temperature = overrides.get("temperature") or 0.3
    tokenLength = overrides.get("tokenLength") or 1500
    fileName = overrides.get("fileName") or ''
    topK = overrides.get("top") or 3
    deploymentType = overrides.get('deploymentType') or 'gpt3516k'

    # logging.info(f"embeddingModelType: {embeddingModelType}")
    # logging.info(f"selectedTopics: {selectedTopics}")
    # logging.info(f"summaryPromptTemplate: {summaryPromptTemplate}")
    # logging.info(f"temperature: {temperature}")
    # logging.info(f"tokenLength: {tokenLength}")
    # logging.info(f"fileName: {fileName}")
    # logging.info(f"topK: {topK}")
    # logging.info(f"deploymentType: {deploymentType}")

    if summaryPromptTemplate == '':
        summaryPromptTemplate = """You are an AI assistant tasked with summarizing documents from large documents that contains information about Initial Public Offerings. 
        IPO document contains sections with information about the company, its business, strategies, risk, management structure, financial, and other information.
        Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive summary that includes details. 
        Ensure that the summary is easy to understand and provides an accurate representation. 
        Begin the summary with a brief introduction, followed by the main points.
        Generate the summary with minimum of 7 paragraphs and maximum of 10 paragraphs.
        Please remember to use clear language and maintain the integrity of the original information without missing any important details:
        {text}

        """
    
    if (embeddingModelType == 'azureopenai'):
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"{OpenAiEndPoint}"

        if deploymentType == 'gpt35':
            llm = AzureChatOpenAI(
                    openai_api_base=openai.api_base,
                    openai_api_version=OpenAiVersion,
                    deployment_name=OpenAiChat,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    openai_api_type="azure",
                    max_tokens=tokenLength)
        elif deploymentType == "gpt3516k":
            llm = AzureChatOpenAI(
                    openai_api_base=openai.api_base,
                    openai_api_version=OpenAiVersion,
                    deployment_name=OpenAiChat16k,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    openai_api_type="azure",
                    max_tokens=tokenLength)
            
        embeddings = OpenAIEmbeddings(deployment=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
        logging.info("LLM Setup done")
    elif embeddingModelType == "openai":
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07' 
        openai.api_key = OpenAiApiKey
        llm = ChatOpenAI(temperature=temperature,
            openai_api_key=OpenAiApiKey,
            model_name="gpt-3.5-turbo",
            max_tokens=tokenLength)
        embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)


    summaryTopicData = processTopicSummary(llm, fileName, indexNs, indexType, prospectusSummaryIndexName, embeddings, embeddingModelType, 
                            selectedTopics, summaryPromptTemplate, topK, existingSummary)
    outputFinalAnswer = {"data_points": '', "answer": summaryTopicData, 
                    "thoughts": '',
                        "sources": '', "nextQuestions": '', "error": ""}
    return outputFinalAnswer

def TransformValue(indexNs, indexType, existingSummary, record):
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
        overrides = data['overrides']
        summaryResponse = summarizeTopics(indexNs, indexType, existingSummary, overrides)
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

import logging, json, os
import azure.functions as func
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.summarize import load_summarize_chain
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import RegexParser
#from langchain.vectorstores.redis import Redis
from redis import Redis
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.field import VectorField, TagField, TextField
import numpy as np
from langchain.docstore.document import Document
import tiktoken
from typing import Mapping
from langchain.chains.question_answering import load_qa_chain
from Utilities.envVars import *
from Utilities.cogSearch import performCogSearch
from Utilities.azureBlob import upsertMetadata, getAllBlobs

redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
redisConnection = Redis(host= RedisAddress, port=RedisPort, password=RedisPassword) #api for Docker localhost for local execution

def getEmbedding(text: str, engine="text-embedding-ada-002") -> list[float]:
    try:
        text = text.replace("\n", " ")
        EMBEDDING_ENCODING = 'cl100k_base' if engine == 'text-embedding-ada-002' else 'gpt2'
        encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)
        return openai.Embedding.create(input=encoding.encode(text), engine=engine)["data"][0]["embedding"]
    except Exception as e:
        logging.info(e)


def performRedisSearch(question, indexName, k):
    #embeddingQuery= Redis.embedding_function(question)
    question = question.replace("\n", " ")
    embeddingQuery = getEmbedding(question, engine=OpenAiEmbedding)
    arrayEmbedding = np.array(embeddingQuery)
    returnField = ["metadata", "content", "vector_score"]
    vectorField = "content_vector"
    hybridField = "*"
    baseQuery = (
        f"{hybridField}=>[KNN {k} @{vectorField} $vector AS vector_score]"
    )
    redisQuery = (
        Query(baseQuery)
        .return_fields(*returnField)
        .sort_by("vector_score")
        .paging(0, 5)
        .dialect(2)
    )
    params_dict: Mapping[str, str] = {
            "vector": np.array(arrayEmbedding)  # type: ignore
            .astype(dtype=np.float32)
            .tobytes()
    }

    # perform vector search
    results = redisConnection.ft(indexName).search(redisQuery, params_dict)

    documents = [
        Document(page_content=result.content, metadata=json.loads(result.metadata))
        for result in results.docs
    ]

    return documents

def summarizeGenerateQa(indexType, indexNs, embeddingModelType, requestType, chainType, value):
    if (embeddingModelType == 'azureopenai'):
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"

        llm = AzureChatOpenAI(
                openai_api_base=openai.api_base,
                openai_api_version="2023-03-15-preview",
                deployment_name=OpenAiChat,
                temperature=0,
                openai_api_key=OpenAiKey,
                openai_api_type="azure",
                max_tokens=400)

        embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
        logging.info("LLM Setup done")
    elif embeddingModelType == "openai":
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07' 
        openai.api_key = OpenAiApiKey
        llm = ChatOpenAI(temperature=0,
            openai_api_key=OpenAiApiKey,
            model_name="gpt-3.5-turbo",
            max_tokens=400)
        embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)
    
    qaTemplate = """Use the following portion of a long document.
        {context}
        Question: {question}
        """

    qaPrompt = PromptTemplate(
        template=qaTemplate, input_variables=["context", "question"]
    )

    combinePromptTemplate = """Given the following extracted parts of a long document and a question, recommend between 1-5 sample questions.

    QUESTION: {question}
    =========
    {summaries}
    =========
    """
    combinePrompt = PromptTemplate(
        template=combinePromptTemplate, input_variables=["summaries", "question"]
    )
    qaChain = load_qa_with_sources_chain(llm,
        chain_type="map_reduce", question_prompt=qaPrompt, combine_prompt=combinePrompt)
    qa = "No Sample QA Generated"
    summary = "No Summary Generated"

    if indexType == 'pinecone':
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": 10})
        logging.info("Pinecone Setup done for indexName : " + indexNs)
        
        logging.info("Pinecone Setup done")
        if (requestType == "qa"):
            try:
                chain = RetrievalQAWithSourcesChain(combine_documents_chain=qaChain, retriever=docRetriever, 
                                                    return_source_documents=True)
                answer = chain({"question": 'Generate 1-5 sample questions'}, return_only_outputs=True)
                qa = answer['answer'].replace('\Generate 1-5 sample questions:\n', '').replace('\nSample Questions:\n', '').replace('\n', '\\n')
            except Exception as e:
                logging.info(e)

        if (requestType == "summary"):
            try:
                summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
                rawDocs = vectorDb.similarity_search('*', k=10, namespace=indexNs)
                summary = summaryChain.run(rawDocs)
            except Exception as e:
                logging.info(e)
                
    elif indexType == "redis":
        try:
            docs = performRedisSearch('question', indexNs, 10)
            if (requestType == "qa"):
                answer = qaChain({"input_documents": docs, "question": 'question'}, return_only_outputs=True)
                qa = answer['output_text']
            if (requestType == "summary"):
                summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
                summary = summaryChain.run(docs)
        except Exception as e:
            return {"answer": "Working on fixing Redis Implementation - Error : " + str(e) }
        
    elif indexType == "cogsearch" or indexType == "cogsearchvs":
        r = performCogSearch(indexType, embeddingModelType, "*", indexNs, 10)
        if r == None:
            docs = [Document(page_content="No results found")]
        else :
            docs = [
                Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                for doc in r
                ]
        rawDocs=[]
        for doc in docs:
            rawDocs.append(doc.page_content)
        if (requestType == "qa"):
            answer = qaChain({"input_documents": docs, "question": 'question'}, return_only_outputs=True)
            qa = answer['output_text']
        if (requestType == "summary"):
            summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
            summary = summaryChain.run(docs)

    elif indexType == 'milvus':
        answer = "{'answer': 'TBD'}"

    if (requestType == "qa"):
        metadata = {'qa': qa.replace("-", "_")}
    elif (requestType == "summary"):
        metadata = {'summary': summary.replace("-", "_"), 'qa': qa.replace("-", "_")}
    
    try:
        blobList = getAllBlobs(OpenAiDocConnStr, OpenAiDocContainer)
        for blob in blobList:
            try:
                if (blob.metadata['namespace'] == indexNs):
                    upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blob.name, metadata)
            except:
                continue
    except:
        pass

    return qa, summary

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
        indexNs = req.params.get('indexNs')
        requestType = req.params.get('requestType')
        chainType=req.params.get("chainType")
        embeddingModelType=req.params.get("embeddingModelType")
        logging.info("Input parameters : " + " " + indexType)
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
        result = ComposeResponse(indexType, indexNs, embeddingModelType, requestType, chainType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexType, indexNs, embeddingModelType, requestType, chainType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, indexNs, embeddingModelType, requestType, chainType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(indexType, indexNs, embeddingModelType, requestType, chainType, record):
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

        qa, summary = summarizeGenerateQa(indexType, indexNs, embeddingModelType, requestType, chainType, value)
        return ({
            "recordId": recordId,
            "qa": qa,
            "summary": summary
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

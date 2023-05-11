import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import OpenAI, AzureOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.summarize import load_summarize_chain
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains import VectorDBQAWithSourcesChain
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

def summarizeGenerateQa(indexType, value, indexNs):
    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiKey,
                max_tokens=1024,
                batch_size=10)
    
    embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)

    if indexType == 'pinecone':
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        logging.info("Pinecone Setup done")
        try:
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
                
            chain = VectorDBQAWithSourcesChain(combine_documents_chain=qaChain, vectorstore=vectorDb, 
                                                search_kwargs={"namespace": indexNs})
            answer = chain({"question": 'Generate 1-5 sample questions'}, return_only_outputs=True)
            qa = answer['answer'].replace('\Generate 1-5 sample questions:\n', '').replace('\nSample Questions:\n', '').replace('\n', '\\n')
            #logging.info(qa)
        except Exception as e:
            logging.info(e)

        try:
            summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
            rawDocs = vectorDb.similarity_search('*', k=1000, namespace=indexNs)
            summary = summaryChain.run(rawDocs)
            #logging.info(summary)
        except Exception as e:
            logging.info(e)
    elif indexType == "redis":
        try:
            docs = performRedisSearch('question', indexNs, 10)
            answer = qaChain({"input_documents": docs, "question": 'question'}, return_only_outputs=True)
            logging.info(answer)
            return {"answer": answer['output_text']}
        except Exception as e:
            return {"answer": "Working on fixing Redis Implementation - Error : " + str(e) }

    elif indexType == 'milvus':
        answer = "{'answer': 'TBD'}"

    return qa, summary

def FindAnswer(question, indexType, value, indexNs):
    logging.info("Calling FindAnswer Open AI")
    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    answer = ''

    # https://langchain.readthedocs.io/en/latest/modules/indexes/chain_examples/qa_with_sources.html

    try:
      llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=0,
                openai_api_key=OpenAiKey,
                max_tokens=1024,
                batch_size=10)

      logging.info("LLM Setup done")
      embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
      template = """Given the following extracted parts of a long document, Generate 5 questions..
            Give me that without numbering.

            =========
            {summaries}
            =========
            """
      qaPrompt = PromptTemplate(template=template, input_variables=["summaries"])
      qaChain = load_qa_with_sources_chain(llm, chain_type='stuff', prompt=qaPrompt)


      if indexType == 'pinecone':
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        logging.info("Pinecone Setup done")
        chain = VectorDBQAWithSourcesChain(combine_documents_chain=qaChain, vectorstore=vectorDb, 
                                         search_kwargs={"namespace": indexNs})
        answer = chain({"question": question}, return_only_outputs=True)
        return {"answer": answer['answer'].replace('\nSample Questions:\n', '')}
        logging.info(answer)
      elif indexType == "redis":
        try:
             docs = performRedisSearch(question, indexNs, 10)
             answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
             logging.info(answer)
             return {"answer": answer['output_text']}
        except Exception as e:
            return {"answer": "Working on fixing Redis Implementation - Error : " + str(e) }

      elif indexType == 'milvus':
          answer = "{'answer': 'TBD'}"

    except Exception as e:
      logging.info("Error in FindAnswer Open AI : " + str(e))
      return {"answer": "Working on fixing Implementation - Error : " + str(e) }

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
        result = ComposeResponse(indexType, body, indexNs)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(indexType, jsonData, indexNs):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, value, indexNs)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(indexType, record, indexNs):
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

        qa, summary = summarizeGenerateQa(indexType, value, indexNs)
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

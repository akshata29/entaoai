import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains import VectorDBQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import RegexParser
from redis import Redis
import numpy as np
from langchain.docstore.document import Document
#from langchain.vectorstores import Weaviate
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch

OpenAiKey = os.environ['OpenAiKey']
OpenAiEndPoint = os.environ['OpenAiEndPoint']
OpenAiVersion = os.environ['OpenAiVersion']
OpenAiDavinci = os.environ['OpenAiDavinci']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
OpenAiService = os.environ['OpenAiService']
OpenAiDocStorName = os.environ['OpenAiDocStorName']
OpenAiDocStorKey = os.environ['OpenAiDocStorKey']
OpenAiDocConnStr = f"DefaultEndpointsProtocol=https;AccountName={OpenAiDocStorName};AccountKey={OpenAiDocStorKey};EndpointSuffix=core.windows.net"
OpenAiDocContainer = os.environ['OpenAiDocContainer']
PineconeEnv = os.environ['PineconeEnv']
PineconeKey = os.environ['PineconeKey']
VsIndexName = os.environ['VsIndexName']
SearchService = os.environ['SearchService']
SearchKey = os.environ['SearchKey']

def FindAnswer(chainType, question, indexType, value, indexNs, approach, overrides):
    logging.info("Calling FindAnswer Open AI")
    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    answer = ''

    # https://langchain.readthedocs.io/en/latest/modules/indexes/chain_examples/qa_with_sources.html

    try:
        topK = overrides.get("top") or 5
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        logging.info("Search for Top " + str(topK) + " and chainType is " + str(overrideChain))
        if (approach == 'rtr'):
            llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    max_tokens=tokenLength,
                    batch_size=10)

            logging.info("LLM Setup done")
            embeddings = OpenAIEmbeddings(document_model_name=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)

            if (overrideChain == "stuff"):
                template = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
                If you don't know the answer, just say that you don't know. Don't try to make up an answer.
                ALWAYS return a "SOURCES" part in your answer.

                QUESTION: {question}
                =========
                {summaries}
                =========
                """
                qaPrompt = PromptTemplate(template=template, input_variables=["summaries", "question"])
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, prompt=qaPrompt)
            elif (overrideChain == "map_rerank"):
                outputParser = RegexParser(
                    regex=r"(.*?)\nScore: (.*)",
                    output_keys=["answer", "score"],
                )

                promptTemplate = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

                In addition to giving an answer, also return a score of how fully it answered the user's question. This should be in the following format:

                Question: [question here]
                [answer here]
                Score: [score between 0 and 100]

                Begin!

                Context:
                ---------
                {context}
                ---------
                Question: {question}
                """
                qaPrompt = PromptTemplate(
                    template=promptTemplate,
                    input_variables=["context", "question"],
                    output_parser=outputParser,
                )
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, metadata_keys=['source'], prompt=qaPrompt)
            elif (overrideChain == "map_reduce"):

                qaTemplate = """Use the following portion of a long document to see if any of the text is relevant to answer the question.
                Return any relevant text.
                {context}
                Question: {question}
                Relevant text, if any :"""

                qaPrompt = PromptTemplate(
                    template=qaTemplate, input_variables=["context", "question"]
                )

                combinePromptTemplate = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
                If you don't know the answer, just say that you don't know. Don't try to make up an answer.
                ALWAYS return a "SOURCES" part in your answer.

                QUESTION: {question}
                =========
                {summaries}
                =========
                """
                combinePrompt = PromptTemplate(
                    template=combinePromptTemplate, input_variables=["summaries", "question"]
                )
                qaChain = load_qa_with_sources_chain(llm,
                    chain_type=overrideChain, question_prompt=qaPrompt, combine_prompt=combinePrompt)
            elif (overrideChain == "refine"):
                refineTemplate = (
                    "The original question is as follows: {question}\n"
                    "We have provided an existing answer, including sources: {existing_answer}\n"
                    "We have the opportunity to refine the existing answer"
                    "(only if needed) with some more context below.\n"
                    "------------\n"
                    "{context_str}\n"
                    "------------\n"
                    "Given the new context, refine the original answer to better "
                    "If you do update it, please update the sources as well. "
                    "If the context isn't useful, return the original answer."
                )
                refinePrompt = PromptTemplate(
                    input_variables=["question", "existing_answer", "context_str"],
                    template=refineTemplate,
                )

                qaTemplate = (
                    "Context information is below. \n"
                    "---------------------\n"
                    "{context_str}"
                    "\n---------------------\n"
                    "Given the context information and not prior knowledge, "
                    "answer the question: {question}\n"
                )
                qaPrompt = PromptTemplate(
                    input_variables=["context_str", "question"], template=qaTemplate
                )
                qaChain = load_qa_with_sources_chain(llm,
                chain_type=overrideChain, question_prompt=qaPrompt, refine_prompt=refinePrompt)

            if indexType == 'pinecone':
                vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
                logging.info("Pinecone Setup done")
                chain = VectorDBQAWithSourcesChain(combine_documents_chain=qaChain, vectorstore=vectorDb, k=topK, 
                                                search_kwargs={"namespace": indexNs})
                answer = chain({"question": question}, return_only_outputs=True)
                return {"data_points": [], "answer": answer['answer'].replace("Answer: ", ''), "thoughts": answer['sources'], "error": ""}
            elif indexType == "redis":
                try:
                    returnField = ["metadata", "content", "vector_score"]
                    vectorField = "content_vector"
                    results = performRedisSearch(question, indexNs, topK, returnField, vectorField)
                    docs = [
                            Document(page_content=result.content, metadata=json.loads(result.metadata))
                            for result in results.docs
                    ]
                    answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    return {"data_points": [], "answer": answer['output_text'].replace("Answer: ", ''), "thoughts": '', "error": ""}
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": ""}
            elif indexType == "cogsearch":
                try:
                    r = performCogSearch(question, indexNs, topK)
                    if r == None:
                        docs = [Document(page_content="No results found")]
                    else :
                        docs = [
                            Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                            for doc in r
                            ]
                    answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    return {"data_points": [], "answer": answer['output_text'].replace("Answer: ", ''), "thoughts": '', "error": ""}
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": ""}    
            #   elif indexType == "weaviate":
            #         try:
            #             import weaviate
            #             client = weaviate.Client(url=WeaviateUrl)
            #             logging.info("Client initialized")
            #             weaviate = Weaviate(client, index_name=indexNs, text_key="content")
            #             docs = weaviate.similarity_search(question, topK)
            #             logging.info(docs)
            #             answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
            #             return {"data_points": [], "answer": answer['output_text'].replace("Answer: ", ''), "thoughts": '', "error": ""}
            #         except Exception as e:
            #             logging.info("Exception occurred in weaviate " + str(e))
            #             return {"data_points": [], "answer": answer['output_text'], "thoughts": '', "error": ""}
            elif indexType == 'milvus':
                answer = "{'answer': 'TBD', 'sources': ''}"
                return answer
        elif approach == 'rrr':
            answer = "{'answer': 'TBD', 'sources': ''}"
            return answer
        elif approach == 'rca':
            answer = "{'answer': 'TBD', 'sources': ''}"
            return answer
    

    except Exception as e:
      logging.info("Error in FindAnswer Open AI : " + str(e))

    #return answer

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
        question = req.params.get('question')
        indexType = req.params.get('indexType')
        indexNs = req.params.get('indexNs')
        logging.info("Input parameters : " + chainType + " " + question + " " + indexType)
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
        result = ComposeResponse(chainType, question, indexType, body, indexNs)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(chainType, question, indexType, jsonData, indexNs):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(chainType, question, indexType, value, indexNs)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(chainType, question, indexType, record, indexNs):
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
        approach = data['approach']
        overrides = data['overrides']

        answer = FindAnswer(chainType, question, indexType, value, indexNs, approach, overrides)
        return ({
            "recordId": recordId,
            "data": answer
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

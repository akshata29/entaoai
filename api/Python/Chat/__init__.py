import logging, json, os
import azure.functions as func
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.llms.openai import AzureOpenAI
#from langchain.vectorstores.redis import Redis
from redis import Redis
import numpy as np
from langchain.docstore.document import Document
from typing import Mapping
from langchain import LLMChain, PromptTemplate
from langchain.chains import ChatVectorDBChain
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.chains import VectorDBQAWithSourcesChain
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch

OpenAiKey = os.environ['OpenAiKey']
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
OpenAiChat = os.environ['OpenAiChat']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
SearchService = os.environ['SearchService']
SearchKey = os.environ['SearchKey']


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
        question = req.params.get('question')
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
        result = ComposeResponse(body, indexNs, indexType, question, indexName)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(jsonData, indexNs, indexType, question, indexName):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(value, indexNs, indexType, question, indexName)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def getChatHistory(history, includeLastTurn=True, maxTokens=1000) -> str:
    historyText = []
    
    for h in reversed(history if includeLastTurn else history[:-1]):
        user = h['user']
        bot = (h.get("bot") if h.get("bot") else "")
        historyText.append((user, bot))
        if len(historyText) > maxTokens*4:
            break
    return historyText

def GetRrrAnswer(history, indexNs, indexType, question, indexName):

    qaTemplate = """You are an AI assistant for the all questions on document.
    I am still improving my Knowledge base. The documentation is located from document. You have a deep understanding of the document.
    You are given the following extracted parts of a long document and a question. Provide an answer with a hyperlink to the PDF or with a code block directly from the PDF. You should only use hyperlinks that are explicitly listed as a source in the context. Do NOT make up a hyperlink that is not listed. If you don't know the answer, just say 'Hmm, I'm not sure.' Don't try to make up an answer. If the question is not about
    the information in document, politely inform them that you are tuned to only answer questions about information in the document.
    
    ========= 
    {context} 
    Question: {question} 
    ========= 
    """

    qaTemplate1 = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
        If you don't know the answer, just say that you don't know. Don't try to make up an answer.
        QUESTION: {question}
        =========
        {summaries}
        =========
    """

    condenseTemplate = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
    
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:
    """

    systemTemplate="""Use the following pieces of context to answer the users question. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    ----------------
    {context}"""
    
    messages = [
        SystemMessagePromptTemplate.from_template(systemTemplate),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
    qaPrompt2 = ChatPromptTemplate.from_messages(messages)

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

    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    qaPrompt = PromptTemplate(
              template=qaTemplate, input_variables=["question", "context"]
          )
    qaPrompt1 = PromptTemplate(
              template=qaTemplate1, input_variables=["question", "summaries"]
          )

    condensePrompt = PromptTemplate(
              template=condenseTemplate, input_variables=["question", "chat_history"]
          )

    try:
        llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=os.environ['Temperature'] or 0.3,
                openai_api_key=OpenAiKey,
                max_tokens=os.environ['MaxTokens'] or 500,
                batch_size=10)
        embeddings = OpenAIEmbeddings(document_model_name=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
        
        if indexType == 'pinecone':
            vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
            logging.info("Pinecone Setup done for indexName : " + indexNs)
            # chain = ChatVectorDBChain.from_llm(llm, vectorstore=vectorDb,qa_prompt=qaPrompt, 
            #     condense_question_prompt=condensePrompt, chain_type="stuff", search_kwargs={"namespace": indexNs})
            
            #questionGenerator = LLMChain(llm=llm, prompt=condensePrompt)
            #docChain = load_qa_chain(llm, chain_type="stuff")
            qaChain = load_qa_with_sources_chain(llm,
            chain_type="map_reduce", question_prompt=qaPrompt, combine_prompt=combinePrompt)
            chain = VectorDBQAWithSourcesChain(combine_documents_chain=qaChain, vectorstore=vectorDb, 
                                         search_kwargs={"namespace": indexNs})
            # chain = ChatVectorDBChain(vectorstore=vectorDb, combine_docs_chain=docChain, 
            #                            question_generator=questionGenerator,
            #                            search_kwargs={"namespace": indexNs})
            historyText = getChatHistory(history, includeLastTurn=False)
            answer = chain({"question": question, "chat_history": historyText}, return_only_outputs=True)
            logging.info(answer)
            return {"data_points": "", "answer": answer['answer'].replace("Answer: ", ''), "thoughts": ""}

        elif indexType == "redis":
            try:
                returnField = ["metadata", "content", "vector_score"]
                vectorField = "content_vector"
                results = performRedisSearch(question, indexNs, 5, returnField, vectorField)
                docs = [
                        Document(page_content=result.content, metadata=json.loads(result.metadata))
                        for result in results.docs
                ]
                qaChain = load_qa_with_sources_chain(llm,
                    chain_type="map_reduce", question_prompt=qaPrompt, combine_prompt=combinePrompt)
                answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                return {"data_points": [], "answer": answer['output_text'].replace('Answer: ', ''), "thoughts": '', "error": ""}
            except Exception as e:
                return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": ""}
        elif indexType == "cogsearch":
            r = performCogSearch(question, indexNs, 5)
            if r == None:
                    docs = [Document(page_content="No results found")]
            else :
                docs = [
                    Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                    for doc in r
                    ]
            qaChain = load_qa_with_sources_chain(llm,
                    chain_type="map_reduce", question_prompt=qaPrompt, combine_prompt=combinePrompt)
            answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
            logging.info(answer)
            return {"data_points": [], "answer": answer['output_text'].replace('Answer: ', ''), "thoughts": '', "error": ""}
        elif indexType == 'milvus':
            answer = "{'answer': 'TBD', 'sources': ''}"
            return answer
        
    except Exception as e:
        logging.info(e)

    return {"data_points": "", "answer": "", "thoughts": ""}

def GetAnswer(history, approach, overrides, indexNs, indexType, question, indexName):
    logging.info("Getting Answer")
    try:
      logging.info("Loading OpenAI")
      if (approach == 'rrr'):
        r = GetRrrAnswer(history, indexNs, indexType, question, indexName)
      else:
          return json.dumps({"error": "unknown approach"})
      return r
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(record, indexNs, indexType, question, indexName):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:
        assert ('data' in record), "'data' field is required."
        data = record['data']
        #assert ('text' in data), "'text' field is required in 'data' object."

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
        history = data['history']
        approach = data['approach']
        overrides = data['approach']

        summaryResponse = GetAnswer(history, approach, overrides, indexNs, indexType, question, indexName)
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

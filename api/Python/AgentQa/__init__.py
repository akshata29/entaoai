import logging, json, os
import azure.functions as func
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
import numpy as np
from langchain.chains import RetrievalQA
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.schema import (
    AgentAction,
    AgentFinish,
)
from Utilities.envVars import *
from langchain.vectorstores.redis import Redis
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

def addTool(indexType, embeddings, llm, overrideChain, indexNs, indexName, returnDirect, topK):
    if indexType == "pinecone":
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever(search_kwargs={"k": topK}))
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool
    elif indexType == "redis":
        redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
        vectorDb = Redis.from_existing_index(index_name=indexNs, embedding=embeddings, redis_url=redisUrl)
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever(search_kwargs={"k": topK}))
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool

def AgentQaAnswer(question, overrides):
    logging.info("Calling AgentQaAnswer Open AI")
   
    answer = ''
    try:
        topK = overrides.get("top") or 5
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        indexes = json.loads(json.dumps(overrides.get('indexes')))
        indexType = overrides.get('indexType')
        embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
        logging.info("Search for Top " + str(topK) + " and chainType is " + str(overrideChain))


        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureChatOpenAI(
                        openai_api_base=openai.api_base,
                        openai_api_version=OpenAiVersion,
                        deployment_name=OpenAiChat,
                        temperature=temperature,
                        openai_api_key=OpenAiKey,
                        openai_api_type="azure",
                        max_tokens=tokenLength)

            embeddings = OpenAIEmbeddings(deployment=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
            logging.info("Azure OpenAI LLM Setup done")
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
            logging.info("OpenAI LLM Setup done")
        
        tools = []
        for index in indexes:
            indexNs = index['indexNs']
            indexName = index['indexName']
            returnDirect = bool(index['returnDirect'])
            tool = addTool(indexType, embeddings, llm, overrideChain, indexNs, indexName, returnDirect, topK)
            tools.append(tool)

        logging.info("Index Setup done")
        agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
                    verbose=False, return_intermediate_steps=True)
        answer = agent({"input":question})
        logging.info(answer)
        action = answer['intermediate_steps']

        sources = ''
        for a, data in action:
            sources = a.tool
            break;
        
        followupQaPromptTemplate = """Generate three very brief follow-up questions from the answer that the user would likely ask next.
        Use double angle brackets to reference the questions, e.g. <Is there a more details on that?>.
        Try not to repeat questions that have already been asked.
        Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'

        {context} 
        """

        docs = [Document(page_content=answer['output'])]
        followupPrompt = PromptTemplate(template=followupQaPromptTemplate, input_variables=["context"])
        followupChain = load_qa_chain(llm, chain_type='stuff', prompt=followupPrompt)
        nextQuestions = followupChain({"input_documents": docs, "question": ''}, return_only_outputs=True)
        nextQuestions = nextQuestions['output_text']
    
        return {"data_points": [], "answer": answer['output'].replace("Answer: ", ''), "thoughts": answer['intermediate_steps'], "sources": sources, "nextQuestions":nextQuestions, "error": ""}

    except Exception as e:
        logging.info("Error in AgentQaAnswer Open AI : " + str(e))
        return {"data_points": [], "answer": 'Exception Occured :' + str(e), "thoughts": '', "sources": '', "nextQuestions":'', "error": str(e)}

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
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        if len(PineconeKey) > 10 and len(PineconeEnv) > 10:
            pinecone.init(
                api_key=PineconeKey,  # find at app.pinecone.io
                environment=PineconeEnv  # next to api key in console
            )
        result = ComposeResponse(body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(record):
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
        question = data['question']

        answer = AgentQaAnswer(question, overrides)
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

import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI
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

def addTool(indexType, embeddings, llm, overrideChain, indexNs, indexName, returnDirect):
    if indexType == "pinecone":
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever())
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool
    elif indexType == "redis":
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever())
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool

def FindAnswer(question, overrides):
    logging.info("Calling FindAnswer Open AI")
    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    answer = ''

    try:
        topK = overrides.get("top") or 5
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        indexes = json.loads(json.dumps(overrides.get('indexes')))
        indexType = overrides.get('indexType')
        logging.info("Search for Top " + str(topK) + " and chainType is " + str(overrideChain))
        llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=temperature,
                openai_api_key=OpenAiKey,
                max_tokens=tokenLength,
                batch_size=10)

        logging.info("LLM Setup done")
        embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)

        tools = []
        for index in indexes:
            indexNs = index['indexNs']
            indexName = index['indexName']
            returnDirect = bool(index['returnDirect'])
            tool = addTool(indexType, embeddings, llm, overrideChain, indexNs, indexName, returnDirect)
            tools.append(tool)

        # vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        # logging.info("VectorDb Done")
        # index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever())
        # logging.info("RetrievalQA Done")
        # tools = [
        #     Tool(
        #         name = indexName,
        #         func=index.run,
        #         description=indexName
        #     ),
        # ]
        logging.info("Pinecone Setup done")
        agent = initialize_agent(tools, llm, agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
                    verbose=False, return_intermediate_steps=True, early_stopping_method="generate")
        answer = agent({"input":question})
        action = answer['intermediate_steps']
        sources = ''
        for a, data in action:
            sources = a.tool
            break;
        
        followupQaPromptTemplate = """Generate three very brief follow-up questions from the answer {answer} that the user would likely ask next.
        Use double angle brackets to reference the questions, e.g. <Is there a more details on that?>.
        Try not to repeat questions that have already been asked.
        Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'"""

        finalPrompt = followupQaPromptTemplate.format(answer = answer['output'])
        try:
            completion = openai.Completion.create(
                engine=OpenAiDavinci,
                prompt=finalPrompt,
                temperature=temperature,
                max_tokens=tokenLength,
                n=1)
            nextQuestions = completion.choices[0].text
        except Exception as e:
            logging.error(e)
            nextQuestions =  ''
    
        return {"data_points": [], "answer": answer['output'].replace("Answer: ", ''), "thoughts": answer['intermediate_steps'], "sources": sources, "nextQuestions":nextQuestions, "error": ""}

    except Exception as e:
        logging.info("Error in FindAnswer Open AI : " + str(e))
        return {"data_points": [], "answer": 'Exception Occured', "thoughts": '', "sources": '', "nextQuestions":'', "error": str(e)}

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

        answer = FindAnswer(question, overrides)
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

import logging, json, os, urllib
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI, OpenAI
import os
from langchain.sql_database import SQLDatabase
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import SQLDatabaseSequentialChain
from langchain.chains import LLMChain
from langchain.schema import AgentAction
from Utilities.envVars import *

def SqlChainAnswer(topK, question, embeddingModelType, value):
    logging.info("Calling SqlChainAnswer Open AI")
    answer = ''

    try:
        synapseConnectionString = "Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{};" \
                      "Database={};Uid={};Pwd={};Encrypt=yes;TrustServerCertificate=no;" \
                      "Connection Timeout=30;".format(SynapseName, SynapsePool, SynapseUser, SynapsePassword)
        params = urllib.parse.quote_plus(synapseConnectionString)
        sqlConnectionString = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
        db = SQLDatabase.from_uri(sqlConnectionString)

        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                    temperature=os.environ['Temperature'] or 0,
                    openai_api_key=OpenAiKey,
                    max_tokens=1000)

            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = OpenAI(temperature=os.environ['Temperature'] or 0,
                    openai_api_key=OpenAiApiKey)

        logging.info("LLM Setup done")


        defaultTemplate = """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
        Use the following format:

        Question: "Question here"
        SQLQuery: "SQL Query to run"
        SQLResult: "Result of the SQLQuery"
        Answer: "Final answer here"

        Only use the following tables:

        {table_info}
        
        Question: {input}

        """
        SqlPrompt = PromptTemplate(
            input_variables=["input", "table_info", "dialect"], template=defaultTemplate
        )

        # SqlDbChain = SQLDatabaseChain(llm=llm, database=db, prompt=SqlPrompt, verbose=True, return_intermediate_steps=True,
        #                               top_k=topK)
        SqlDbChain = SQLDatabaseSequentialChain.from_llm(llm, db, verbose=True, return_intermediate_steps=True, 
                                                         query_prompt=SqlPrompt, top_k=topK)
        answer = SqlDbChain(question)

        # followupPrompt = """
        # Given an input table definition, Generate three very brief follow-up questions that the user would likely ask next.
        # Use double angle brackets to reference the questions, e.g. <<Is there a more details on that?>>.
        # Try not to repeat questions that have already been asked.
        # Only generate questions and do not generate any text before or after the questions, such as 'Next Questions

        # QUESTION: {question}
        # =========

        # """
        # followupPrompt = PromptTemplate(
        #     input_variables=["question"], template=followupPrompt
        # )
        # qaChain = LLMChain(llm, prompt=followupPrompt)
        # followupAnswer = qaChain.predict(question)
        # logging.info(followupAnswer)

        intermediateSteps = answer['intermediate_steps']
        toolInput = ''
        observation = ''
        logging.info("Intermediate Steps : " + str(intermediateSteps))

        return {"data_points": [], "answer": answer['result'], "thoughts": intermediateSteps, 
                "toolInput": intermediateSteps[0], "observation": intermediateSteps[1], "error": ""}
    
        #return {"data_points": [], "answer": answer['result'], "thoughts": answer['intermediate_steps'], "error": ""}
    except Exception as e:
        logging.info("Error in SqlChainAnswer Open AI : " + str(e))
        return {"data_points": [], "answer": "Error in SqlChainAnswer Open AI : " + str(e), "thoughts": '', "error": str(e)}

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        topK = req.params.get('topK')
        question = req.params.get('question')
        embeddingModelType = req.params.get('embeddingModelType')
        logging.info("Input parameters : " + topK + " " + question)
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(topK, question, embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(topK, question, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(topK, question, embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(topK, question, embeddingModelType, record):
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

        answer = SqlChainAnswer(topK, question, embeddingModelType, value)
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

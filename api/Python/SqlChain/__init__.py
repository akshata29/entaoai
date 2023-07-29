import logging, json, os, urllib
import azure.functions as func
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import os
from langchain.sql_database import SQLDatabase
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import SQLDatabaseSequentialChain
from langchain.chains import LLMChain
from langchain.schema import AgentAction
from Utilities.envVars import *
from typing import Dict

def parseAnswer(result: Dict) -> Dict:
    sql_cmd_key = "sql_cmd"
    sql_result_key = "sql_result"
    table_info_key = "table_info"
    input_key = "input"
    final_answer_key = "answer"

    _example = {
        "input": result.get("query"),
    }

    steps = result.get("intermediate_steps")
    answer_key = sql_cmd_key # the first one
    for step in steps:
        # The steps are in pairs, a dict (input) followed by a string (output).
        # Unfortunately there is no schema but you can look at the input key of the
        # dict to see what the output is supposed to be
        if isinstance(step, dict):
            # Grab the table info from input dicts in the intermediate steps once
            if table_info_key not in _example:
                _example[table_info_key] = step.get(table_info_key)

            if input_key in step:
                if step[input_key].endswith("SQLQuery:"):
                    answer_key = sql_cmd_key # this is the SQL generation input
                if step[input_key].endswith("Answer:"):
                    answer_key = final_answer_key # this is the final answer input
            elif sql_cmd_key in step:
                _example[sql_cmd_key] = step[sql_cmd_key]
                answer_key = sql_result_key # this is SQL execution input
        elif isinstance(step, str):
            # The preceding element should have set the answer_key
            _example[answer_key] = step
    return _example

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

            llm = AzureChatOpenAI(
                        openai_api_base=openai.api_base,
                        openai_api_version=OpenAiVersion,
                        deployment_name=OpenAiChat,
                        temperature=0,
                        openai_api_key=OpenAiKey,
                        openai_api_type="azure",
                        max_tokens=1000)

            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = ChatOpenAI(temperature=0,
                openai_api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=1000)

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
        parsedResult = parseAnswer(answer)

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

        return {"data_points": [], "answer": parsedResult['answer'], "thoughts": intermediateSteps, 
                "toolInput": parsedResult['sql_cmd'], "observation": parsedResult['sql_result'], "error": ""}
    
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

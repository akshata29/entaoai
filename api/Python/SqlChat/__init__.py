import logging, json, os, urllib
import azure.functions as func
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
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

def SqlAgentAnswer(topK, question, embeddingModelType, value):
    logging.info("Calling SqlAgentAnswer Open AI")
    answer = ''
    os.environ['OPENAI_API_KEY'] = OpenAiKey

    try:
        synapseConnectionString = "Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{};" \
                      "Database={};Uid={};Pwd={};Encrypt=yes;TrustServerCertificate=no;" \
                      "Connection Timeout=30;".format(SynapseName, SynapsePool, SynapseUser, SynapsePassword)
        params = urllib.parse.quote_plus(synapseConnectionString)
        sqlConnectionString = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
        db = SQLDatabase.from_uri(sqlConnectionString)

        # SqlPrefix = """You are an agent designed to interact with SQL database systems.
        # Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
        # Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results using SELECT TOP in SQL Server syntax.
        # You can order the results by a relevant column to return the most interesting examples in the database.
        # Never query for all the columns from a specific table, only ask for a the few relevant columns given the question.
        # You have access to tools for interacting with the database.
        # Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        # You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        
        # DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        
        # If the question does not seem related to the database, just return "I don't know" as the answer.        
        # """ 

        SqlPrefix = """You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
        Always limit your query to at most {top_k} results using the SELECT TOP in SQL Server syntax.
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for a the few relevant columns given the question.
        If you get a "no such table" error, rewrite your query by using the table in quotes.
        DO NOT use a column name that does not exist in the table.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        You MUST double check your query before executing it. If you get an error while executing a query, rewrite a different query and try again.
        Observations from the database should be in the form of a JSON with following keys: "column_name", "column_value"
        DO NOT try to execute the query more than three times.
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        If the question does not seem related to the database, just return "I don't know" as the answer.
        If you cannot find a way to answer the question, just return the best answer you can find after trying at least three times."""

        SqlSuffix = """Begin!
            Question: {input}
            Thought: I should look at the tables in the database to see what I can query.
            {agent_scratchpad}"""
        
        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"{OpenAiEndPoint}"

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

        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        logging.info("Toolkit Setup done")


        agentExecutor = create_sql_agent(
                llm=llm,
                toolkit=toolkit,
                verbose=True,
                prefix=SqlPrefix, 
                #suffix=SqlSuffix,
                top_k=topK,
                kwargs={"return_intermediate_steps": True}
            )
        agentExecutor.return_intermediate_steps = True
     
        logging.info("Agent Setup done")
        answer = agentExecutor._call({"input":question})
        parsedResult = parseAnswer(answer)
        intermediateSteps = answer['intermediate_steps']
        toolInput = ''
        observation = ''
        for item in intermediateSteps:
            agentAction: AgentAction = item[0]
            if (agentAction.tool == 'query_sql_db'):
                toolInput = str(agentAction.tool_input)
                observation = item[1]

        return {"data_points": [], "answer": answer['output'], "thoughts": intermediateSteps, 
                "toolInput": toolInput, "observation": observation, "error": ""}
    except Exception as e:
        logging.info("Error in SqlAgentAnswer Open AI : " + str(e))
        return {"data_points": [], "answer": "Error in SqlAgentAnswer Open AI : " + str(e), "thoughts": '', "error": str(e)}

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

        answer = SqlAgentAnswer(topK, question, embeddingModelType, value)
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

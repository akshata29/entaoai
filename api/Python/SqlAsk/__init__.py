import logging, json, os, urllib
import azure.functions as func
import openai
import os
from Utilities.envVars import *
from typing import Dict
import pyodbc
import pandas as pd
from sqlalchemy import create_engine


def connectSqlServer(database):
    '''
    Setup SQL Server
    '''
    server = SynapseName
    username = SynapseUser
    password = SynapsePassword
    connection = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    
    return connection

def executeQuery(query, sqlConnectionString, limit=10000):  
    engine = create_engine(sqlConnectionString)
    result = pd.read_sql_query(query, engine)
    result = result.infer_objects()
    for col in result.columns:  
        if 'date' in col.lower():  
            result[col] = pd.to_datetime(result[col], errors="ignore")  

    if limit is not None:  
        result = result.head(limit)  # limit to save memory  
    # session.close()  
    return result

def runSqlQuery(completion):
    '''
    Function to run the generated SQL Query on SQL server and retrieve output.
    Input: AOAI completion (SQL Query)
    Output: Pandas dataframe containing results of the query run
    
    '''
    connection = connectSqlServer(SynapsePool)
    df = pd.read_sql(completion, connection)
    return df

def getTableSchema(sqlConnectionString):
    sqlQuery = """  
    SELECT C.TABLE_NAME, C.COLUMN_NAME, C.DATA_TYPE, T.TABLE_TYPE, T.TABLE_SCHEMA  
    FROM INFORMATION_SCHEMA.COLUMNS C  
    JOIN INFORMATION_SCHEMA.TABLES T ON C.TABLE_NAME = T.TABLE_NAME AND C.TABLE_SCHEMA = T.TABLE_SCHEMA  
    WHERE T.TABLE_TYPE = 'BASE TABLE'  
    """  
    
    # Execute the SQL query and store the results in a DataFrame  
    df = executeQuery(sqlQuery, sqlConnectionString, limit=None)  
    #df = runSqlQuery(sqlQuery)
    output=[]
    # Initialize variables to store table and column information  
    curTable = ''  
    columns = []  
    
    # Loop through the query results and output the table and column information  
    for index, row in df.iterrows():
        tableName = f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}" 
        colName = row['COLUMN_NAME']  
        dataType = row['DATA_TYPE']   
        if " " in tableName:
            tableName= f"[{tableName}]" 
        colName = row['COLUMN_NAME']  
        if " " in colName:
            colName= f"[{colName}]" 

        # If the table name has changed, output the previous table's information  
        if curTable != tableName and curTable != '':  
            output.append(f"table: {curTable}, columns: {', '.join(columns)}")
            columns = []  
        
        # Add the current column information to the list of columns for the current table  
        columns.append(f"{colName} {dataType}")  
        
        # Update the current table name  
        curTable = tableName  
    
    # Output the last table's information  
    output.append(f"table: {curTable}, columns: {', '.join(columns)}")
    output = "\n ".join(output)
    return output

def generateNlToSql(prompt, tableSchema, history = []):
    '''
    This GPT4 engine is setup for NLtoSQL tasks on the Sales DB.
    Input: NL question related to sales
    Output: SQL query to run on the sales database
    '''

    sysPrompt = f""" You are a SQL programmer Assistant.Your role is to generate SQL code (SQL Server) to retrieve an answer to a natural language query. Make sure to disambiguate column names when creating queries that use more than one table. If a valid SQL query cannot be generated, only say "ERROR:" followed by why it cannot be generated.
                  Do not answer any questions on inserting or deleting rows from the table. Instead, say "ERROR: I am not authorized to make changes to the data"

                  Use the following sales database schema to write SQL queries:
                  {tableSchema}

                  Examples:
                  User: Which Shipper can ship the product?. SQL Code:
                  Assistant: SELECT s.ShipperID, s.CompanyName FROM Shippers s JOIN Orders o ON s.ShipperID = o.ShipVia JOIN OrderDetails od ON o.OrderID = od.OrderID JOIN Products p ON od.ProductID = p.ProductID;
                  User: Number of units in stock by category and supplier continent? SQL Code:
                  Assistant: SELECT c.CategoryName, s.Country AS SupplierContinent, SUM(p.UnitsInStock) AS TotalUnitsInStock FROM Products p JOIN Categories c ON p.CategoryID = c.CategoryID JOIN Suppliers s ON p.SupplierID = s.SupplierID GROUP BY c.CategoryName, s.Country ORDER BY c.CategoryName, s.Country;
                  User: List Top 10 Products?. SQL Code:
                  Assistant: SELECT TOP 10 Products from Products;
            """
    messages=[
            {"role": "system", "content": sysPrompt}
        ]

    messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    
    response = openai.ChatCompletion.create(
        engine=OpenAiChat16k, # The deployment name you chose when you deployed the ChatGPT or GPT-4 model.
        messages=messages,
        temperature=0,
        max_tokens=2000,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response['choices'][0]['message']['content']

def generateSqlToNl(prompt_in):
    '''
    This GPT4 engine is setup for SQLtoNL tasks on the Sales DB.
    Input: Original question asked. Answer retreived from running SQL query.
    Output: Natural language sentence(s).
    '''
    
    response = openai.ChatCompletion.create(
        engine=OpenAiChat16k, # The deployment name you chose when you deployed the ChatGPT or GPT-4 model.
        messages=[
            {"role": "system", "content": """You are bot that takes question-answer pairs and converts the answer to natural language. For tabular information return it as an html table. Do not return markdown format."""},
            {"role": "user", "content": prompt_in},
        ],
        temperature=0,
        max_tokens=2000,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    return response['choices'][0]['message']['content']

def SqlAskAnswer(topK, question, embeddingModelType, value):
    logging.info("Calling SqlAsk Open AI")
    answer = ''

    try:
        synapseConnectionString = "Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{};" \
                      "Database={};Uid={};Pwd={};Encrypt=yes;TrustServerCertificate=no;" \
                      "Connection Timeout=30;".format(SynapseName, SynapsePool, SynapseUser, SynapsePassword)
        params = urllib.parse.quote_plus(synapseConnectionString)
        sqlConnectionString = 'mssql+pyodbc:///?odbc_connect={}'.format(params)

        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"{OpenAiEndPoint}"
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey

        logging.info("LLM Setup done")

        # STEP 1: Generate an SQL query using the chat history
        tableSchema = getTableSchema(sqlConnectionString)
        sqlQuery = generateNlToSql(question, tableSchema)
        logging.info("SQL Query generated: " + sqlQuery)

        # STEP 2: Run generated SQL query against the database
        #sqlResult = runSqlQuery(sqlQuery)
        sqlResult = executeQuery(sqlQuery, sqlConnectionString, limit=None)  

         # STEP 3: Format the SQL query and SQL result into a natural language response
        formattedAnswer = generateSqlToNl(str(question +  str(sqlResult.to_dict('list'))))

        # STEP 4: Return the answer
        answer = {"data_points": [], "answer": formattedAnswer, "thoughts": tableSchema, 
                "toolInput": sqlQuery, "observation": str(sqlResult.to_dict('list')), "error": ""}

        return answer
    except Exception as e:
        logging.info("Error in SqlAskAnswer Open AI : " + str(e))
        return {"data_points": [], "answer": "Error in SqlAskAnswer Open AI : " + str(e), "thoughts": '', "error": str(e)}

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
        logging.info("Input parameters : " + str(topK) + " " + question)
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

        answer = SqlAskAnswer(topK, question, embeddingModelType, value)
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

import logging, json, os, urllib
import azure.functions as func
import openai
import os
from langchain.sql_database import SQLDatabase
from langchain.prompts.prompt import PromptTemplate
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chains import LLMChain
from langchain.schema import AgentAction
from Utilities.envVars import *
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import pandas as pd
from typing import List
from sqlalchemy import create_engine  
import time
import re
import sys
from io import StringIO

def executeSqlQuery(query, limit=10000):  
    synapseConnectionString = "Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{};" \
                    "Database={};Uid={};Pwd={};Encrypt=yes;TrustServerCertificate=no;" \
                    "Connection Timeout=30;".format(SynapseName, SynapsePool, SynapseUser, SynapsePassword)
    params = urllib.parse.quote_plus(synapseConnectionString)
    engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)

    result = pd.read_sql_query(query, engine)
    result = result.infer_objects()
    for col in result.columns:  
        if 'date' in col.lower():  
            result[col] = pd.to_datetime(result[col], errors="ignore")  

    if limit is not None:  
        result = result.head(limit)  # limit to save memory  

    # session.close()  
    return result  

def getTableSchema(tableNames:List[str]):

    # Create a comma-separated string of table names for the IN operator  
    tableNamesStr = ','.join(f"'{name}'" for name in tableNames)  
    # print("tableNamesStr: ", tableNamesStr)
    
    # Define the SQL query to retrieve table and column information 
    sqlQuery = f"""  
    SELECT C.TABLE_NAME, C.COLUMN_NAME, C.DATA_TYPE, T.TABLE_TYPE, T.TABLE_SCHEMA  
    FROM INFORMATION_SCHEMA.COLUMNS C  
    JOIN INFORMATION_SCHEMA.TABLES T ON C.TABLE_NAME = T.TABLE_NAME AND C.TABLE_SCHEMA = T.TABLE_SCHEMA  
    WHERE T.TABLE_TYPE = 'BASE TABLE'  AND C.TABLE_NAME IN ({tableNamesStr})  
    """  
    # Execute the SQL query and store the results in a DataFrame  
    df = executeSqlQuery(sqlQuery, limit=None)  
    output=[]
    # Initialize variables to store table and column information  
    currentTable = ''  
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
        if currentTable != tableName and currentTable != '':  
            output.append(f"table: {currentTable}, columns: {', '.join(columns)}")  
            columns = []  
        
        # Add the current column information to the list of columns for the current table  
        columns.append(f"{colName} {dataType}")  
        
        # Update the current table name  
        currentTable = tableName  
    
    # Output the last table's information  
    output.append(f"table: {currentTable}, columns: {', '.join(columns)}")
    output = "\n ".join(output)

    logging.info("List of all tables and columns: %s", output)
    return output

def getTableNames():
    # Define the SQL query to retrieve table and column information 
    sqlQuery = """  
    SELECT DISTINCT C.TABLE_NAME  
    FROM INFORMATION_SCHEMA.COLUMNS C  
    JOIN INFORMATION_SCHEMA.TABLES T ON C.TABLE_NAME = T.TABLE_NAME AND C.TABLE_SCHEMA = T.TABLE_SCHEMA  
    WHERE T.TABLE_TYPE = 'BASE TABLE' 
    """  

    df = executeSqlQuery(sqlQuery, limit=None)  
    
    output=[]
    
    # Loop through the query results and output the table and column information  
    for index, row in df.iterrows():
        tableName = f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}"  
        if " " in tableName:
            tableName= f"[{tableName}]" 
        output.append(tableName)  
    
    logging.info("List of all tables: %s", output)
    return output

def extractCodeAndComment(input, pythonCodes):
    # print("entire_input: \n", entire_input)
    remainingInput = input
    comments=[]
    for pythonCode in pythonCodes:
        tempPythonCode = "```python\n"+pythonCode+"```"
        textBefore = remainingInput.split(tempPythonCode)[0]
        comments.append(textBefore)
        remainingInput = remainingInput.split(tempPythonCode)[1]
    return comments, remainingInput

def extractOutput(input, extractPattern):
    # print("text_input\n",text_input)
    outputs=[]
    for pattern in extractPattern: 
        if "python" in pattern[1]:
            pythonCodes = re.findall(pattern[1], input, re.DOTALL)
            comments, textAfter= extractCodeAndComment(input, pythonCodes)
            for comment, code in zip(comments, pythonCodes):
                outputs.append({"python":code, "comment":comment})
            outputs.append({"text_after":textAfter})
        elif "request_to_data_engineer" in pattern[1]:
            request = re.findall(pattern[1], input, re.DOTALL)
            if len(request)>0:
                outputs.append({"request_to_data_engineer":request[0]})

def validateOutput(llmOutput,extractedOutput):
    valid = False
    if "Final Answer:" in llmOutput:
        return True
    for output in extractedOutput:
        if len(output.get("python",""))!=0 or len(output.get("request_to_data_engineer",""))!=0:
            return True
    if (llmOutput == "OPENAI_ERROR"):
        valid = True
    return valid

def callLlm(embeddingModelType, prompt, stop):        
    try:
        if (embeddingModelType == 'azureopenai'):
            baseUrl = f"{OpenAiEndPoint}"
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"{OpenAiEndPoint}"

            completion = openai.ChatCompletion.create(
                engine=OpenAiChat,
                prompt=prompt,
                temperature=0,
                max_tokens=1250,
                stop=stop)
            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            completion = openai.ChatCompletion.create(
                engine="gpt-3.5-turbo",
                prompt=prompt,
                temperature=0,
                max_tokens=1250,
                stop=stop)
        llmOutput = completion['choices'][0]['message']['content']
    except Exception as e:
        logging.error("Error in calling LLM: %s", e)
        llmOutput=""

    return llmOutput

def getNextSteps(userQuestion, convHistory, assistantResponse, stop, extractPatterns, embeddingModelType):
        if len(convHistory)>2:
            convHistory.pop() #removing old history

        if len(userQuestion)>0:
            convHistory.append({"role": "user", "content": userQuestion})
        if len(assistantResponse)>0:
            convHistory.append({"role": "assistant", "content": assistantResponse})
        n=0
        logging.info("ConvHistory: %s", convHistory)
        try:
            llmOutput = callLlm(embeddingModelType, convHistory, stop)
        except Exception as e:
            if "maximum context length" in str(e):
                print(f"Context length exceeded")
                return "OPENAI_ERROR",""  
            # time.sleep(8) #sleep for 8 seconds
            # while n<5:
            #     try:
            #         llmOutput = callLlm(embeddingModelType, convHistory, stop)
            #     except Exception as e:
            #         n +=1

            #         print(f"error calling open AI, I am retrying 5 attempts , attempt {n}")
            #         time.sleep(8) #sleep for 8 seconds
            #         print(str(e))

            llmOutput = "OPENAI_ERROR"     
             
    
        outputs = extractOutput(llmOutput, extractPatterns)
        if len(llmOutput)==0:
            return "",[]
        if not validateOutput(llmOutput, outputs): #wrong output format
            llmOutput = "WRONG_OUTPUT_FORMAT"
        return llmOutput,outputs

def SqlVisualAnswer(topK, question, embeddingModelType, value):
    logging.info("Calling SqlVisualAnswer Open AI")
    answer = ''

    try:

        sysMessage="""
            You are data scientist to help answer business questions by writing python code to analyze and draw business insights.
            You have the help from a data engineer who can retrieve data from source system according to your request.
            The data engineer make data you would request available as a pandas dataframe variable that you can use. 
            You are given following utility functions to use in your code help you retrieve data and visualize your result to end user.
                1. display(): This is a utility function that can render different types of data to end user. 
                    - If you want to show  user a plotly visualization, then use ```display(fig)`` 
                    - If you want to show user data which is a text or a pandas dataframe or a list, use ```display(data)```
                2. print(): use print() if you need to observe data for yourself. 
            Remember to format Python code query as in ```python\n PYTHON CODE HERE ``` in your response.
            Only use display() to visualize or print result to user. Only use plotly for visualization.
            Please follow the <<Template>> below:
            """

        fewShotExample="""
            <<Template>>
            Question: User Question
            Thought: First, I need to accquire the data needed for my analysis
            Action: 
            ```request_to_data_engineer
            Prepare a dataset with customers, categories and quantity, for example
            ```
            Observation: Name of the dataset and description 
            Thought: Now I can start my work to analyze data 
            Action:  
            ```python
            import pandas as pd
            import numpy as np
            #load data provided by data engineer
            step1_df = load("name_of_dataset")
            # Fill missing data
            step1_df['Some_Column'] = step1_df['Some_Column'].replace(np.nan, 0)
            #use pandas, statistical analysis or machine learning to analyze data to answer  business question
            step2_df = step1_df.apply(some_transformation)
            print(step2_df.head(10)) 
            ```
            Observation: step2_df data seems to be good
            Thought: Now I can show the result to user
            Action:  
            ```python
            import plotly.express as px 
            fig=px.line(step2_df)
            #visualize fig object to user.  
            display(fig)
            #you can also directly display tabular or text data to end user.
            display(step2_df)
            ```
            ... (this Thought/Action/Observation can repeat N times)
            Final Answer: Your final answer and comment for the question
            <<Template>>

            """

        extractPatterns=[('request_to_data_engineer',r"```request_to_data_engineer\n(.*?)```"),('python',r"```python\n(.*?)```")]

        formattedSysMessage = f"""
        {sysMessage}
        {fewShotExample}
        """

        convHistory =  [{"role": "system", "content": formattedSysMessage}]

        maxSteps = 15
        count =1

        userQuestion= f"Question: {question}"
        newInput=""
        errorMsg=""
        finalOutput = ""
        while count<= maxSteps:
            llmOutput,nextSteps = getNextSteps(userQuestion, convHistory, newInput, 
                                                 ["Observation:"], extractPatterns, embeddingModelType )
            
            userQuestion=""
            if llmOutput=='OPENAI_ERROR':
                logging.info("Error Calling Azure Open AI, probably due to service limit, please start over")
                break
            elif llmOutput=='WRONG_OUTPUT_FORMAT': #just have open AI try again till the right output comes
                count +=1
                continue
            newInput= "" #forget old history
            runOk =True
            if len(nextSteps)>0:
                request = nextSteps[0].get("request_to_data_engineer", "")
                if len(request)>0:
                    dataOutput =data_preparer.run(request,show_code,show_prompt,st)
                    if dataOutput is not None: #Data is returned from data engineer
                        newInput = "Observation: this is the output from data engineer\n"+dataOutput
                        continue
                    else:
                        logging.info("I am sorry, we cannot accquire data from source system, please try again")
                        break

            for output in nextSteps:
                comment= output.get("comment","")
                newInput += comment
                pythonCode = output.get("python","")
                newInput += pythonCode
                if len(pythonCode)>0:
                    oldStdOut = sys.stdout
                    sys.stdout = myStdOut = StringIO()

                    try:
                        exec(pythonCode, locals())
                        sys.stdout = oldStdOut
                        std_out = str(myStdOut.getvalue())
                        if len(std_out)>0:
                            newInput +="\nObservation:\n"+ std_out 
                            # print(new_input)                  
                    except Exception as e:
                        newInput +="\nObservation: Encounter following error:"+str(e)+"\nIf the error is about python bug, fix the python bug, if it's about SQL query, double check that you use the corect tables and columns name and query syntax, can you re-write the code?"
                        sys.stdout = oldStdOut
                        runOk = False
                        errorMsg= str(e)
            if not runOk:
                logging.info(f"encountering error: {errorMsg}, \nI will now retry")

            count +=1
            if "Final Answer:" in llmOutput:
                finalOutput= output.get("comment","")+output.get("text_after","")+output.get("text_after","")
            if count>= maxSteps:
                logging.info("I am sorry, I cannot handle the question, please change the question and try again")

        return {"data_points": [], "answer": finalOutput, "thoughts": '', 
                "toolInput": '', "observation": '', "error": ""}
    
        #return {"data_points": [], "answer": answer['result'], "thoughts": answer['intermediate_steps'], "error": ""}
    except Exception as e:
        logging.info("Error in SqlVisualAnswer Open AI : " + str(e))
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

        answer = SqlVisualAnswer(topK, question, embeddingModelType, value)
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

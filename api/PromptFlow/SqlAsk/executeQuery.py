from promptflow import tool
from promptflow.connections import CustomConnection
import openai
import pandas as pd
from sqlalchemy import create_engine
import logging, json, os, urllib

def executeSqlQuery(query, sqlConnectionString, limit=10000): 
    try: 
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
    except Exception as e:
        return "Exception Occurred : " + str(e)

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def executeQuery(sqlQuery: str, conn:CustomConnection):
    synapseConnectionString = "Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{};" \
                      "Database={};Uid={};Pwd={};Encrypt=yes;TrustServerCertificate=no;" \
                      "Connection Timeout=30;".format(conn.SynapseName, conn.SynapsePool, conn.SynapseUser, conn.SynapsePassword)
    params = urllib.parse.quote_plus(synapseConnectionString)
    sqlConnectionString = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
    sqlResult = executeSqlQuery(sqlQuery, sqlConnectionString, limit=None)

    return sqlResult

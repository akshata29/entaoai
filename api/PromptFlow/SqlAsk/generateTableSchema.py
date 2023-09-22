from promptflow import tool
import logging, json, os, urllib
from sqlalchemy import create_engine
import pandas as pd
from promptflow.connections import CustomConnection

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

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def generateTableSchema(conn:CustomConnection):

  synapseConnectionString = "Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{};" \
                      "Database={};Uid={};Pwd={};Encrypt=yes;TrustServerCertificate=no;" \
                      "Connection Timeout=30;".format(conn.SynapseName, conn.SynapsePool, conn.SynapseUser, conn.SynapsePassword)
  params = urllib.parse.quote_plus(synapseConnectionString)
  sqlConnectionString = 'mssql+pyodbc:///?odbc_connect={}'.format(params)
  tableSchema = getTableSchema(sqlConnectionString)

  return tableSchema
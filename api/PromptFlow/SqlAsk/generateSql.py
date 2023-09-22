from promptflow import tool
from promptflow.connections import CustomConnection
import openai

def generateNlToSql(prompt, conn, tableSchema, history = []):
    '''
    This GPT4 engine is setup for NLtoSQL tasks on the Sales DB.
    Input: NL question related to sales
    Output: SQL query to run on the sales database
    '''
    
    openai.api_type = "azure"
    openai.api_key = conn.OpenAiKey
    openai.api_version = conn.OpenAiVersion
    openai.api_base = conn.OpenAiEndPoint

    sysPrompt = f""" You are a SQL Server programmer Assistant.Your role is to generate SQL code (SQL Server) to retrieve an answer to a natural language query. Make sure to disambiguate column names when creating queries that use more than one table. If a valid SQL query cannot be generated, only say "ERROR:" followed by why it cannot be generated.
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
        engine=conn.OpenAiChat16k, # The deployment name you chose when you deployed the ChatGPT or GPT-4 model.
        messages=messages,
        temperature=0,
        max_tokens=2000,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response['choices'][0]['message']['content']

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def generateSql(question: str, conn:CustomConnection, tableSchema: str):
    sqlQuery = generateNlToSql(question, conn, tableSchema)

    return sqlQuery

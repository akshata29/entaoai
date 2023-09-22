from promptflow import tool
from promptflow.connections import CustomConnection
import openai

def generateSqlToNl(sqlPrompt, conn):
    '''
    This GPT4 engine is setup for SQLtoNL tasks on the Sales DB.
    Input: Original question asked. Answer retreived from running SQL query.
    Output: Natural language sentence(s).
    '''
    
    openai.api_type = "azure"
    openai.api_key = conn.OpenAiKey
    openai.api_version = conn.OpenAiVersion
    openai.api_base = conn.OpenAiEndPoint
    
    response = openai.ChatCompletion.create(
        engine=conn.OpenAiChat16k, # The deployment name you chose when you deployed the ChatGPT or GPT-4 model.
        messages=[
            {"role": "system", "content": """You are bot that takes question-answer pairs and converts the answer to natural language. For tabular information return it as an html table. Do not return markdown format."""},
            {"role": "user", "content": sqlPrompt},
        ],
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
def generateNlp(question: str, conn:CustomConnection, sqlResult: object):
    if type(sqlResult) is str:
        if (str(sqlResult).find("Exception Occurred") >= 0):
            return str(sqlResult)
    else:
        formattedAnswer = generateSqlToNl(str(question +  str(sqlResult.to_dict('list'))), conn)
        return formattedAnswer

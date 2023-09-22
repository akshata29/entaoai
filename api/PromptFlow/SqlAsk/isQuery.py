from promptflow import tool
from promptflow.connections import CustomConnection
import openai

def verifyIfValid(question, tableSchema, conn):
    openai.api_type = "azure"
    openai.api_key = conn.OpenAiKey
    openai.api_version = conn.OpenAiVersion
    openai.api_base = conn.OpenAiEndPoint

    sysMessage = """
      If the requested OBJECTIVE can be answered by querying a database with tables described in SCHEMA, ANSWER: YES.
      Otherwise ANSWER: NO.

      Do not answer with any other word than YES or NO.

      SCHEMA:
      {tableSchema}

      OBJECTIVE: {question}

      ANSWER: Let's think step by step and respond with ONLY YES or NO.
    """

    sysMessage = sysMessage.format(question=question, tableSchema=tableSchema)

    response = openai.ChatCompletion.create(
        engine=conn.OpenAiChat16k, # The deployment name you chose when you deployed the ChatGPT or GPT-4 model.
        messages=[
            {"role": "system", "content": sysMessage},
        ],
        temperature=0,
        max_tokens=1000,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response['choices'][0]['message']['content']

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def IsQuery(question: str, tableSchema: str, conn:CustomConnection):
    validQuery = verifyIfValid(question, tableSchema, conn)
    if validQuery == "YES":
        return {
            "jsonAnswer": None,
            "validQuestion": True
        }
    else:
        return {
            "jsonAnswer": None,
            "validQuestion": False
        }

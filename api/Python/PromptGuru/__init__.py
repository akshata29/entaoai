import logging, json, os
import azure.functions as func
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from Utilities.envVars import *

def PromptGuruAnswer(task, embeddingModelType, value):
    logging.info("Calling PromptGuruAnswer Open AI")
    answer = ''
    
    try:

        promptPrompt = """
                Your task is to help users develop effective prompts for interacting with ChatGPT. 
                Remember to use the following techniques:

                -   Start with clear instructions
                -   Use few-shot learning
                -   Repeat instructions at the end
                -   Prime the output
                -   Add clear syntax
                -   Break the task down
                -   Use affordances
                -   Chain of thought prompting
                -   Specify the output structure

                Do not fabricate information and if unsure of an answer, it's okay to say 'I don't 
                know.' Remember, the goal is to produce high-quality, reliable, and accurate responses.

                Following is the example of good prompt for the task of English Translator and Improver:
                User: Act as an English Translator and Improver

                Assistant:  I want you to act as an English translator, spelling corrector and improver. 
                I will speak to you in any language and you will detect the language, translate it and answer in the corrected 
                and improved version of my text, in English. I want you to replace my simplified A0-level words 
                and sentences with more beautiful and elegant, upper level English words and sentences. 
                Keep the meaning same, but make them more literary. I want you to only reply the correction, 
                the improvements and nothing else, do not write explanations.

                User: {userTask}

                Assistant:

                """
        
        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureChatOpenAI(
                    openai_api_base=openai.api_base,
                    openai_api_version="2023-03-15-preview",
                    deployment_name=OpenAiChat,
                    temperature=0,
                    openai_api_key=OpenAiKey,
                    openai_api_type="azure",
                    max_tokens=400)

            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = ChatOpenAI(temperature=0,
                openai_api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=400)

        promptPromptTemplate = PromptTemplate(template=promptPrompt, input_variables=["userTask"])
        chain = LLMChain(llm=llm, prompt=promptPromptTemplate)
        answer = chain.run({ 'userTask': task})
        return {"data_points": '', "answer": answer, 
                        "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
    

    except Exception as e:
      logging.info("Error in PromptGuruAnswer Open AI : " + str(e))
      return {"data_points": "", "answer": "Exception during finding answers - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}

    #return answer

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

        try:
            task = req.params.get('task')
            embeddingModelType = req.params.get('embeddingModelType')
            body = json.dumps(req.get_json())
        except ValueError:
            return func.HttpResponse(
                "Invalid body",
                status_code=400
            )

        result = ComposeResponse(task, embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(task, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(task, embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(task, embeddingModelType, record):
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

        answer = PromptGuruAnswer(task, embeddingModelType, value)
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

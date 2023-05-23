import logging, json, os
import azure.functions as func
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from Utilities.envVars import *

def ConvertCodeAnswer(inputLanguage, outputLanguage, modelName, embeddingModelType, inputCode):
    logging.info("Calling ConvertCodeAnswer Open AI")
    answer = ''
    
    try:
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
                    max_tokens=2000)

            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = ChatOpenAI(temperature=0,
                openai_api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=2000)

        codePrompt = ''
        if (inputLanguage == 'Natural Language'):
            codePrompt = """
                You are an expert programmer in all programming languages. Translate the natural language to "{outputLanguage}" code. Do not include \`\`\`.

                Example translating from natural language to Python:

                Natural language:
                Print the numbers 0 to 9.

                Python code:
                for i in range(1, 11):
                    print(i)

                Natural language:
                {inputCode}

                {outputLanguage} code (no \`\`\`):
                """
            codePromptTemplate = PromptTemplate(template=codePrompt, input_variables=["outputLanguage", "inputCode"])
            chain = LLMChain(llm=llm, prompt=codePromptTemplate)
            answer = chain.run({ 'inputCode': inputCode, "outputLanguage": outputLanguage})

        elif (outputLanguage == 'Natural Language'):
            codePrompt = """
                You are an expert programmer in all programming languages. Translate the "{inputLanguage}" code to natural language in plain English that the average adult could understand. Respond as bullet points starting with -.
            
                Example translating from JavaScript to natural language:
            
                Python code:
                for i in range(1, 11):
                    print(i)
            
                Natural language:
                Print the numbers 0 to 9.
                
                {inputLanguage} code:
                {inputCode}

                Natural language:
                """
            codePromptTemplate = PromptTemplate(template=codePrompt, input_variables=["inputLanguage", "inputCode"])
            chain = LLMChain(llm=llm, prompt=codePromptTemplate)
            answer = chain.run({ 'inputLanguage': inputLanguage, 'inputCode': inputCode})

        else:
            # codePrompt = """
            #     You are an expert programmer in all programming languages. Translate the "{inputLanguage}" code to "{outputLanguage}" code. Do not include \`\`\`.
  
            #     Example translating from JavaScript to Python:
  
            #     JavaScript code:
            #     for (let i = 0; i < 10; i++) {
            #         console.log(i);
            #     }
            
            #     Python code:
            #     for i in range(10):
            #         print(i)  
                
            #     {inputLanguage} code:
            #     {inputCode}

            #     {outputLanguage} code (no \`\`\`):
            #     """
            codePrompt = """
                ##### You are an expert programmer in all programming languages. Translate the code from "{inputLanguage}" into "{outputLanguage}"
                ### {inputLanguage}

                {inputCode}

                ### {outputLanguage}
                """
            codePromptTemplate = PromptTemplate(template=codePrompt, input_variables=["inputLanguage", "outputLanguage", "inputCode"])
            chain = LLMChain(llm=llm, prompt=codePromptTemplate)
            answer = chain.run({ 'inputLanguage': inputLanguage, 'inputCode': inputCode, "outputLanguage": outputLanguage})
        return {"data_points": '', "answer": answer, 
                        "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
    

    except Exception as e:
      logging.info("Error in ConvertCodeAnswer Open AI : " + str(e))
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
            inputLanguage = req.params.get('inputLanguage')
            outputLanguage = req.params.get('outputLanguage')
            modelName = req.params.get('modelName')
            embeddingModelType = req.params.get('embeddingModelType')
            body = json.dumps(req.get_json())
        except ValueError:
            return func.HttpResponse(
                "Invalid body",
                status_code=400
            )

        result = ComposeResponse(inputLanguage, outputLanguage, modelName, embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(inputLanguage, outputLanguage, modelName, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(inputLanguage, outputLanguage, modelName, embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(inputLanguage, outputLanguage, modelName, embeddingModelType, record):
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

        answer = ConvertCodeAnswer(inputLanguage, outputLanguage, modelName, embeddingModelType, value)
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

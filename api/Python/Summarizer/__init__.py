import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI, OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import uuid
from langchain.document_loaders import UnstructuredFileLoader
from Utilities.envVars import *

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        promptName = req.params.get('promptName')
        promptType = req.params.get('promptType')
        chainType = req.params.get('chainType')
        docType = req.params.get('docType')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(promptType, promptName, chainType, docType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def Summarize(promptType, promptName, chainType, docType, inLineText, overrides):
    logging.info("Calling Summarize Open AI")
    temperature = overrides.get("temperature") or 0.3
    tokenLength = overrides.get('tokenLength') or 500
    embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'

    summaryResponse = ''

    if (embeddingModelType == 'azureopenai'):
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"

        llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                temperature=temperature,
                max_tokens=tokenLength,
                openai_api_key=OpenAiKey)

        completion = openai.Completion.create(
                engine= OpenAiDavinci,
                prompt = inLineText,
                temperature = temperature,
                max_tokens = tokenLength,
        )
        logging.info("LLM Setup done")
    elif embeddingModelType == "openai":
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07' 
        openai.api_key = OpenAiApiKey
        
        llm = OpenAI(temperature=temperature,
                openai_api_key=OpenAiApiKey)
        
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=inLineText,
            temperature=temperature,
            max_tokens=tokenLength)
            
    if (promptType == "custom"):
        try:
            logging.info(inLineText)
        except Exception as e:
            logging.info("Exception : " + str(e))
        summaryResponse = completion.choices[0].text
        return summaryResponse
    else:
        pTemplate = os.environ[promptName]
        logging.info("Prompt Template : " + pTemplate)
        InputVariables = os.environ[promptName + "Iv"]
        if (docType == "inline"):
            logging.info("Llm created")
            uResult = uuid.uuid4()
            logging.info(uResult.hex)
            downloadPath = os.path.join(tempfile.gettempdir(), uResult.hex + ".txt")
            os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
            try:
                with open(downloadPath, "wb") as file:
                    file.write(bytes(inLineText, 'utf-8'))
            except Exception as e:
                logging.error(e)

            logging.info("File created")
            textSplitter = RecursiveCharacterTextSplitter(chunk_size=3500, chunk_overlap=0)
            loader = UnstructuredFileLoader(downloadPath)
            rawDocs = loader.load()
            docs = textSplitter.split_documents(rawDocs)
            # We need to use refine or map reduce only if we have a need for chunking
            if (len(docs) <= 1):
                chainType = 'stuff'

            logging.info(len(docs))
            logging.info("Chain Type : " + chainType)
            try:
                if chainType == "map_reduce":
                    Prompt = PromptTemplate(template=pTemplate, input_variables=[InputVariables])
                    chain = load_summarize_chain(llm, chain_type=chainType, map_prompt=Prompt, combine_prompt=Prompt)
                elif chainType == "refine":
                    qaPromptTemplate = """Write a concise summary of the following:

                    {text}


                    CONCISE SUMMARY:"""
                    qaPrompt = PromptTemplate(template=qaPromptTemplate, input_variables=["text"])
                    refineTemplate = (
                        "Your job is to produce a final summary\n"
                        "We have provided an existing summary up to a certain point: {existing_answer}\n"
                        "We have the opportunity to refine the existing summary"
                        "(only if needed) with some more context below.\n"
                        "------------\n"
                        "{text}\n"
                        "------------\n"
                        "Given the new context, refine the original summary"
                        "If the context isn't useful, return the original summary."
                    )
                    refinePrompt = PromptTemplate(
                        input_variables=["existing_answer", "text"],
                        template=refineTemplate,
                    )
                    chain = load_summarize_chain(llm, chain_type=chainType,
                                                question_prompt=qaPrompt, refine_prompt=refinePrompt)
                else:
                    Prompt = PromptTemplate(template=pTemplate, input_variables=[InputVariables])
                    chain = load_summarize_chain(llm, chain_type=chainType, prompt=Prompt)
                logging.info("Chain Loaded")
                summaryResponse = chain.run(docs)
            except Exception as e:
                logging.error(e)

            return summaryResponse
        else:
            return summaryResponse
        
def ComposeResponse(promptType, promptName, chainType, docType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(promptType, promptName, chainType, docType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(promptType, promptName, chainType, docType, record):
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
        inlineText = data['text']
        overrides = data['overrides']

        summaryResponse = Summarize(promptType, promptName, chainType, docType, inlineText, overrides)
        return ({
            "recordId": recordId,
            "data": {
                "text": summaryResponse
                    }
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

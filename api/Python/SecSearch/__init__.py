import logging, json, os
import azure.functions as func
import openai
import os
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import numpy as np
import pandas as pd
from Utilities.redisIndex import createRedisIndex, chunkAndEmbed, performRedisSearch
from langchain.docstore.document import Document
from langchain.llms.openai import OpenAI, AzureOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import AnalyzeDocumentChain
from Utilities.envVars import *
from Utilities.cogSearch import performCogSearch

redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort

def SecSearch(indexType, indexName,  question, top, embeddingModelType):
    logging.info("Embedding text")
    try:
        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                    temperature=os.environ['Temperature'] or 0.3,
                    openai_api_key=OpenAiKey,
                    max_tokens=1024,
                    batch_size=10)
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = OpenAI(temperature=os.environ['Temperature'] or 0.3,
                    openai_api_key=OpenAiApiKey)
            
        logging.info("LLM Setup done")

        if (indexType == 'redis'):
            results = performRedisSearch(question, indexName, int(top), [], 'content_vector', embeddingModelType)
            contentPdf = pd.DataFrame(list(map(lambda x: {'cik' : x.cik, 'company': x.company, 'filingType': x.filing_type, 
                                            'filingDate': x.filing_date, 'reportPeriod': x.period_of_report,
                                            'sic': x.sic, 'incState': x.state_of_inc, 'stateLoc': x.state_location,
                                                'fiscalYearEnd': x.fiscal_year_end, 'filingHtmlIndex': x.filing_html_index,
                                                'htmLink': x.htm_filing_link, 'completeFilingLink': x.complete_text_filing_link,
                                                'content': x.content, 'contentSummary': '',
                                                'filename': x.filename, 'vector_score': x.vector_score}, results.docs)))
            contentPdf = contentPdf.sort_values(by=['vector_score'], ascending=False)
            contentPdf = contentPdf.reset_index(drop=True)
            contentPdf = contentPdf.drop(columns=['vector_score'])
            summaryChain = load_summarize_chain(llm, chain_type="stuff")
            summarizeDocumentChain = AnalyzeDocumentChain(combine_docs_chain=summaryChain)
            logging.info("Calling Summarize")
            for index, row in contentPdf.iterrows():
                summary = summarizeDocumentChain.run(row['content'])
                #contentDoc = [Document(page_content=row['content'], metadata={"source": row['filename']})]
                #summary = summaryChain.run(contentDoc)
                row['contentSummary'] = summary
            return  json.loads((contentPdf.to_json(orient='records')))
        elif (indexType == 'cogsearchvs'):
            results = performCogSearch(indexType, embeddingModelType, question, indexName, int(top), returnFields=["id",
                     "cik", "company", "filing_type", "filing_date", "period_of_report", "sic", 
                     "state_of_inc", "state_location", "fiscal_year_end", "filing_html_index", "htm_filing_link",
                     "complete_text_filing_link", "filename", "content", "sourcefile"] )
            contentPdf = pd.DataFrame(list(map(lambda x: {'cik' : x['cik'], 'company': x['company'], 'filingType': x['filing_type'], 
                                'filingDate': x['filing_date'], 'reportPeriod': x['period_of_report'],
                                'sic': x['sic'], 'incState': x['state_of_inc'], 'stateLoc': x['state_location'],
                                'fiscalYearEnd': x['fiscal_year_end'], 'filingHtmlIndex': x['filing_html_index'],
                                'htmLink': x['htm_filing_link'], 'completeFilingLink': x['complete_text_filing_link'],
                                'content': x['content'], 'contentSummary': '',
                                'filename': x['filename']}, results)))
            summaryChain = load_summarize_chain(llm, chain_type="stuff")
            summarizeDocumentChain = AnalyzeDocumentChain(combine_docs_chain=summaryChain)
            logging.info("Calling Summarize")
            for index, row in contentPdf.iterrows():
                summary = summarizeDocumentChain.run(row['content'])
                row['contentSummary'] = summary
            return  json.loads((contentPdf.to_json(orient='records')))
    except Exception as e:
      logging.error(e)
      return [{
            "cik": "",
            "company": "Exception Occurred",
            "completeFilingLink": "",
            "content": str(e),
            "contentSummary": str(e),
            "filename": "",
            "filingDate": "",
            "filingHtmlIndex": "",
            "filingType": "",
            "fiscalYearEnd": "",
            "htmLink": "",
            "incState": "",
            "reportPeriod": "",
            "sic": "",
            "stateLoc": ""
        }]

def TransformValue(indexType, indexName, question, top, embeddingModelType, record):
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

        summaryResponse = SecSearch(indexType, indexName, question, top, embeddingModelType)
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

def ComposeResponse(indexType, indexName, question, top, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, indexName, question, top, embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        indexType = req.params.get('indexType')
        indexName = req.params.get('indexName')
        question = req.params.get('question')
        embeddingModelType = req.params.get('embeddingModelType')
        top = req.params.get('top')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(indexType, indexName, question, top, embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )


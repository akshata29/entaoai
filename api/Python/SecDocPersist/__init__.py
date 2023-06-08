import logging, json, os
import azure.functions as func
import openai
import os
import numpy as np
from Utilities.azureBlob import upsertMetadata, getBlob, getAllBlobs
from Utilities.envVars import *
from azure.search.documents.indexes.models import (  
    SearchIndex,  
    SearchField,  
    SearchFieldDataType,  
    SimpleField,  
    SearchableField,  
    SearchIndex,  
    SemanticConfiguration,  
    PrioritizedFields,  
    SemanticField,  
    SearchField,  
    SemanticSettings,  
    VectorSearch,  
    VectorSearchAlgorithmConfiguration,  
)
from azure.search.documents.models import Vector 
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential 
from Utilities.envVars import *
from Utilities.cogSearch import indexSections
import tiktoken
from Utilities.embeddings import generateEmbeddings
from itertools import islice

def GetAllFiles():
    # Get all files in the container from Azure Blob Storage
    # Create the BlobServiceClient object
    blobList = getAllBlobs(OpenAiDocConnStr, SecDocContainer)
    files = []
    for file in blobList:
        if (file.metadata == None):
            files.append({
            "filename" : file.name,
            "embedded": "false",
            })
        else:
            files.append({
                "filename" : file.name,
                "embedded": file.metadata["embedded"] if "embedded" in file.metadata else "false",
                })
    logging.info(f"Found {len(files)} files in the container")
    return files

def createSearchIndex(indexType, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        if indexType == "cogsearchvs":
            index = SearchIndex(
                name=indexName,
                fields=[
                            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                            SimpleField(name="cik", type=SearchFieldDataType.String),
                            SimpleField(name="company", type=SearchFieldDataType.String),
                            SimpleField(name="filing_type", type=SearchFieldDataType.String),
                            SimpleField(name="filing_date", type=SearchFieldDataType.String),
                            SimpleField(name="period_of_report", type=SearchFieldDataType.String),
                            SimpleField(name="sic", type=SearchFieldDataType.String),
                            SimpleField(name="state_of_inc", type=SearchFieldDataType.String),
                            SimpleField(name="state_location", type=SearchFieldDataType.String),
                            SimpleField(name="fiscal_year_end", type=SearchFieldDataType.String),
                            SimpleField(name="filing_html_index", type=SearchFieldDataType.String),
                            SimpleField(name="htm_filing_link", type=SearchFieldDataType.String),
                            SimpleField(name="complete_text_filing_link", type=SearchFieldDataType.String),
                            SimpleField(name="filename", type=SearchFieldDataType.String),
                            SimpleField(name="item_1", type=SearchFieldDataType.String),
                            SimpleField(name="item_1A", type=SearchFieldDataType.String),
                            SimpleField(name="item_1B", type=SearchFieldDataType.String),
                            SimpleField(name="item_2", type=SearchFieldDataType.String),
                            SimpleField(name="item_3", type=SearchFieldDataType.String),
                            SimpleField(name="item_4", type=SearchFieldDataType.String),
                            SimpleField(name="item_5", type=SearchFieldDataType.String),
                            SimpleField(name="item_6", type=SearchFieldDataType.String),
                            SimpleField(name="item_7", type=SearchFieldDataType.String),
                            SimpleField(name="item_7A", type=SearchFieldDataType.String),
                            SimpleField(name="item_8", type=SearchFieldDataType.String),
                            SimpleField(name="item_9", type=SearchFieldDataType.String),
                            SimpleField(name="item_9A", type=SearchFieldDataType.String),
                            SimpleField(name="item_9B", type=SearchFieldDataType.String),
                            SimpleField(name="item_10", type=SearchFieldDataType.String),
                            SimpleField(name="item_11", type=SearchFieldDataType.String),
                            SimpleField(name="item_12", type=SearchFieldDataType.String),
                            SimpleField(name="item_13", type=SearchFieldDataType.String),
                            SimpleField(name="item_14", type=SearchFieldDataType.String),
                            SimpleField(name="item_15", type=SearchFieldDataType.String),
                            SimpleField(name="metadata", type=SearchFieldDataType.String),
                            SearchableField(name="content", type=SearchFieldDataType.String,
                                            searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                            # SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                            #             searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                            SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True),
                ],
                vector_search = VectorSearch(
                    algorithm_configurations=[
                        VectorSearchAlgorithmConfiguration(
                            name="vectorConfig",
                            kind="hnsw",
                            hnsw_parameters={
                                "m": 4,
                                "efConstruction": 400,
                                "efSearch": 500,
                                "metric": "cosine"
                            }
                        )
                    ]
                ),
                semantic_settings=SemanticSettings(
                    configurations=[SemanticConfiguration(
                        name='semanticConfig',
                        prioritized_fields=PrioritizedFields(
                            title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
            )
        elif indexType == "cogsearch":
            index = SearchIndex(
                name=indexName,
                fields=[
                            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                            SimpleField(name="cik", type=SearchFieldDataType.String),
                            SimpleField(name="company", type=SearchFieldDataType.String),
                            SimpleField(name="filing_type", type=SearchFieldDataType.String),
                            SimpleField(name="filing_date", type=SearchFieldDataType.String),
                            SimpleField(name="period_of_report", type=SearchFieldDataType.String),
                            SimpleField(name="sic", type=SearchFieldDataType.String),
                            SimpleField(name="state_of_inc", type=SearchFieldDataType.String),
                            SimpleField(name="state_location", type=SearchFieldDataType.String),
                            SimpleField(name="fiscal_year_end", type=SearchFieldDataType.String),
                            SimpleField(name="filing_html_index", type=SearchFieldDataType.String),
                            SimpleField(name="htm_filing_link", type=SearchFieldDataType.String),
                            SimpleField(name="complete_text_filing_link", type=SearchFieldDataType.String),
                            SimpleField(name="filename", type=SearchFieldDataType.String),
                            SimpleField(name="item_1", type=SearchFieldDataType.String),
                            SimpleField(name="item_1A", type=SearchFieldDataType.String),
                            SimpleField(name="item_1B", type=SearchFieldDataType.String),
                            SimpleField(name="item_2", type=SearchFieldDataType.String),
                            SimpleField(name="item_3", type=SearchFieldDataType.String),
                            SimpleField(name="item_4", type=SearchFieldDataType.String),
                            SimpleField(name="item_5", type=SearchFieldDataType.String),
                            SimpleField(name="item_6", type=SearchFieldDataType.String),
                            SimpleField(name="item_7", type=SearchFieldDataType.String),
                            SimpleField(name="item_7A", type=SearchFieldDataType.String),
                            SimpleField(name="item_8", type=SearchFieldDataType.String),
                            SimpleField(name="item_9", type=SearchFieldDataType.String),
                            SimpleField(name="item_9A", type=SearchFieldDataType.String),
                            SimpleField(name="item_9B", type=SearchFieldDataType.String),
                            SimpleField(name="item_10", type=SearchFieldDataType.String),
                            SimpleField(name="item_11", type=SearchFieldDataType.String),
                            SimpleField(name="item_12", type=SearchFieldDataType.String),
                            SimpleField(name="item_13", type=SearchFieldDataType.String),
                            SimpleField(name="item_14", type=SearchFieldDataType.String),
                            SimpleField(name="item_15", type=SearchFieldDataType.String),
                            SimpleField(name="metadata", type=SearchFieldDataType.String),
                            SearchableField(name="content", type=SearchFieldDataType.String,
                                            searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                            SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True),
                ],
                semantic_settings=SemanticSettings(
                    configurations=[SemanticConfiguration(
                        name='semanticConfig',
                        prioritized_fields=PrioritizedFields(
                            title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
            )

        try:
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def batched(iterable, n):
    """Batch data into tuples of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := tuple(islice(it, n))):
        yield batch

def chunkedTokens(text, encoding_name, chunk_length):
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    chunks_iterator = batched(tokens, chunk_length)
    yield from chunks_iterator

def getChunkedText(text, encoding_name="cl100k_base", max_tokens=1500):
    chunked_text = []
    encoding = tiktoken.get_encoding(encoding_name)
    for chunk in chunkedTokens(text, encoding_name=encoding_name, chunk_length=max_tokens):
        chunked_text.append(encoding.decode(chunk))
    return chunked_text

def chunkAndEmbed(embeddingModelType, indexType, indexName, secDoc, fullPath):
    encoding = tiktoken.get_encoding("cl100k_base")
    fullData = []
    text = secDoc['item_1'] + secDoc['item_1A'] + secDoc['item_7'] + secDoc['item_7A']
    text = text.replace("\n", " ")
    # Since we are not embedding, let's not worry about the length of the text
    # length = len(encoding.encode(text))

    if indexType == "cogsearchvs":
        # if length > 1500:
        #     k=0
        #     chunkedText = getChunkedText(text, encoding_name="cl100k_base", max_tokens=1500)
        #     logging.info(f"Total chunks: {len(chunkedText)}")
        #     for chunk in chunkedText:
        #         secCommonData = {
        #             "id": f"{fullPath}-{k}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
        #             "cik": secDoc['cik'],
        #             "company": secDoc['company'],
        #             "filing_type": secDoc['filing_type'],
        #             "filing_date": secDoc['filing_date'],
        #             "period_of_report": secDoc['period_of_report'],
        #             "sic": secDoc['sic'],
        #             "state_of_inc": secDoc['state_of_inc'],
        #             "state_location": secDoc['state_location'],
        #             "fiscal_year_end": secDoc['fiscal_year_end'],
        #             "filing_html_index": secDoc['filing_html_index'],
        #             "htm_filing_link": secDoc['htm_filing_link'],
        #             "complete_text_filing_link": secDoc['complete_text_filing_link'],
        #             "filename": secDoc['filename'],
        #             "item_1": secDoc['item_1'],
        #             "item_1A": secDoc['item_1A'],
        #             "item_1B": secDoc['item_1B'],
        #             "item_2": secDoc['item_2'],
        #             "item_3": secDoc['item_3'],
        #             "item_4": secDoc['item_4'],
        #             "item_5": secDoc['item_5'],
        #             "item_6": secDoc['item_6'],
        #             "item_7": secDoc['item_7'],
        #             "item_7A": secDoc['item_7A'],
        #             "item_8": secDoc['item_8'],
        #             "item_9": secDoc['item_9'],
        #             "item_9A": secDoc['item_9A'],
        #             "item_9B": secDoc['item_9B'],
        #             "item_10": secDoc['item_10'],
        #             "item_11": secDoc['item_11'],
        #             "item_12": secDoc['item_12'],
        #             "item_13": secDoc['item_13'],
        #             "item_14": secDoc['item_14'],
        #             "item_15": secDoc['item_15'],
        #             "content": chunk,
        #             #"contentVector": [],
        #             "metadata" : json.dumps({"cik": secDoc['cik'], "source": secDoc['filename'], "filingType": secDoc['filing_type'], "reportDate": secDoc['period_of_report']}),
        #             "sourcefile": fullPath
        #         }
        #         # Comment for now on not generating embeddings
        #         #secCommonData['contentVector'] = generateEmbeddings(embeddingModelType, chunk)
        #         fullData.append(secCommonData)
        #         k=k+1
        # else:
        #logging.info(f"Process full text with text {text}")
        secCommonData = {
                "id": f"{fullPath}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "cik": secDoc['cik'],
                "company": secDoc['company'],
                "filing_type": secDoc['filing_type'],
                "filing_date": secDoc['filing_date'],
                "period_of_report": secDoc['period_of_report'],
                "sic": secDoc['sic'],
                "state_of_inc": secDoc['state_of_inc'],
                "state_location": secDoc['state_location'],
                "fiscal_year_end": secDoc['fiscal_year_end'],
                "filing_html_index": secDoc['filing_html_index'],
                "htm_filing_link": secDoc['htm_filing_link'],
                "complete_text_filing_link": secDoc['complete_text_filing_link'],
                "filename": secDoc['filename'],
                "item_1": secDoc['item_1'],
                "item_1A": secDoc['item_1A'],
                "item_1B": secDoc['item_1B'],
                "item_2": secDoc['item_2'],
                "item_3": secDoc['item_3'],
                "item_4": secDoc['item_4'],
                "item_5": secDoc['item_5'],
                "item_6": secDoc['item_6'],
                "item_7": secDoc['item_7'],
                "item_7A": secDoc['item_7A'],
                "item_8": secDoc['item_8'],
                "item_9": secDoc['item_9'],
                "item_9A": secDoc['item_9A'],
                "item_9B": secDoc['item_9B'],
                "item_10": secDoc['item_10'],
                "item_11": secDoc['item_11'],
                "item_12": secDoc['item_12'],
                "item_13": secDoc['item_13'],
                "item_14": secDoc['item_14'],
                "item_15": secDoc['item_15'],
                "content": text,
                #"contentVector": [],
                "metadata" : json.dumps({"cik": secDoc['cik'], "source": secDoc['filename'], "filingType": secDoc['filing_type'], "reportDate": secDoc['period_of_report']}),
                "sourcefile": fullPath
            }
        # Comment for now on not generating embeddings
        #secCommonData['contentVector'] = generateEmbeddings(embeddingModelType, text)
        fullData.append(secCommonData)

        searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))
        results = searchClient.upload_documents(fullData)
        succeeded = sum([1 for r in results if r.succeeded])
        logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

    return None

def PersistSecDocs(embeddingModelType, indexType, indexName,  value):
    logging.info("Embedding text")
    try:
        filesData = GetAllFiles()
        filesData = list(filter(lambda x : x['embedded'] == "false", filesData))
        logging.info(filesData)
        filesData = list(map(lambda x: {'filename': x['filename']}, filesData))

        logging.info(f"Found {len(filesData)} files to embed")
        for file in filesData:
            fileName = file['filename']
            readBytes = getBlob(OpenAiDocConnStr, SecDocContainer, fileName)
            secDoc = json.loads(readBytes.decode("utf-8"))           
            # For now we will combine Item 1, 1A, 7, 7A into a single field "content"
            # item_1 = TextField(name="item_1")
            # item_1A = TextField(name="item_1A")
            # item_1B = TextField(name="item_1B")
            # item_2 = TextField(name="item_2")
            # item_3 = TextField(name="item_3")
            # item_4 = TextField(name="item_4")
            # item_5 = TextField(name="item_5")
            # item_6 = TextField(name="item_6")
            # item_7 = TextField(name="item_7")
            # item_7A = TextField(name="item_7A")
            # item_8 = TextField(name="item_8")
            # item_9 = TextField(name="item_9")
            # item_9A = TextField(name="item_9A")
            # item_9B = TextField(name="item_9B")
            # item_10 = TextField(name="item_10")
            # item_11 = TextField(name="item_11")
            # item_12 = TextField(name="item_12")
            # item_13 = TextField(name="item_13")
            # item_14 = TextField(name="item_14")
            # item_15 = TextField(name="item_15")
            # item1Embedding = VectorField("item1_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item1AEmbedding = VectorField("item1A_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item7Embedding = VectorField("item7_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item7AEmbedding = VectorField("item7A_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # item8Embedding = VectorField("item8_vector", "HNSW", { "TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": distanceMetrics, "INITIAL_CAP": 3155})
            # fields = [cik, company, filing_type, filing_date, period_of_report, sic, state_of_inc, state_location, 
            #          fiscal_year_end, filing_html_index, htm_filing_link, complete_text_filing_link, filename,
            #          item_1, item_1A, item_1B, item_2, item_3, item_4, item_5, item_6, item_7, item_7A, item_8, item_9, 
            #          item_9A, item_9B, item_10, item_11, item_12, item_13, item_14, item_15, item1Embedding,
            #          item1AEmbedding, item7Embedding, item7AEmbedding, item8Embedding]
            
            if indexType == "cogsearchvs":
                logging.info("Create index")
                createSearchIndex(indexType, indexName)
                logging.info("Index created")
                logging.info("Embedding")
                chunkAndEmbed(embeddingModelType, indexType, indexName, secDoc, os.path.basename(fileName))
                logging.info("Embedding complete")
                metadata = {'embedded': 'true', 'indexType': indexType, "indexName": indexName}
                upsertMetadata(OpenAiDocConnStr, SecDocContainer, fileName, metadata)
        return "Success"
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(embeddingModelType, indexType, indexName, record):
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

        summaryResponse = PersistSecDocs(embeddingModelType, indexType, indexName, value)
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

def ComposeResponse(embeddingModelType, indexType, indexName, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(embeddingModelType, indexType, indexName, value)
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
        embeddingModelType = req.params.get('embeddingModelType')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(embeddingModelType, indexType, indexName, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )


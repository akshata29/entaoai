from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
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
from tenacity import retry, wait_random_exponential, stop_after_attempt  
import openai
import logging

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
# Function to generate embeddings for title and content fields, also used for query embeddings
def generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, text):
    if (embeddingModelType == 'azureopenai'):
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"{OpenAiEndPoint}"

        response = openai.Embedding.create(
            input=text, engine=OpenAiEmbedding)
        embeddings = response['data'][0]['embedding']

    elif embeddingModelType == "openai":
        try:
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey

            response = openai.Embedding.create(
                input=text, engine="text-embedding-ada-002", api_key = OpenAiApiKey)
            embeddings = response['data'][0]['embedding']
        except Exception as e:
            logging.info(e)
        
    return embeddings

def deleteSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName in indexClient.list_index_names():
        logging.info(f"Deleting {indexName} search index")
        indexClient.delete_index(indexName)
    else:
        logging.info(f"Search index {indexName} does not exist")

def createPibIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="symbol", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="cik", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="step", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="description", type="Edm.String", retrievable=True),
                        SearchableField(name="insertedDate", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="pibData", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        #SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='pibData')]))])
        )

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def findPibData(SearchService, SearchKey, indexName, cik, step, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="cik eq '" + cik + "' and step eq '" + step + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def deletePibData(SearchService, SearchKey, indexName, cik, step, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="cik eq '" + cik + "' and step eq '" + step + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        if r.get_count() > 0:
            for doc in r:
                searchClient.delete_documents(doc)
        return None
    except Exception as e:
        print(e)

    return None

def createEarningCallIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="symbol", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="quarter", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="year", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="callDate", type="Edm.String", retrievable=True),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        #SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def findEarningCalls(SearchService, SearchKey, indexName, symbol, quarter, year, returnFields=["id", "content", "sourcefile"]):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="symbol eq '" + symbol + "' and quarter eq '" + quarter + "' and year eq '" + year + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def findEarningCallsBySymbol(SearchService, SearchKey, indexName, symbol, returnFields=["id", "content", "sourcefile"]):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="symbol eq '" + symbol + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def performEarningCallCogSearch(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, 
                                embeddingModelType, OpenAiEmbedding, symbol, quarter, year, question, indexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        r = searchClient.search(  
            search_text="",  
            filter="symbol eq '" + symbol + "' and quarter eq '" + quarter + "' and year eq '" + year + "'",
            vector=Vector(value=generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, question), k=k, fields="contentVector"),  
            select=returnFields,
            semantic_configuration_name="semanticConfig"
        )
        return r
    except Exception as e:
        print(e)

    return None

def createEarningCallVectorIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="symbol", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="quarter", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="year", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="callDate", type="Edm.String", retrievable=True),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                    searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
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

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def createEarningCallSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, docs,
                              callDate, symbol, year, quarter):
    counter = 1
    for i in docs:
        yield {
            "id": f"{symbol}-{year}-{quarter}-{counter}",
            "symbol": symbol,
            "quarter": quarter,
            "year": year,
            "callDate": callDate,
            "content": i.page_content,
            "contentVector": generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, i.page_content)
        }
        counter += 1

def indexEarningCallSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, 
                             OpenAiEmbedding, indexName, docs, callDate, symbol, year, quarter):
    logging.info("Total docs: " + str(len(docs)))
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))

    # Validate if we already have created documents for this call transcripts
    r = searchClient.search(  
            search_text="",
            filter="symbol eq '" + symbol + "' and year eq '" + year + "' and quarter eq '" + quarter + "'",
            semantic_configuration_name="semanticConfig",
            include_total_count=True
    )
    logging.info(f"Found {r.get_count()} sections for {symbol} {year} Q{quarter}")

    if r.get_count() > 0:
        logging.info(f"Already indexed {r.get_count()} sections for {symbol} {year} Q{quarter}")
        return
    
    sections = createEarningCallSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, docs,
                                         callDate, symbol, year, quarter)
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = searchClient.index_documents(batch=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def createPressReleaseIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="symbol", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="releaseDate", type="Edm.String", retrievable=True),
                        SearchableField(name="title", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        #SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def createStockNewsIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="symbol", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="publishedDate", type="Edm.String", retrievable=True),
                        SearchableField(name="title", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="image", type="Edm.String", retrievable=True),
                        SearchableField(name="site", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="url", type="Edm.String", retrievable=True),
                        #SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def mergeDocs(SearchService, SearchKey, indexName, docs):
    logging.info("Total docs: " + str(len(docs)))
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))
    i = 0
    batch = []
    for s in docs:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = searchClient.merge_or_upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.merge_or_upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def createSecFilingIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True), 
                        SimpleField(name="cik", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="company", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="filingType", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="filingDate", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="periodOfReport", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="sic", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="stateOfInc", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="stateLocation", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="fiscalYearEnd", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="filingHtmlIndex", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="htmFilingLink", type=SearchFieldDataType.String, retrievable=True),
                        SimpleField(name="completeTextFilingLink", type=SearchFieldDataType.String, retrievable=True),
                        SimpleField(name="filename", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item1", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item1A", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item1B", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item2", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item3", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item4", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item5", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item6", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item7", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item7A", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item8", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item9", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item9A", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item9B", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item10", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item11", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item12", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item13", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item14", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="item15", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SimpleField(name="metadata", type=SearchFieldDataType.String, searchable=True, retrievable=True),
                        SearchableField(name="content", type=SearchFieldDataType.String, retrievable=True),
                        # SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        #             searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                        SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)

def findSecFiling(SearchService, SearchKey, indexName, cik, filingType, filingDate, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="cik eq '" + cik + "' and filingType eq '" + filingType + "' and filingDate eq '" + filingDate + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def createSecFilingsVectorIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="symbol", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="cik", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="latestFilingDate", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="filingType", type="Edm.String", sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                    searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
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

        try:
            logging.info(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            logging.info(e)
    else:
        logging.info(f"Search index {indexName} already exists")

def createSecFilingsSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, docs,
                              cik, symbol, latestFilingDate, filingType):
    counter = 1
    for i in docs:
        yield {
            "id": f"{symbol}-{latestFilingDate}-{filingType}-{counter}",
            "symbol": symbol,
            "cik": cik,
            "latestFilingDate": latestFilingDate,
            "filingType": filingType,
            "content": i.page_content,
            "contentVector": generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, i.page_content)
        }
        counter += 1

def indexSecFilingsSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, 
                             OpenAiEmbedding, indexName, docs, cik, symbol, latestFilingDate, filingType):
    logging.info("Total docs: " + str(len(docs)))
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))

    # Validate if we already have created documents for this call transcripts
    r = searchClient.search(  
            search_text="",
            filter="cik eq '" + cik + "' and symbol eq '" + symbol + "' and latestFilingDate eq '" + latestFilingDate  + "' and filingType eq '" + filingType + "'",
            semantic_configuration_name="semanticConfig",
            include_total_count=True
    )
    logging.info(f"Found {r.get_count()} sections for {symbol} {cik} {latestFilingDate} {filingType}")

    if r.get_count() > 0:
        logging.info(f"Already indexed {r.get_count()} sections for {symbol} {cik} {latestFilingDate} {filingType}")
        return
    
    sections = createSecFilingsSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, docs,
                                         cik, symbol, latestFilingDate, filingType)
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = searchClient.index_documents(batch=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def findLatestSecFilings(SearchService, SearchKey, indexName, cik, symbol, latestFilingDate, filingType, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="cik eq '" + cik + "' and symbol eq '" + symbol + "' and latestFilingDate eq '" + latestFilingDate  + "' and filingType eq '" + filingType + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def indexDocs(SearchService, SearchKey, indexName, docs):
    logging.info("Total docs: " + str(len(docs)))
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))
    i = 0
    batch = []
    for s in docs:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = searchClient.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def performLatestPibDataSearch(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, 
                               OpenAiEmbedding, filterData, question, indexName, k, returnFields=["id", "content"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        r = searchClient.search(  
            search_text="",
            filter=filterData,
            vector=Vector(value=generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, question), k=k, fields="contentVector"),  
            select=returnFields,
            semantic_configuration_name="semanticConfig"
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def performCogSearch(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, OpenAiEmbedding, question, indexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        r = searchClient.search(  
            search_text="",  
            vector=Vector(value=generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, question), k=k, fields="contentVector"),  
            select=returnFields,
            semantic_configuration_name="semanticConfig"
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def performCogVectorSearch(embedValue, embedField, SearchService, SearchKey, indexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        r = searchClient.search(  
            search_text="",  
            vector=Vector(value=embedValue, k=k, fields=embedField),  
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def performKbCogVectorSearch(embedValue, embedField, SearchService, SearchKey, indexType, indexName, kbIndexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=kbIndexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            vector=Vector(value=embedValue, k=k, fields=embedField),  
            filter="indexType eq '" + indexType + "' and indexName eq '" + indexName + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        logging.info(e)

    return None

def findFileInIndex(SearchService, SearchKey, indexName, fileName, returnFields=["id", "content", "sourcefile"]):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="sourcefile eq '" + fileName + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def createSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                    searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
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

        try:
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def createSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, fileName, docs):
    counter = 1
    for i in docs:
        yield {
            "id": f"{fileName}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
            "content": i.page_content,
            "contentVector": generateEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, i.page_content),
            "sourcefile": os.path.basename(fileName)
        }
        counter += 1

def indexSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, OpenAiEmbedding, fileName, indexName, docs):
    print("Total docs: " + str(len(docs)))
    sections = createSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, fileName, docs)
    print(f"Indexing sections from '{fileName}' into search index '{indexName}'")
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = searchClient.index_documents(batch=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def createProspectusSummary(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="fileName", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="docType", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="topic", type=SearchFieldDataType.String, sortable=True,
                                        searchable=True, retrievable=True, filterable=True, facetable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="summary", type="Edm.String", retrievable=True),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='summary')]))])
        )

        try:
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def findTopicSummaryInIndex(SearchService, SearchKey, indexName, fileName, docType, topic, returnFields=["id", "fileName", "docType", 'topic', "summary"]):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(
            search_text="",
            filter="fileName eq '" + fileName + "' and docType eq '" + docType + "' and topic eq '" + topic + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def findSummaryInIndex(SearchService, SearchKey, indexName, fileName, docType, returnFields=["id", "fileName", "docType", 'topic', "summary"]):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(
            search_text="",
            filter="fileName eq '" + fileName + "' and docType eq '" + docType + "'",
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

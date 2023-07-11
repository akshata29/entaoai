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

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
# Function to generate embeddings for title and content fields, also used for query embeddings
def generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, text):
    if (embeddingModelType == 'azureopenai'):
        baseUrl = f"https://{OpenAiService}.openai.azure.com"
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"

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
            print(e)
        
    return embeddings

def deleteSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName in indexClient.list_index_names():
        print(f"Deleting {indexName} search index")
        indexClient.delete_index(indexName)
    else:
        print(f"Search index {indexName} does not exist")
        
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
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

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
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def createEarningCallSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, docs,
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
            "contentVector": generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, i.page_content)
        }
        counter += 1

def indexEarningCallSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, 
                             OpenAiEmbedding, indexName, docs, callDate, symbol, year, quarter):
    print("Total docs: " + str(len(docs)))
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
    print(f"Found {r.get_count()} sections for {symbol} {year} Q{quarter}")

    if r.get_count() > 0:
        print(f"Already indexed {r.get_count()} sections for {symbol} {year} Q{quarter}")
        return
    
    sections = createEarningCallSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, docs,
                                         callDate, symbol, year, quarter)
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
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

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
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def mergeDocs(SearchService, SearchKey, indexName, docs):
    print("Total docs: " + str(len(docs)))
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
            print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.merge_or_upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

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
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)

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
        print(e)

    return None


def indexDocs(SearchService, SearchKey, indexName, docs):
    print("Total docs: " + str(len(docs)))
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
            print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def performCogSearch(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, OpenAiEmbedding, question, indexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        r = searchClient.search(  
            search_text="",  
            vector=Vector(value=generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, question), k=k, fields="contentVector"),  
            select=returnFields,
            semantic_configuration_name="semanticConfig"
        )
        return r
    except Exception as e:
        print(e)

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
        print(e)

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
        print(e)

    return None

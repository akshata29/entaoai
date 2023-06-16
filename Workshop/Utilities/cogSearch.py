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
def generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, text):
    if (embeddingModelType == 'azureopenai'):
        baseUrl = f"https://{OpenAiService}.openai.azure.com"
        openai.api_type = "azure"
        openai.api_key = OpenAiKey
        openai.api_version = OpenAiVersion
        openai.api_base = f"https://{OpenAiService}.openai.azure.com"

        response = openai.Embedding.create(
            input=text, engine="text-embedding-ada-002")
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
                        SimpleField(name="calldate", type="Edm.String", retrievable=True),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
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
                        SimpleField(name="releasedate", type="Edm.String", retrievable=True),
                        SearchableField(name="title", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
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
                        SimpleField(name="publisheddate", type="Edm.String", retrievable=True),
                        SearchableField(name="title", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="image", type="Edm.String", retrievable=True),
                        SearchableField(name="site", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="url", type="Edm.String", retrievable=True),
                        SimpleField(name="inserteddate", type="Edm.String", searchable=True, retrievable=True,),
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

def createSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, fileName, docs):
    counter = 1
    for i in docs:
        yield {
            "id": f"{fileName}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
            "content": i.page_content,
            "contentVector": generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, i.page_content),
            "sourcefile": os.path.basename(fileName)
        }
        counter += 1

def indexSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, fileName, indexName, docs):
    print("Total docs: " + str(len(docs)))
    sections = createSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, fileName, docs)
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

def performCogSearch(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, question, indexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        r = searchClient.search(  
            search_text="",  
            vector=Vector(value=generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, question), k=k, fields="contentVector"),  
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

def createKbSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="question", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SimpleField(name="indexType", type="Edm.String", searchable=True, retrievable=True, filterable=True, facetable=False),
                        SimpleField(name="indexName", type="Edm.String", searchable=True, retrievable=True, filterable=True, facetable=False),
                        SearchField(name="vectorQuestion", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                    searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                        SimpleField(name="answer", type="Edm.String", filterable=False, facetable=False),
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
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='question')]))])
        )

        try:
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def performKbCogVectorSearch(embedValue, embedField, SearchService, SearchKey, indexType, indexName, kbIndexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=kbIndexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        createKbSearchIndex(SearchService, SearchKey, kbIndexName)
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
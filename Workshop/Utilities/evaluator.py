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

def createEvaluatorDocumentSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="documentId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="documentName", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="sourceFile", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft")
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='documentName')]))])
        )

        try:
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def createEvaluatorQaSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="documentId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="questionId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="question", type=SearchFieldDataType.String, retrievable=True),
                        SearchableField(name="answer", type=SearchFieldDataType.String, retrievable=True)
            ],
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

def createEvaluatorResultIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="runId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="subRunId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="documentId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="retrieverType", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="promptStyle", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="splitMethod", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="chunkSize", type=SearchFieldDataType.String, filterable=True, retrievable=True),
                        SearchableField(name="overlap", type=SearchFieldDataType.String, filterable=True, retrievable=True),
                        SearchableField(name="question", type=SearchFieldDataType.String, retrievable=True),
                        SearchableField(name="answer", type=SearchFieldDataType.String, retrievable=True),
                        SearchableField(name="predictedAnswer", type=SearchFieldDataType.String, retrievable=True),
                        SearchableField(name="answerScore", type=SearchFieldDataType.String, retrievable=True),
                        SearchableField(name="retrievalScore", type=SearchFieldDataType.String, retrievable=True),
                        SearchableField(name="latency", type=SearchFieldDataType.String, retrievable=True),
            ],
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

def createEvaluatorRunIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="runId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="subRunId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="documentId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="retrieverType", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="promptStyle", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="splitMethod", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="chunkSize", type=SearchFieldDataType.String, filterable=True, retrievable=True),
                        SearchableField(name="overlap", type=SearchFieldDataType.String, filterable=True, retrievable=True),
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='semanticConfig',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='documentId')]))])
        )

        try:
            print(f"Creating {indexName} search index")
            indexClient.create_index(index)
        except Exception as e:
            print(e)
    else:
        print(f"Search index {indexName} already exists")

def searchEvaluatorRunIdIndex(SearchService, SearchKey, indexName, documentId):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="documentId eq '" + documentId + "'",
            top=1,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def searchEvaluatorRunIndex(SearchService, SearchKey, indexName, documentId, retriever, promptStyle, splitMethod, chunkSize, overlap):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="documentId eq '" + documentId + "' and splitMethod eq '" + splitMethod + "' and chunkSize eq '" + chunkSize + "' and overlap eq '" + overlap + 
                "' and retrieverType eq '" + retriever + "' and promptStyle eq '" + promptStyle + "'",
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def searchEvaluatorDocumentIndexedData(SearchService, SearchKey, indexName, documentId, splitMethod, chunkSize, overlap):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="documentId eq '" + documentId + "' and splitMethod eq '" + splitMethod + "' and chunkSize eq '" + chunkSize + "' and overlap eq '" + overlap + "'",
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def searchEvaluatorDocument(SearchService, SearchKey,indexName, documentName):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="documentName eq '" + documentName + "'",
            semantic_configuration_name="semanticConfig",
            top=1,
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def searchEvaluatorQaData(SearchService, SearchKey,indexName, documentId):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="documentId eq '" + documentId + "'",
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

def createEvaluatorDataSearchIndex(SearchService, SearchKey, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                        SearchableField(name="documentId", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="splitMethod", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="chunkSize", type=SearchFieldDataType.String, filterable=True, retrievable=True),
                        SearchableField(name="overlap", type=SearchFieldDataType.String, filterable=True, retrievable=True),
                        SearchableField(name="model", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="modelType", type=SearchFieldDataType.String, searchable=True, filterable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchableField(name="content", type=SearchFieldDataType.String,
                                        searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                        SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                    searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                        SimpleField(name="sourceFile", type=SearchFieldDataType.String, filterable=True, facetable=True),
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

def createEvaluatorDataSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, fileName, 
                            docs, splitMethod, chunkSize, overlap, model, modelType, documentId):
    counter = 1

    for i in docs:
        yield {
            "id": f"{fileName}-{counter}-{chunkSize}-{overlap}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
            "documentId": documentId,
            "splitMethod": splitMethod,
            "chunkSize": chunkSize,
            "overlap": overlap,
            "model": model,
            "modelType": modelType,
            "content": i.page_content,
            "contentVector": generateEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding, i.page_content),
            "sourceFile": os.path.basename(fileName)
        }
        counter += 1

def indexEvaluatorDataSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, 
                           embeddingModelType, OpenAiEmbedding, fileName, indexName, docs,
                           splitMethod, chunkSize, overlap, model, modelType, documentId):
    print("Total docs: " + str(len(docs)))
    sections = createEvaluatorDataSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, embeddingModelType, OpenAiEmbedding,
                                       fileName, docs, splitMethod, chunkSize, overlap, model, modelType, documentId)
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

def getEvaluatorResult(SearchService, SearchKey, indexName, documentId):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    
    try:
        r = searchClient.search(  
            search_text="",
            filter="documentId eq '" + documentId + "'",
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None
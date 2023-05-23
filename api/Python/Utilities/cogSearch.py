from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
import logging
from azure.search.documents.models import QueryType
from Utilities.embeddings import generateEmbeddings
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
from Utilities.envVars import *

def deleteSearchIndex(indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName in indexClient.list_index_names():
        logging.info(f"Deleting {indexName} search index")
        indexClient.delete_index(indexName)
    else:
        logging.info(f"Search index {indexName} does not exist")
        
def createSearchIndex(indexType, indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        if indexType == "cogsearchvs":
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
        elif indexType == "cogsearch":
            index = SearchIndex(
                name=indexName,
                fields=[
                            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
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

def createSections(indexType, embeddingModelType, fileName, docs):
    counter = 1
    if indexType == "cogsearchvs":
        for i in docs:
            yield {
                "id": f"{fileName}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "content": i.page_content,
                "contentVector": generateEmbeddings(embeddingModelType, i.page_content),
                "sourcefile": os.path.basename(fileName)
            }
            counter += 1
    elif indexType == "cogsearch":
        for i in docs:
            yield {
                "id": f"{fileName}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "content": i.page_content,
                "sourcefile": os.path.basename(fileName)
            }
            counter += 1

def indexSections(indexType, embeddingModelType, fileName, indexName, docs):

    logging.info("Total docs: " + str(len(docs)))
    sections = createSections(indexType, embeddingModelType, fileName, docs)
    logging.info(f"Indexing sections from '{fileName}' into search index '{indexName}'")
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net/",
                                    index_name=indexName,
                                    credential=AzureKeyCredential(SearchKey))
    
    # batch = []
    # for s in sections:
    #     batch.append(s)
    # results = searchClient.upload_documents(documents=batch)
    # succeeded = sum([1 for r in results if r.succeeded])
    # logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
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

def performCogSearch(indexType, embeddingModelType, question, indexName, k, returnFields=["id", "content", "sourcefile"] ):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        if indexType == "cogsearchvs":
            r = searchClient.search(  
                search_text="",  
                vector=Vector(value=generateEmbeddings(embeddingModelType, question), k=k, fields="contentVector"),  
                select=returnFields,
                semantic_configuration_name="semanticConfig"
            )
        elif indexType == "cogsearch":
            #r = searchClient.search(question, filter=None, top=k)
            try:
                r = searchClient.search(question, 
                                    filter=None,
                                    query_type=QueryType.SEMANTIC, 
                                    query_language="en-us", 
                                    query_speller="lexicon", 
                                    semantic_configuration_name="semanticConfig", 
                                    top=k, 
                                    query_caption="extractive|highlight-false")
            except Exception as e:
                 r = searchClient.search(question, 
                                filter=None,
                                query_type=QueryType.SEMANTIC, 
                                query_language="en-us", 
                                query_speller="lexicon", 
                                semantic_configuration_name="default", 
                                top=k, 
                                query_caption="extractive|highlight-false")
        return r
    except Exception as e:
        logging.info(e)

    return None

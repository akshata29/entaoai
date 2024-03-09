import logging
import os
import re

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.models import QueryType
from azure.search.documents.indexes.models import *

def create_clients():

    admin_client = SearchIndexClient(endpoint=f"https://{os.getenv('SearchService')}.search.windows.net/",
            credential=AzureKeyCredential(os.getenv('SearchKey')))
    
    search_client = SearchClient(endpoint=f"https://{os.getenv('SearchService')}.search.windows.net/",
                                    index_name=os.getenv('mmIndexName'),
                                    credential=AzureKeyCredential(os.getenv('SearchKey')))
    
    indexer_client = SearchIndexerClient(endpoint=f"https://{os.getenv('SearchService')}.search.windows.net/",
                                    index_name=os.getenv('mmIndexName'),
                                    credential=AzureKeyCredential(os.getenv('SearchKey')))

    sem_search_client = SearchClient(endpoint=f"https://{os.getenv('SearchService')}.search.windows.net/",
                                    index_name=os.getenv('mmSemanticIndexName'),
                                    credential=AzureKeyCredential(os.getenv('SearchKey')))

    
    # admin_client   = SearchIndexClient(endpoint=f"https://{os.getenv('SearchService')}.search.windows.net/",
    #                                 index_name=KB_INDEX_NAME,
    #                                 credential=AzureKeyCredential(os.getenv('SearchKey')))
    # search_client  = SearchClient(endpoint=COG_SEARCH_ENDPOINT,
    #                             index_name=KB_INDEX_NAME,
    #                             credential=AzureKeyCredential(COG_SEARCH_ADMIN_KEY))
    # indexer_client = SearchIndexerClient(endpoint=COG_SEARCH_ENDPOINT,
    #                                     index_name=KB_INDEX_NAME,
    #                                     credential=AzureKeyCredential(COG_SEARCH_ADMIN_KEY))
    # sem_search_client = SearchClient(endpoint=COG_SEARCH_ENDPOINT,
    #                                     index_name=KB_SEM_INDEX_NAME,
    #                                     credential=AzureKeyCredential(COG_SEARCH_ADMIN_KEY))

    return admin_client, search_client, indexer_client, sem_search_client

def create_schema():
    fields = [
        SimpleField(name="asset_id", type=SearchFieldDataType.String, key=True, filterable=True, sortable=True, retrievable=True),
        SearchableField(name="asset_path", type=SearchFieldDataType.String, sortable=True, filterable=True, retrievable=True),
        SearchableField(name="pdf_path", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="filename", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="image_file", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="asset_filename", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SimpleField(name="page_number", type=SearchFieldDataType.Int32, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="type", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="document_id", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="python_block", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="python_code", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="markdown", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="mermaid", type=SearchFieldDataType.String, retrievable=True, filterable=True, sortable=True),
        SearchableField(name="tags", type=SearchFieldDataType.String, analyzer_name="en.lucene", retrievable=True, filterable=True, sortable=True),
        SearchableField(name="text", type=SearchFieldDataType.String, analyzer_name="en.lucene", retrievable=True, filterable=True, sortable=True)  # Added "text" field
    ]
    return fields

def create_semantic_search_index(admin_client, search_client, indexer_client, sem_search_client, fields):
    useCogVectorSearch = 1
    
    if useCogVectorSearch == 1:
        vs = cogsearch_vecstore.CogSearchVecStore()

        try:    
            vs.delete_index()
            print ('Index', os.getenv('mmVectorIndexName'), 'Deleted')
        except Exception as ex:
            print (f"OK: Looks like index {os.getenv('mmVectorIndexName')} does not exist")

        try:
            vs.create_index()
            print ('Index', os.getenv('mmVectorIndexName'), 'created')
        except Exception as ex:
            print (f"Index creation exception {os.getenv('mmVectorIndexName')}:\n{ex}")    

    else:

        try:
            result = admin_client.delete_index(os.getenv('mmSemanticIndexName'))
            print ('Index', os.getenv('mmSemanticIndexName'), 'Deleted')
        except Exception as ex:
            print (f"Index deletion exception:\n{ex}")

        index = SearchIndex(
            name=os.getenv('mmSemanticIndexName'),
            fields=fields,
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='default',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )

        try:
            result = admin_client.create_index(index)
            print ('Index', result.name, 'created')
        except Exception as ex:
            print (f"Index creation exception:\n{ex}")        



def create_index(admin_client, search_client, indexer_client, sem_search_client, fields):

    try:
        result = admin_client.delete_index(os.getenv('mmIndexName'))
        print ('Index', os.getenv('mmIndexName'), 'Deleted')
    except Exception as ex:
        print (f"Index deletion exception:\n{ex}")

    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    scoring_profiles = []

    index = SearchIndex(
        name=os.getenv('mmIndexName'),
        fields=fields,
        scoring_profiles=scoring_profiles,
        suggesters = None,
        cors_options=cors_options)

    try:
        result = admin_client.create_index(index)
        print ('Index', result.name, 'created')
    except Exception as ex:
        print (f"Index creation exception:\n{ex}")
    
def index_semantic_sections(admin_client, search_client, indexer_client, sem_search_client, sections):

    i = 0
    batch = []
    for s in sections:
        dd = {
            "id": s['id'],
            "content": s['text_en'],
            "category": s['access'],
            "sourcefile": s['doc_url'],
            "orig_lang": s['orig_lang'],
            "container": s['container'],
            "filename": s['filename'],
            "web_url": s['web_url']
        }

        batch.append(dd) 
        i += 1
        if i % 1000 == 0:
            results = sem_search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = sem_search_client.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def create_indexer(admin_client, search_client, indexer_client, sem_search_client, container):
    container = SearchIndexerDataContainer(name=container)

    data_source = SearchIndexerDataSourceConnection(
        name=KB_DATA_SOURCE_NAME,
        type="azureblob",
        connection_string=KB_BLOB_CONN_STR,
        container=container
    )

    output_field_mappings.append({"sourceFieldName": "/document/status","targetFieldName": "status", "mappingFunction":None})


    indexer = SearchIndexer(
        name=KB_INDEXER_NAME,
        data_source_name=KB_DATA_SOURCE_NAME,
        target_index_name=KB_INDEX_NAME,
        skillset_name=KB_SKILLSET_NAME,
        field_mappings = [ { "sourceFieldName": "metadata_storage_path", "targetFieldName": "url" },
                           { "sourceFieldName": "metadata_storage_name", "targetFieldName": "file_name" },
                         ],
        output_field_mappings = output_field_mappings
    )

    try:
        indexer_client.delete_indexer(indexer)
        print(f"Deleted Indexer - {KB_INDEXER_NAME}")
    except Exception as ex:
        print (f"Indexer deletion exception:\n{ex}")

    try:
        indexer_client.delete_data_source_connection(data_source)
        print(f"Deleted Data Source - {KB_SKILLSET_NAME}")
    except Exception as ex:
        print (f"Data Source deletion exception:\n{ex}")

    try:
        result = indexer_client.create_data_source_connection(data_source)
        print(f"Created new Data Source Connection - {KB_DATA_SOURCE_NAME}")   
    except Exception as ex:
        print (f"Data source creation exception:\n{ex}")

    try:
        result = indexer_client.create_indexer(indexer)
        print(f"Created new Indexer - {KB_INDEXER_NAME}")
    except Exception as ex:
        print (f"Indexer creation exception:\n{ex}")



def run_indexer(admin_client, search_client, indexer_client, sem_search_client):
    print (f"Running Indexer {KB_INDEXER_NAME}")
    indexer_client.run_indexer(KB_INDEXER_NAME)



def ingest_kb(admin_client, search_client, indexer_client, sem_search_client, container = KB_BLOB_CONTAINER):
    create_semantic_search_index(admin_client, search_client, indexer_client, sem_search_client)
    create_index(admin_client, search_client, indexer_client, sem_search_client)
    create_skillset(admin_client, search_client, indexer_client, sem_search_client)
    create_indexer(admin_client, search_client, indexer_client, sem_search_client, container)
    run_indexer(admin_client, search_client, indexer_client, sem_search_client)







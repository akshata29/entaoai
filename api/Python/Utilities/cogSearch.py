from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
import logging
from azure.search.documents.models import QueryType

SearchService = os.environ['SearchService']
SearchKey = os.environ['SearchKey']

def createSearchIndex(indexName):
    indexClient = SearchIndexClient(endpoint=f"https://{SearchService}.search.windows.net/",
            credential=AzureKeyCredential(SearchKey))
    if indexName not in indexClient.list_index_names():
        index = SearchIndex(
            name=indexName,
            fields=[
                        SimpleField(name="id", type="Edm.String", key=True),
                        SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
                        #SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
                        SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True),
                        #SimpleField(name="totalpages", type="Edm.String", filterable=True, facetable=True),
                        #SimpleField(name="title", type="Edm.String", filterable=True, facetable=True)
                    ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='default',
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

def createSections(fileName, docs):
    counter = 1
    for i in docs:
        # yield {
        #     "id": f"{fileName}-{counter}".replace(".", "_").replace(" ", "_"),
        #     "content": i.page_content,
        #     "sourcepage": str(i.metadata["page_number"]),
        #     "totalpages": str(i.metadata["total_pages"]),
        #     "sourcefile": fileName,
        #     "title":i.metadata["title"]
        # }
        yield {
            "id": f"{fileName}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_"),
            "content": i.page_content,
            "sourcefile": fileName
        }
        counter += 1

def indexSections(fileName, indexName, docs):

    sections = createSections(fileName, docs)
    logging.info(f"Indexing sections from '{fileName}' into search index '{indexName}'")
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
            logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = searchClient.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        logging.info(f"\tIndexed {len(results)} sections, {succeeded} succeeded")

def performCogSearch(question, indexName, k):
    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        #r = searchClient.search(question, filter=None, top=k)
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

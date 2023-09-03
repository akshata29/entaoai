from promptflow import tool
import openai
from promptflow.connections import CustomConnection
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import QueryType
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
import json

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
                        SearchableField(name="indexType", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, facetable=False),
                        SearchableField(name="indexName", type=SearchFieldDataType.String, searchable=True, retrievable=True, filterable=True, facetable=False),
                        SearchField(name="vectorQuestion", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                    searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                        SimpleField(name="answer", type=SearchFieldDataType.String),
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
            filter="indexType eq '" + indexType + "' and indexName eq '" + indexName + "'",
            vector=Vector(value=embedValue, k=k, fields=embedField),  
            select=returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return r
    except Exception as e:
        print(e)

    return None

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def checkCacheAnswer(question:str, embeddedQuestion:object, indexType: str, indexNs:str, conn:CustomConnection):
  
  try:
    # Let's verify if the questions is already answered before and check our KB first before asking LLM
    # Let's perform the search on the KB first before asking the question to the model
    kbSearch = performKbCogVectorSearch(embeddedQuestion, 'vectorQuestion', conn.SearchService, conn.SearchKey, 
      indexType, indexNs, conn.KbIndexName, 1, ["id", "question", "indexType", "indexName", "answer"])

    print("KB Search Count: " + str(kbSearch.get_count()))

    if kbSearch.get_count() > 0:
        for s in kbSearch:
            if s['@search.score'] >= 0.95:
                jsonAnswer = json.loads(s['answer'])
                return {
                    "jsonAnswer": jsonAnswer,
                    "existingAnswer": True
                }
            else:
                print(s['@search.score'])
                return {
                    "jsonAnswer": None,
                    "existingAnswer": False
                }
    else:
        return {
            "jsonAnswer": None,
            "existingAnswer": False
        }
  except Exception as e:
    print(e)
    return {
        "jsonAnswer": None,
        "existingAnswer": False
    }

from promptflow import tool
from promptflow.connections import CustomConnection
from langchain.docstore.document import Document
from typing import Mapping
import numpy as np
import json
from langchain.vectorstores import FAISS

def performCogSearch(embedValue, embedField, SearchService, SearchKey, indexType, question, indexName, k, 
    returnFields=["id", "content", "sourcefile"] ):
    print("Performing CogSearch")
    print("SearchService: " + SearchService)
    print("indexName: " + indexName)

    searchClient = SearchClient(endpoint=f"https://{SearchService}.search.windows.net",
        index_name=indexName,
        credential=AzureKeyCredential(SearchKey))
    try:
        if indexType == "cogsearchvs":
            r = searchClient.search(  
                search_text="",  
                vector=Vector(value=embedValue, k=k, fields=embedField),  
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
        print(e)

    return None

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def searchVectorDb(embeddedQuestion:object, indexType:str, indexNs:str, topK:int, embeddings:object):
  docs = []

  if indexType == "faiss":
      
    try:
        faissDb = FAISS.load_local(indexNs, embeddings=embeddings)
        docs = faissDb.similarity_search_by_vector(embeddedQuestion, k=topK)
    except Exception as e:
        docs = [Document(page_content="No Results Found" + str(e), metadata={"id": "", "source": ""})]
        pass

    return docs

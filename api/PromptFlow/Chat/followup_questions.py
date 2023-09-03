from promptflow import tool
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from promptflow.connections import CustomConnection
import uuid
import json
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
from azure.cosmos import CosmosClient, PartitionKey
from azure.search.documents.models import Vector
import datetime
import uuid

def insertMessage(sessionId, type, role, totalTokens, tokens, response, cosmosContainer):
    aiMessage = {
        "id": str(uuid.uuid4()), 
        "type": type, 
        "role": role, 
        "sessionId": sessionId, 
        "tokens": tokens, 
        "timestamp": datetime.datetime.utcnow().isoformat(), 
        "content": response
    }
    cosmosContainer.create_item(body=aiMessage)

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

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def generateFollowupQuestions(retrievedDocs: list, question: str, promptTemplate:str, overrides:list, llm, modifiedAnswer:str, 
    indexType:str, indexNs:str, conn:CustomConnection) -> list:
    overrideChain = overrides.get("chainType") or 'stuff'
    sessionId = overrides.get('sessionId')

    try:
        cosmosClient = CosmosClient(url=conn.CosmosEndpoint, credential=conn.CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=conn.CosmosDatabase)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=conn.CosmosContainer, partition_key=cosmosKey)
    except Exception as e:
        print("Error connecting to CosmosDB: " + str(e))

    followupTemplate = """
    Generate three very brief follow-up questions that the user would likely ask next.
    Use double angle brackets to reference the questions, e.g. <>.
    Try not to repeat questions that have already been asked.

    Return the questions in the following format:
    <>
    <>
    <>

    ALWAYS return a "NEXT QUESTIONS" part in your answer.

    {context}
    """
    followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
    followupChain = load_qa_chain(llm, chain_type='stuff', prompt=followupPrompt)
    

    if promptTemplate == '':
        template = """
            Given the following extracted parts of a long document and a question, create a final answer. 
            If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
            If the answer is not contained within the text below, say \"I don't know\".

            {summaries}
            Question: {question}
        """
    else:
        template = promptTemplate
    
    rawDocs=[]
    for doc in retrievedDocs:
        rawDocs.append(doc.page_content)

    qaPrompt = PromptTemplate(template=template, input_variables=["summaries", "question"])

    if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
        thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
    elif overrideChain == "refine":
        thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
    
    # Followup questions
    followupAnswer = followupChain({"input_documents": retrievedDocs, "question": question}, return_only_outputs=True)
    nextQuestions = followupAnswer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:').replace('NEXT QUESTIONS:', '').replace('NEXT QUESTIONS', '')
    sources = ''                
    if (modifiedAnswer.find("I don't know") >= 0):
        sources = ''
        nextQuestions = ''
    else:
        sources = sources + "\n" + retrievedDocs[0].metadata['source']

    outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                "sources": sources, "nextQuestions": nextQuestions, "error": ""}
    
    try:
        insertMessage(sessionId, "Message", "Assistant", 0, 0, outputFinalAnswer, cosmosContainer)
    except Exception as e:
        print("Error inserting message: " + str(e))

    results = {}
    results["values"] = []
    results["values"].append({
                "recordId": 0,
                "data": outputFinalAnswer
                })
    return results
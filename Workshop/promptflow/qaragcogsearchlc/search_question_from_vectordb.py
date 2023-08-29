from promptflow import tool
from langchain.vectorstores import Pinecone
import pinecone
from promptflow.connections import CustomConnection
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import *
from langchain.docstore.document import Document

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
def searchVectorDb(question:str, embeddedQuestion:object, indexType:str, indexNs:str, topK:int, conn:CustomConnection):
  docs = []
  # PineconeKey = conn.PineconeKey
  # PineconeEnv = conn.PineconeEnv
  # VsIndexName = conn.VsIndexName
  SearchService = conn.SearchService
  SearchKey = conn.SearchKey

  if indexType == 'pinecone':
      # pinecone.init(
      #     api_key=PineconeKey,  # find at app.pinecone.io
      #     environment=PineconeEnv  # next to api key in console
      # )
      # vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
      # docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
      # chain = RetrievalQA(combine_documents_chain=qaChain, retriever=docRetriever, return_source_documents=True)
      # llmAnswer = chain({"query": question}, return_only_outputs=True)
      # docs = llmAnswer['source_documents']
      # rawDocs = []
      # for doc in docs:
      #     rawDocs.append(doc.page_content)
      
      # if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
      #     thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
      # elif overrideChain == "refine":
      #     thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
      
      # answer = llmAnswer['result'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
      # modifiedAnswer = answer
      
      # # Followup questions
      # followupChain = RetrievalQA(combine_documents_chain=followupChain, retriever=docRetriever)
      # followupAnswer = followupChain({"query": question}, return_only_outputs=True)
      # nextQuestions = followupAnswer['result'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:').replace('NEXT QUESTIONS:', '').replace('NEXT QUESTIONS', '')
      # sources = ''                
      # if (modifiedAnswer.find("I don't know") >= 0):
      #     sources = ''
      #     nextQuestions = ''
      # else:
      #     sources = sources + "\n" + docs[0].metadata['source']

      # outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
      #         "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
      #             "sources": sources, "nextQuestions": nextQuestions, "error": ""}
      
      # try:
      #     kbData.append({
      #             "id": kbId,
      #             "question": question,
      #             "indexType": indexType,
      #             "indexName": indexNs,
      #             "vectorQuestion": vectorQuestion,
      #             "answer": json.dumps(outputFinalAnswer),
      #         })
          
      #     indexDocs(SearchService, SearchKey, KbIndexName, kbData)
      # except Exception as e:
      #     pass

      # return outputFinalAnswer
      return docs        
  elif indexType == "redis":
      # try:
      #     returnField = ["metadata", "content", "vector_score"]
      #     vectorField = "content_vector"
      #     results = performRedisSearch(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, OpenAiEmbedding, question, indexNs, topK, returnField, vectorField, embeddingModelType)
      #     docs = [
      #             Document(page_content=result.content, metadata=json.loads(result.metadata))
      #             for result in results.docs
      #     ]
      #     rawDocs=[]
      #     for doc in docs:
      #         rawDocs.append(doc.page_content)
      #     answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
      #     answer = answer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
      #     modifiedAnswer = answer

      #     if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
      #         thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
      #     elif overrideChain == "refine":
      #         thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
          
      #     # Followup questions
      #     followupAnswer = followupChain({"input_documents": docs, "question": question}, return_only_outputs=True)
      #     nextQuestions = followupAnswer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:').replace('NEXT QUESTIONS:', '').replace('NEXT QUESTIONS', '')
      #     sources = ''                
      #     if (modifiedAnswer.find("I don't know") >= 0):
      #         sources = ''
      #         nextQuestions = ''
      #     else:
      #         sources = sources + "\n" + docs[0].metadata['source']

          
      #     outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
      #             "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
      #                 "sources": sources, "nextQuestions": nextQuestions, "error": ""}
          
      #     try:
      #         kbData.append({
      #             "id": kbId,
      #             "question": question,
      #             "indexType": indexType,
      #             "indexName": indexNs,
      #             "vectorQuestion": vectorQuestion,
      #             "answer": json.dumps(outputFinalAnswer),
      #         })

      #         indexDocs(SearchService, SearchKey, KbIndexName, kbData)
      #     except Exception as e:
      #         pass

      #     return outputFinalAnswer
                      
      # except Exception as e:
      #     return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}

      return docs
  elif indexType == "cogsearch" or indexType == "cogsearchvs":
      try:
          r = performCogSearch(embeddedQuestion, "contentVector", SearchService, SearchKey, indexType, question, indexNs, topK)
          if r == None:
              docs = [Document(page_content="No Results Found", metadata={"id": "", "source": ""})]
          else :
              docs = [
                  Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                  for doc in r
                  ]
      except Exception as e:
          docs = [Document(page_content="No Results Found" + str(e), metadata={"id": "", "source": ""})]
          pass
      
      return docs
          
import logging, json, os
import azure.functions as func
import openai
from langchain_openai import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
import os
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import RegexParser
#from redis import Redis
from langchain_community.vectorstores.redis import Redis
import numpy as np
from langchain.docstore.document import Document
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch, generateKbEmbeddings, performKbCogVectorSearch, indexDocs
from langchain.prompts import load_prompt
from Utilities.envVars import *
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from Utilities.azureBlob import getLocalBlob, getFullPath
from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI
import uuid
#from Utilities.azureSearch import AzureSearch
from langchain.vectorstores.azuresearch import AzureSearch
from langchain.chains import LLMChain
from langchain import hub
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from operator import itemgetter
from langchain.schema.runnable import RunnableMap
from azure.search.documents.indexes.models import SearchField, SimpleField, SearchableField, SearchFieldDataType

def formatDocs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def QaAnswer(chainType, question, indexType, value, indexNs, approach, overrides):
    logging.info("Calling QaAnswer Open AI")
    answer = ''
    
    try:
        topK = overrides.get("top") or 5
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
        promptTemplate = overrides.get('promptTemplate') or ''
        deploymentType = overrides.get('deploymentType') or 'gpt35'
        searchType = overrides.get('searchType') or 'similarity'

        logging.info("TopK: " + str(topK))
        logging.info("ChainType: " + str(overrideChain))
        logging.info("Temperature: " + str(temperature))
        logging.info("TokenLength: " + str(tokenLength))
        logging.info("EmbeddingModelType: " + str(embeddingModelType))
        logging.info("PromptTemplate: " + str(promptTemplate))
        logging.info("DeploymentType: " + str(deploymentType))
        logging.info("OpenAiChat: " + str(OpenAiChat))
        logging.info("OpenAiChat16k: " + str(OpenAiChat16k))
        logging.info("OpenAiEmbedding: " + str(OpenAiEmbedding))
        logging.info("SearchType: " + str(searchType))
        
        
        thoughtPrompt = ''

        if (embeddingModelType == 'azureopenai'):

            if deploymentType == 'gpt35':
                llm = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat,
                        temperature=temperature,
                        api_key=OpenAiKey,
                        openai_api_type="azure",
                        max_tokens=tokenLength)
            elif deploymentType == "gpt3516k":
                llm = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat16k,
                        temperature=temperature,
                        api_key=OpenAiKey,
                        openai_api_type="azure",
                        max_tokens=tokenLength)
                
            embeddings = AzureOpenAIEmbeddings(azure_endpoint=OpenAiEndPoint, azure_deployment=OpenAiEmbedding, api_key=OpenAiKey, openai_api_type="azure")
            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = ChatOpenAI(temperature=temperature,
                openai_api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=tokenLength)
            embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)


        if (approach == 'rtr'):
            if (overrideChain == "stuff"):
                followupTemplate = """
                Generate three very brief questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <What is Azure?>.
                Try not to repeat questions that have already been asked.  Don't include the context in the answer.

                Return the questions in the following format:
                <>
                <>
                <>
                
                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                {context}

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
            elif (overrideChain == "map_rerank"):
                followupTemplate = """
                Generate three very brief questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <What is Azure?>.
                Try not to repeat questions that have already been asked.  Don't include the context in the answer.

                Return the questions in the following format:
                <>
                <>
                <>
                
                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                {context}

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
            elif (overrideChain == "map_reduce"):
                followupTemplate = """
                Generate three very brief questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <What is Azure?>.
                Try not to repeat questions that have already been asked.  Don't include the context in the answer.

                Return the questions in the following format:
                <>
                <>
                <>
                
                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                {context}

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
            elif (overrideChain == "refine"):
                followupTemplate = """
                Generate three very brief questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <What is Azure?>.
                Try not to repeat questions that have already been asked.  Don't include the context in the answer.

                Return the questions in the following format:
                <>
                <>
                <>
                
                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                {context}

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])


            try:
                # Let's verify if the questions is already answered before and check our KB first before asking LLM
                vectorQuestion = generateKbEmbeddings(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, OpenAiEmbedding, embeddingModelType, question)

                # Let's perform the search on the KB first before asking the question to the model
                kbSearch = performKbCogVectorSearch(vectorQuestion, 'vectorQuestion', SearchService, SearchKey, indexType, indexNs, KbIndexName, 1, ["id", "question", "indexType", "indexName", "answer"])

                logging.info("KB Search Count: " + str(kbSearch.get_count()))

                if kbSearch.get_count() > 0:
                    for s in kbSearch:
                        if s['@search.score'] >= 0.95:
                            logging.info("Found answer from existing KB with search score of " + str(s['@search.score']))
                            #jsonAnswer = ast.literal_eval(json.dumps(s['answer']))
                            jsonAnswer = json.loads(s['answer'])
                            return jsonAnswer
            except Exception as e:
                logging.info("Error in KB Search: " + str(e))
                pass

            kbData = []
            kbId = str(uuid.uuid4())

            if indexType == 'pinecone':
                if promptTemplate == '':
                        prompt = hub.pull("rlm/rag-prompt")
                else:
                        prompt = PromptTemplate(template=promptTemplate, input_variables=["context", "question"])

                vectorDb = PineconeVectorStore.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
                retriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
                logging.info("Pinecone Setup done")

                retrievedDocs = retriever.get_relevant_documents(question)
                rawDocs=[]
                for doc in retrievedDocs:
                    rawDocs.append(doc.page_content)

                ragChain = (
                    {"context": retriever | formatDocs, "question": RunnablePassthrough()}
                    | prompt
                    | llm
                    | StrOutputParser()
                )
                try:
                    modifiedAnswer = ragChain.invoke(question)
                    modifiedAnswer = modifiedAnswer.replace("Answer: ", '')
                    logging.info("Modified Answer: " + modifiedAnswer)
                except Exception as e:
                    logging.info("Error in RAG Chain: " + str(e))
                    pass

                if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
                    thoughtPrompt = prompt.format(question=question, context=rawDocs)
                elif overrideChain == "refine":
                    thoughtPrompt = prompt.format(question=question, context_str=rawDocs)
                
                ragChainFollowup = (
                        {"context": RunnablePassthrough() }
                        | followupPrompt
                        | llm
                        | StrOutputParser()
                    )
                nextQuestions = ragChainFollowup.invoke({"context": ''.join(rawDocs)})
                logging.info("Next Questions: " + nextQuestions)
                sources = '' 
                if (modifiedAnswer.find("I don't know") >= 0):
                    sources = ''
                    nextQuestions = ''
                # else:
                #     sources = sources + "\n" + docs[0].metadata['source']

                outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
                        "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                            "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                
                try:
                    kbData.append({
                            "id": kbId,
                            "question": question,
                            "indexType": indexType,
                            "indexName": indexNs,
                            "vectorQuestion": vectorQuestion,
                            "answer": json.dumps(outputFinalAnswer),
                        })
                    
                    indexDocs(SearchService, SearchKey, KbIndexName, kbData)
                except Exception as e:
                    logging.error("Error in KB Indexing: " + str(e))
                    pass

                return outputFinalAnswer            
            elif indexType == "redis":
                try:
                    if promptTemplate == '':
                        prompt = hub.pull("rlm/rag-prompt")
                    else:
                        prompt = PromptTemplate(template=promptTemplate, input_variables=["context", "question"])

                    indexSchema = {
                        "text": [{"name": "source"}, {"name": "content"}],
                        "vector": [{"name": "content_vector", "dims": 768, "algorithm": "FLAT", "distance_metric": "COSINE"}],
                    }

                    redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort

                    rds = Redis.from_existing_index(
                        embeddings,
                        index_name=indexNs,
                        redis_url=redisUrl,
                        schema=indexSchema
                    )
                    retriever = rds.as_retriever(search_type="similarity", search_kwargs={"k": topK})
                    retrievedDocs = retriever.get_relevant_documents(question)
                    rawDocs=[]
                    for doc in retrievedDocs:
                        rawDocs.append(doc.page_content)

                    ragChain = (
                        {"context": retriever | formatDocs, "question": RunnablePassthrough()}
                        | prompt
                        | llm
                        | StrOutputParser()
                    )
                    try:
                        modifiedAnswer = ragChain.invoke(question)
                        modifiedAnswer = modifiedAnswer.replace("Answer: ", '')
                        logging.info("Modified Answer: " + modifiedAnswer)
                    except Exception as e:
                        logging.info("Error in RAG Chain: " + str(e))
                        pass

                    if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
                        thoughtPrompt = prompt.format(question=question, context=rawDocs)
                    elif overrideChain == "refine":
                        thoughtPrompt = prompt.format(question=question, context_str=rawDocs)
                    
                    ragChainFollowup = (
                        {"context": RunnablePassthrough() }
                        | followupPrompt
                        | llm
                        | StrOutputParser()
                    )
                    nextQuestions = ragChainFollowup.invoke({"context": ''.join(rawDocs)})
                    logging.info("Next Questions: " + nextQuestions)
                    sources = '' 

                    if (modifiedAnswer.find("I don't know") >= 0):
                        sources = ''
                        nextQuestions = ''
                    # else:
                    #     sources = sources + "\n" + docs[0].metadata['source']

                    
                    outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
                            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                                "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                    
                    try:
                        kbData.append({
                            "id": kbId,
                            "question": question,
                            "indexType": indexType,
                            "indexName": indexNs,
                            "vectorQuestion": vectorQuestion,
                            "answer": json.dumps(outputFinalAnswer),
                        })

                        indexDocs(SearchService, SearchKey, KbIndexName, kbData)
                    except Exception as e:
                        logging.info("Error in KB Indexing: " + str(e))
                        pass

                    return outputFinalAnswer
                                
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
            elif indexType == "cogsearch" or indexType == "cogsearchvs":
                try:
                    # fields=[
                    #         SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                    #         SearchableField(name="content", type=SearchFieldDataType.String,
                    #                         searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                    #         SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                    #             vector_search_dimensions=1536, vector_search_profile_name="vectorConfig"),  
                    #         SimpleField(name="metadata", type="Edm.String", filterable=True),
                    # ]
                    # csVectorStore: AzureSearch = AzureSearch(
                    #     azure_search_endpoint=f"https://{SearchService}.search.windows.net",
                    #     azure_search_key=SearchKey,
                    #     index_name=indexNs,
                    #     fields=fields,
                    #     embedding_function=embeddings.embed_query,
                    #     semantic_configuration_name="semanticConfig",
                    # )

                    # # Perform a similarity search
                    # if (searchType == 'similarity'):
                    #     docs = csVectorStore.similarity_search(
                    #         query=question,
                    #         k=topK,
                    #         search_type="similarity",
                    #     )
                    # elif (searchType == 'hybrid'):
                    #     docs = csVectorStore.similarity_search(
                    #         query=question,
                    #         k=topK,
                    #         search_type="similarity",
                    #     )
                    # elif (searchType == 'hybridrerank'):
                    #     docs = csVectorStore.semantic_hybrid_search(
                    #         query=question,
                    #         k=topK
                    #     )

                    # logging.info("CogSearch Results: " + str(len(docs)))
                    # rawDocs=[]
                    # for doc in docs:
                    #     rawDocs.append(doc.page_content)
                    
                    # answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    # answer = answer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
                    # modifiedAnswer = answer

                    rawDocs=[]
                    csVectorStore: AzureSearch = AzureSearch(
                        azure_search_endpoint=f"https://{SearchService}.search.windows.net",
                        azure_search_key=SearchKey,
                        index_name=indexNs,
                        embedding_function=embeddings.embed_query,
                        semantic_configuration_name="semanticConfig",
                    )
                    retriever = csVectorStore.as_retriever(search_type=searchType, search_kwargs={"k": 3})
                    retrievedDocs = retriever.get_relevant_documents(question)
                    for doc in retrievedDocs:
                        rawDocs.append(doc.page_content)
                    
                    if promptTemplate == '':
                        prompt = hub.pull("rlm/rag-prompt")
                    else:
                        prompt = PromptTemplate(template=promptTemplate, input_variables=["context", "question"])
                    
                    # ragChainFromDocs = (
                    #     {
                    #         "context": lambda input: formatDocs(input["documents"]),
                    #         "question": itemgetter("question"),
                    #     }
                    #     | prompt
                    #     | llm
                    #     | StrOutputParser()
                    # )
                    # ragChainWithSource = RunnableMap(
                    #     {"documents": retriever, "question": RunnablePassthrough()}
                    # ) | {
                    #     "documents": lambda input: [doc.metadata for doc in input["documents"]],
                    #     "answer": ragChainFromDocs,
                    # }
                    ragChain = (
                        {"context": retriever | formatDocs, "question": RunnablePassthrough()}
                        | prompt
                        | llm
                        | StrOutputParser()
                    )
                    try:
                        #modifiedAnswer = ragChainWithSource.invoke(question)['answer']
                        modifiedAnswer = ragChain.invoke(question)
                        modifiedAnswer = modifiedAnswer.replace("Answer: ", '')
                        logging.info("Modified Answer: " + modifiedAnswer)
                    except Exception as e:
                        logging.info("Error in RAG Chain: " + str(e))
                        pass

                    if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
                        thoughtPrompt = prompt.format(question=question, context=rawDocs)
                    elif overrideChain == "refine":
                        thoughtPrompt = prompt.format(question=question, context_str=rawDocs)
                    
                   
                    # llmChain = LLMChain(prompt=followupPrompt, llm=llm)
                    # nextQuestions = llmChain.predict(context=rawDocs)
                    ragChainFollowup = (
                        {"context": RunnablePassthrough() }
                        | followupPrompt
                        | llm
                        | StrOutputParser()
                    )
                    nextQuestions = ragChainFollowup.invoke({"context": ''.join(rawDocs)})
                    logging.info("Next Questions: " + nextQuestions)
                    sources = ''                
                    if (modifiedAnswer.find("I don't know") >= 0):
                        sources = ''
                        nextQuestions = ''
                    # else:
                    #     sources = sources + "\n" + docs[0].metadata['source']

                    outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
                            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                                "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                    
                    try:
                        kbData.append({
                            "id": kbId,
                            "question": question,
                            "indexType": indexType,
                            "indexName": indexNs,
                            "vectorQuestion": vectorQuestion,
                            "answer": json.dumps(outputFinalAnswer),
                        })

                        indexDocs(SearchService, SearchKey, KbIndexName, kbData)
                    except Exception as e:
                        logging.info("Error in KB Indexing: " + str(e))
                        pass

                    return outputFinalAnswer
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Cognitive Search Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
            elif indexType == "csv":
                downloadPath = getLocalBlob(OpenAiDocConnStr, OpenAiDocContainer, '', indexNs)
                agent = create_csv_agent(llm, downloadPath, verbose=True)
                answer = agent.run(question)
                sources = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, os.path.basename(downloadPath))
                return {"data_points": '', "answer": answer, 
                            "thoughts": '',
                                "sources": sources, "nextQuestions": '', "error": ""}


            elif indexType == 'milvus':
                answer = "{'answer': 'TBD', 'sources': ''}"
                return answer
        elif approach == 'rrr':
            answer = "{'answer': 'TBD', 'sources': ''}"
            return answer
        elif approach == 'rca':
            answer = "{'answer': 'TBD', 'sources': ''}"
            return answer
    

    except Exception as e:
      logging.error("Error in QaAnswer Open AI : " + str(e))
      return {"data_points": "", "answer": "Exception during finding answers - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}

    #return answer

def ComposeResponse(chainType, question, indexType, jsonData, indexNs):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(chainType, question, indexType, value, indexNs)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(chainType, question, indexType, record, indexNs):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:
        assert ('data' in record), "'data' field is required."
        data = record['data']
        assert ('text' in data), "'text' field is required in 'data' object."

    except KeyError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "KeyError:" + error.args[0] }   ]
            })
    except AssertionError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "AssertionError:" + error.args[0] }   ]
            })
    except SystemError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "SystemError:" + error.args[0] }   ]
            })

    try:
        # Getting the items from the values/data/text
        value = data['text']
        approach = data['approach']
        overrides = data['overrides']

        answer = QaAnswer(chainType, question, indexType, value, indexNs, approach, overrides)
        return ({
            "recordId": recordId,
            "data": answer
            })

    except Exception as error:
        logging.error("Error in Transform Value: " + str(error))
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        chainType = req.params.get('chainType')
        question = req.params.get('question')
        indexType = req.params.get('indexType')
        indexNs = req.params.get('indexNs')
        logging.info("chainType: " + chainType)
        logging.info("question: " + question)
        logging.info("indexType: " + indexType)
        logging.info("indexNs: " + indexNs)

        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        try:
            if len(PineconeKey) > 10 and len(PineconeEnv) > 10:
                # pinecone.init(
                #     api_key=PineconeKey,  # find at app.pinecone.io
                #     environment=PineconeEnv  # next to api key in console
                # )
                os.environ["PINECONE_API_KEY"] = PineconeKey
                pc = Pinecone(api_key=PineconeKey)
        except Exception as e:
            logging.error("Error in Pinecone Init: " + str(e))
            pass
        result = ComposeResponse(chainType, question, indexType, body, indexNs)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

import datetime
import logging, json, os
import uuid
import azure.functions as func
from langchain_openai import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
import os
from openai import OpenAI, AzureOpenAI
from pinecone import Pinecone
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.docstore.document import Document
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch
from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate
from Utilities.envVars import *
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from Utilities.azureBlob import getLocalBlob, getFullPath
from azure.cosmos import CosmosClient, PartitionKey
from langchain_community.callbacks.manager import get_openai_callback
from langchain.chains.question_answering import load_qa_chain
from langchain.output_parsers import RegexParser
from langchain.chains import RetrievalQA
from typing import Any, Sequence
from Utilities.modelHelper import numTokenFromMessages, getTokenLimit
from Utilities.messageBuilder import MessageBuilder
from langchain.vectorstores.azuresearch import AzureSearch
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
)
from langchain.chains import LLMChain
from langchain import hub
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores.redis import Redis

def formatDocs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        indexNs = req.params.get('indexNs')
        indexType = req.params.get('indexType')
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        if len(PineconeKey) > 10 and len(PineconeEnv) > 10:
            os.environ["PINECONE_API_KEY"] = PineconeKey
            pc = Pinecone(api_key=PineconeKey)
        #     pinecone.init(
        #         api_key=PineconeKey,  # find at app.pinecone.io
        #         environment=PineconeEnv  # next to api key in console
        #     )
        result = ComposeResponse(body, indexNs, indexType)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(jsonData, indexNs, indexType):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(value, indexNs, indexType)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def getMessagesFromHistory(systemPrompt: str, modelId: str, history: Sequence[dict[str, str]], 
                           userConv: str, fewShots = [], maxTokens: int = 4096):
        #messageBuilder = MessageBuilder(systemPrompt, modelId)
        messages = []
        messages.append({'role': 'system', 'content': systemPrompt})
        tokenLength = numTokenFromMessages(messages[-1], modelId)

        # Add examples to show the chat what responses we want. It will try to mimic any responses and make sure they match the rules laid out in the system message.
        for shot in fewShots:
            messages.insert(1, {'role': shot.get('role'), 'content': shot.get('content')})

        userContent = userConv
        appendIndex = len(fewShots) + 1

        messages.insert(appendIndex, {'role': "user", 'content': userContent})

        for h in reversed(history[:-1]):
            if h.get("bot"):
                messages.insert(appendIndex, {'role': "assistant", 'content': h.get('bot')})
            messages.insert(appendIndex, {'role': "user", 'content': h.get('user')})
            tokenLength += numTokenFromMessages(messages[appendIndex], modelId)
            if tokenLength > maxTokens:
                break

        return messages

def getChatHistory(history, includeLastTurn=True, maxTokens=1000) -> str:
    historyText = ""
    for h in reversed(history if includeLastTurn else history[:-1]):
        historyText = """<|im_start|>user""" +"\n" + h["user"] + "\n" + """<|im_end|>""" + "\n" + """<|im_start|>assistant""" + "\n" + (h.get("bot") + """<|im_end|>""" if h.get("bot") else "") + "\n" + historyText
        if len(historyText) > maxTokens*4:
            break
    return historyText

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

def GetRrrAnswer(history, approach, overrides, indexNs, indexType):
    embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
    topK = overrides.get("top") or 5
    temperature = overrides.get("temperature") or 0.3
    tokenLength = overrides.get('tokenLength') or 500
    firstSession = overrides.get('firstSession') or False
    sessionId = overrides.get('sessionId')
    promptTemplate = overrides.get('promptTemplate') or ''
    deploymentType = overrides.get('deploymentType') or 'gpt35'
    overrideChain = overrides.get("chainType") or 'stuff'
    searchType = overrides.get('searchType') or 'similarity'
    pc = Pinecone(api_key=PineconeKey)


    logging.info("Search for Top " + str(topK))
    try:
        cosmosClient = CosmosClient(url=CosmosEndpoint, credential=CosmosKey)
        cosmosDb = cosmosClient.create_database_if_not_exists(id=CosmosDatabase)
        cosmosKey = PartitionKey(path="/sessionId")
        cosmosContainer = cosmosDb.create_container_if_not_exists(id=CosmosContainer, partition_key=cosmosKey, offer_throughput=400)
    except Exception as e:
        logging.info("Error connecting to CosmosDB: " + str(e))

    lastQuestion = history[-1]["user"]
    totalTokens = 0

    # If we are getting the new session, let's insert the data into CosmosDB
    try:
        if firstSession:
            sessionInfo = overrides.get('session') or ''
            session = json.loads(sessionInfo)
            cosmosContainer.upsert_item(session)
            logging.info(session)
    except Exception as e:
        logging.info("Error inserting session into CosmosDB: " + str(e))


    systemTemplate = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base.
    Generate a search query based on the conversation and the new question.
    The search query should be optimized to find the answer to the question in the knowledge base.
    If you cannot generate a search query, return just the number 0.

    """

    gptModel = "gpt-35-turbo"
    if (embeddingModelType == 'azureopenai'):
        if deploymentType == 'gpt35':
            gptModel = "gpt-35-turbo"
        elif deploymentType == 'gpt3516k':
            gptModel = "gpt-35-turbo-16k"
    elif embeddingModelType == 'openai':
        if deploymentType == 'gpt35':
            gptModel = "gpt-3.5-turbo"
        elif deploymentType == 'gpt3516k':
            gptModel = "gpt-3.5-turbo-16k"

    tokenLimit = getTokenLimit(gptModel)
    # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
    messages = getMessagesFromHistory(
            systemTemplate,
            gptModel,
            history,
            'Generate search query for: ' + lastQuestion,
            [],
            tokenLimit - len('Generate search query for: ' + lastQuestion) - tokenLength
            )
    
    if (embeddingModelType == 'azureopenai'):

        embeddings = AzureOpenAIEmbeddings(azure_endpoint=OpenAiEndPoint, azure_deployment=OpenAiEmbedding, api_key=OpenAiKey, openai_api_type="azure")
        if deploymentType == 'gpt35':
            llmChat = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat,
                        temperature=temperature,
                        api_key=OpenAiKey,
                        max_tokens=tokenLength)
            
            client = AzureOpenAI(
                    api_key = OpenAiKey,  
                    api_version = OpenAiVersion,
                    azure_endpoint = OpenAiEndPoint
                    )
            completion = client.chat.completions.create(
                model=OpenAiChat, 
                messages=messages,
                temperature=0.0,
                max_tokens=32,
                n=1)
                        
        elif deploymentType == "gpt3516k":
            llmChat = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat16k,
                        temperature=temperature,
                        api_key=OpenAiKey,
                        max_tokens=tokenLength)
            
            client = AzureOpenAI(
                    api_key = OpenAiKey,  
                    api_version = OpenAiVersion,
                    azure_endpoint = OpenAiEndPoint
                    )
            completion = client.chat.completions.create(
                model=OpenAiChat16k, 
                messages=messages,
                temperature=0.0,
                max_tokens=32,
                n=1)
            
        logging.info("LLM Setup done")

    elif embeddingModelType == "openai":
        llmChat = ChatOpenAI(temperature=0.3,
                api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=1000)
        embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)

        client = OpenAI(api_key=OpenAiApiKey)
        completion = client.chat.completions.create(
                    model=OpenAiChat, 
                    messages=messages,
                    temperature=0.0,
                    max_tokens=32,
                    n=1)
    try:
        # userToken = completion.usage.total_tokens
        # totalTokens = totalTokens + userToken
        if len(history) > 1:
            q = completion.choices[0].message.content
        else:
            q = lastQuestion
            
        logging.info("Question " + str(q))
        if q.strip() == "0":
            q = lastQuestion

        if (q == ''):
            q = lastQuestion

        try:
            insertMessage(sessionId, "Message", "User", 0, 0, lastQuestion, cosmosContainer)
        except Exception as e:
            logging.info("Error inserting session into CosmosDB: " + str(e))
        

    except Exception as e:
        q = lastQuestion
        logging.info(e)

    try:
        logging.info("Execute step 2")
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
        logging.info("Final Prompt created")
        if indexType == 'pinecone':
            rawDocs=[]
            vectorDb = PineconeVectorStore.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
            retriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
            logging.info("Pinecone Setup done")
            retrievedDocs = retriever.get_relevant_documents(q)
            for doc in retrievedDocs:
                rawDocs.append(doc.page_content)
            
            if promptTemplate == '':
                prompt = hub.pull("rlm/rag-prompt")
            else:
                prompt = PromptTemplate(template=promptTemplate, input_variables=["context", "question"])
        
            if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
                thoughtPrompt = prompt.format(question=q, context=rawDocs)
            elif overrideChain == "refine":
                thoughtPrompt = prompt.format(question=q, context_str=rawDocs)

            with get_openai_callback() as cb:
                ragChain = (
                    {"context": retriever | formatDocs, "question": RunnablePassthrough()}
                    | prompt
                    | llmChat
                    | StrOutputParser()
                )
                try:
                    modifiedAnswer = ragChain.invoke(q)
                    modifiedAnswer = modifiedAnswer.replace("Answer: ", '')
                except Exception as e:
                    logging.info("Error in RAG Chain: " + str(e))
                    pass

                ragChainFollowup = (
                        {"context": RunnablePassthrough() }
                        | followupPrompt
                        | llmChat
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

                response = {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                        "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                        "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                        "nextQuestions": nextQuestions.replace('Next Questions:', '').replace('- ', ''), "error": ""}
                try:
                    insertMessage(sessionId, "Message", "Assistant", totalTokens, cb.total_tokens, response, cosmosContainer)
                except Exception as e:
                    logging.info("Error inserting message: " + str(e))

                return response
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
                retrievedDocs = retriever.get_relevant_documents(q)
                rawDocs=[]
                for doc in retrievedDocs:
                    rawDocs.append(doc.page_content)

                if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
                    thoughtPrompt = prompt.format(question=q, context=rawDocs)
                elif overrideChain == "refine":
                    thoughtPrompt = prompt.format(question=q, context_str=rawDocs)

                with get_openai_callback() as cb:
                    ragChain = (
                        {"context": retriever | formatDocs, "question": RunnablePassthrough()}
                        | prompt
                        | llmChat
                        | StrOutputParser()
                    )
                    try:
                        modifiedAnswer = ragChain.invoke(q)
                        modifiedAnswer = modifiedAnswer.replace("Answer: ", '')
                        logging.info("Modified Answer: " + modifiedAnswer)
                    except Exception as e:
                        logging.info("Error in RAG Chain: " + str(e))
                        pass

                    ragChainFollowup = (
                        {"context": RunnablePassthrough() }
                        | followupPrompt
                        | llmChat
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

                    response = {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                        "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                        "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                        "nextQuestions": nextQuestions.replace('Next Questions:', '').replace('- ', ''), "error": ""}
                    try:
                        insertMessage(sessionId, "Message", "Assistant", totalTokens, cb.total_tokens, response, cosmosContainer)
                    except Exception as e:
                        logging.info("Error inserting message: " + str(e))

                    return response
            except Exception as e:
                return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "",
                        "sources": '', "nextQuestions": '', "error": str(e)}
        elif indexType == "cogsearch" or indexType == "cogsearchvs":
            
            rawDocs=[]
            csVectorStore: AzureSearch = AzureSearch(
                azure_search_endpoint=f"https://{SearchService}.search.windows.net",
                azure_search_key=SearchKey,
                index_name=indexNs,
                embedding_function=embeddings.embed_query,
                semantic_configuration_name="semanticConfig",
            )
            retriever = csVectorStore.as_retriever(search_type=searchType, search_kwargs={"k": 3})
            retrievedDocs = retriever.get_relevant_documents(q)
            for doc in retrievedDocs:
                rawDocs.append(doc.page_content)
            
            if promptTemplate == '':
                prompt = hub.pull("rlm/rag-prompt")
            else:
                prompt = PromptTemplate(template=promptTemplate, input_variables=["context", "question"])


            if overrideChain == "stuff" or overrideChain == "map_rerank" or overrideChain == "map_reduce":
                thoughtPrompt = prompt.format(question=q, context=rawDocs)
            elif overrideChain == "refine":
                thoughtPrompt = prompt.format(question=q, context_str=rawDocs)
            
            with get_openai_callback() as cb:
                ragChain = (
                    {"context": retriever | formatDocs, "question": RunnablePassthrough()}
                    | prompt
                    | llmChat
                    | StrOutputParser()
                )
                try:
                    modifiedAnswer = ragChain.invoke(q)
                    modifiedAnswer = modifiedAnswer.replace("Answer: ", '')
                except Exception as e:
                    logging.info("Error in RAG Chain: " + str(e))
                    pass

                ragChainFollowup = (
                        {"context": RunnablePassthrough() }
                        | followupPrompt
                        | llmChat
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

                response = {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                    "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                    "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                    "nextQuestions": nextQuestions.replace('Next Questions:', '').replace('- ', ''), "error": ""}
                try:
                    insertMessage(sessionId, "Message", "Assistant", totalTokens, cb.total_tokens, response, cosmosContainer)
                except Exception as e:
                    logging.info("Error inserting message: " + str(e))

                return response
        elif indexType == 'milvus':
            answer = "{'answer': 'TBD', 'sources': ''}"
            return answer
    except Exception as e:
        return {"data_points": "", "answer": "Error : " + str(e), "thoughts": "",
                "sources": '', "nextQuestions": '', "error": str(e)}

def GetAnswer(history, approach, overrides, indexNs, indexType):
    logging.info("Getting ChatGpt Answer")
    try:
      if (approach == 'rrr'):
        r = GetRrrAnswer(history, approach, overrides, indexNs, indexType)
      else:
          return json.dumps({"error": "unknown approach"})
      return r
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(record, indexNs, indexType):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:
        assert ('data' in record), "'data' field is required."
        data = record['data']
        #assert ('text' in data), "'text' field is required in 'data' object."

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
        history = data['history']
        approach = data['approach']
        overrides = data['overrides']

        summaryResponse = GetAnswer(history, approach, overrides, indexNs, indexType)
        return ({
            "recordId": recordId,
            "data": summaryResponse
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

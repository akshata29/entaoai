import logging, json, os
import azure.functions as func
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.docstore.document import Document
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate

OpenAiKey = os.environ['OpenAiKey']
OpenAiEndPoint = os.environ['OpenAiEndPoint']
OpenAiVersion = os.environ['OpenAiVersion']
OpenAiDavinci = os.environ['OpenAiDavinci']
OpenAiService = os.environ['OpenAiService']
OpenAiDocStorName = os.environ['OpenAiDocStorName']
OpenAiDocStorKey = os.environ['OpenAiDocStorKey']
OpenAiDocConnStr = f"DefaultEndpointsProtocol=https;AccountName={OpenAiDocStorName};AccountKey={OpenAiDocStorKey};EndpointSuffix=core.windows.net"
OpenAiDocContainer = os.environ['OpenAiDocContainer']
PineconeEnv = os.environ['PineconeEnv']
PineconeKey = os.environ['PineconeKey']
VsIndexName = os.environ['VsIndexName']
OpenAiChat = os.environ['OpenAiChat']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
SearchService = os.environ['SearchService']
SearchKey = os.environ['SearchKey']


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
        pinecone.init(
            api_key=PineconeKey,  # find at app.pinecone.io
            environment=PineconeEnv  # next to api key in console
        )
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

def getChatHistory(history, includeLastTurn=True, maxTokens=1000) -> str:
    historyText = ""
    for h in reversed(history if includeLastTurn else history[:-1]):
        historyText = """<|im_start|>user""" +"\n" + h["user"] + "\n" + """<|im_end|>""" + "\n" + """<|im_start|>assistant""" + "\n" + (h.get("bot") + """<|im_end|>""" if h.get("bot") else "") + "\n" + historyText
        if len(historyText) > maxTokens*4:
            break
    return historyText

def parseResponse(fullAnswer, sources):
    modifiedAnswer = fullAnswer
    if (len(sources) > 0):
        thoughts = sources.replace("NEXT QUESTIONS:", 'Next Questions:')
        try:
            sources = thoughts[:thoughts.index("Next Questions:")]
            nextQuestions = thoughts[thoughts.index("Next Questions:"):]
        except:
            try:
                sources = sources[:sources.index("<<")]
                nextQuestions = sources[sources.index("<<"):]
            except:
                sources = sources
                nextQuestions = ''
                if len(nextQuestions) <= 0:
                    try:
                        modifiedAnswer = fullAnswer[:fullAnswer.index("Next Questions:")]
                        nextQuestions = fullAnswer[fullAnswer.index("Next Questions:"):]
                        if len(nextQuestions) <=0:
                            modifiedAnswer = fullAnswer[:fullAnswer.index("<<")]
                            nextQuestions = thoughts[thoughts.index("<<"):]
                    except:
                        nextQuestions = ''

        return modifiedAnswer.replace("Answer: ", ''), sources, nextQuestions
    else :
        try:
            if fullAnswer.index("SOURCES:") > 0:
                modifiedAnswer = fullAnswer[:fullAnswer.index("SOURCES:")]
                thoughts = fullAnswer[fullAnswer.index("SOURCES:"):]
                thoughts = thoughts.replace("NEXT QUESTIONS:", 'Next Questions:')
                try:
                    sources = thoughts[:thoughts.index("Next Questions:")]
                    nextQuestions = thoughts[thoughts.index("Next Questions:"):]
                except:
                    try:
                        sources = thoughts[:thoughts.index("<<")]
                        nextQuestions = thoughts[thoughts.index("<<"):]
                    except:
                        sources = thoughts
                        nextQuestions = ''
                        if len(nextQuestions) <= 0:
                            try:
                                modifiedAnswer = fullAnswer[:fullAnswer.index("Next Questions:")]
                                nextQuestions = fullAnswer[fullAnswer.index("Next Questions:"):]
                                if len(nextQuestions) <=0:
                                    modifiedAnswer = fullAnswer[:fullAnswer.index("<<")]
                                    nextQuestions = thoughts[thoughts.index("<<"):]
                            except:
                                nextQuestions = ''

                return modifiedAnswer.replace("Answer: ", ''), sources, nextQuestions
            else:
                return fullAnswer, '', ''
        except:
            try:
                modifiedAnswer = fullAnswer[:fullAnswer.index("Next Questions:")]
                nextQuestions = fullAnswer[fullAnswer.index("Next Questions:"):]
            except:
                try:
                    modifiedAnswer = fullAnswer[:fullAnswer.index("<<")]
                    nextQuestions = fullAnswer[fullAnswer.index("<<"):]
                except:
                    modifiedAnswer = fullAnswer
                    nextQuestions = ''
            return modifiedAnswer, '', ''
        
def GetRrrAnswer(history, approach, overrides, indexNs, indexType):
    qaPromptTemplate = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base.
    Generate a search query based on the conversation and the new question.
    The search query should be optimized to find the answer to the question in the knowledge base.

    Chat History:
    {chat_history}

    Question:
    {question}

    Search query:
    """

    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    baseUrl = f"https://{OpenAiService}.openai.azure.com"

    topK = overrides.get("top") or 5
    temperature = overrides.get("temperature") or 0.3
    tokenLength = overrides.get('tokenLength') or 500
    logging.info("Search for Top " + str(topK))
    # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
    optimizedPrompt = qaPromptTemplate.format(chat_history=getChatHistory(history, includeLastTurn=False),
                                              question=history[-1]["user"])

    #.info("Optimized Prompt" + optimizedPrompt)

    try:
        completion = openai.Completion.create(
            engine=OpenAiDavinci,
            prompt=optimizedPrompt,
            temperature=temperature,
            max_tokens=32,
            #max_tokens=tokenLength,
            n=1,
            stop=["\n"])
        q = completion.choices[0].text
        logging.info("Question " + completion.choices[0].text)
        if (q == ''):
            q = history[-1]["user"]
    except Exception as e:
        q = history[-1]["user"]
        logging.info(e)


    logging.info("Execute step 2")
    # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query
    embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)

    llmChat = AzureChatOpenAI(
                openai_api_base=baseUrl,
                openai_api_version="2023-03-15-preview",
                deployment_name=OpenAiChat,
                temperature=temperature,
                openai_api_key=OpenAiKey,
                openai_api_type="azure",
                max_tokens=tokenLength)
    
    combinePromptTemplate = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
          If you don't know the answer, just say that you don't know. Don't try to make up an answer.
          ALWAYS return a "SOURCES" section as part in your answer.

          QUESTION: {question}
          =========
          {summaries}
          =========

          After finding the answer, generate three very brief next questions that the user would likely ask next.
          Use angle brackets to reference the next questions, e.g. <Is there a more details on that?>.
          Try not to repeat questions that have already been asked.
          next questions should come after 'SOURCES' section
          ALWAYS return a "NEXT QUESTIONS" part in your answer.
          """
    
    combinePrompt = PromptTemplate(
        template=combinePromptTemplate, input_variables=["summaries", "question"]
    )

    logging.info("Final Prompt created")
    if indexType == 'pinecone':
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
        logging.info("Pinecone Setup done for indexName : " + indexNs)
        qaChain = load_qa_with_sources_chain(llmChat, chain_type="stuff", 
                                                prompt=combinePrompt)
        chain = RetrievalQAWithSourcesChain(combine_documents_chain=qaChain, retriever=docRetriever, 
                                            return_source_documents=True)
        historyText = getChatHistory(history, includeLastTurn=False)
        answer = chain({"question": q, "summaries": historyText}, return_only_outputs=True)
        docs = answer['source_documents']
        rawDocs = []
        for doc in docs:
            rawDocs.append(doc.page_content)
        thoughtPrompt = combinePrompt.format(question=q, summaries=rawDocs)
        fullAnswer = answer['answer'].replace('ANSWER:', '').replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("NEXT QUESTIONS:", 'Next Questions:')
        sources = answer['sources'].replace("NEXT QUESTIONS:", 'Next Questions:')
        modifiedAnswer, sources, nextQuestions = parseResponse(fullAnswer, sources)
        if ((modifiedAnswer.find("I don't know") >= 0) or (modifiedAnswer.find("I'm not sure") >= 0)):
            sources = ''
            nextQuestions = ''

        logging.info("Sources: " + sources)
        logging.info('Next Questions: ' + nextQuestions)

        return {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                "nextQuestions": nextQuestions.replace('Next Questions:', '').replace('- ', ''), "error": ""}
    elif indexType == "redis":
        try:
            returnField = ["metadata", "content", "vector_score"]
            vectorField = "content_vector"
            results = performRedisSearch(q, indexNs, topK, returnField, vectorField)
            docs = [
                    Document(page_content=result.content, metadata=json.loads(result.metadata))
                    for result in results.docs
            ]
            rawDocs = []
            for doc in docs:
                rawDocs.append(doc.page_content)
            thoughtPrompt = combinePrompt.format(question=q, summaries=rawDocs)
            qaChain = load_qa_with_sources_chain(llmChat,
                chain_type="stuff", prompt=combinePrompt)
            answer = qaChain({"input_documents": docs, "question": q}, return_only_outputs=True)
            fullAnswer = answer['output_text'].replace('ANSWER:', '').replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("NEXT QUESTIONS:", 'Next Questions:')
            modifiedAnswer, sources, nextQuestions = parseResponse(fullAnswer, '')
            if ((modifiedAnswer.find("I don't know") >= 0) or (modifiedAnswer.find("I'm not sure") >= 0)):
                sources = ''
                nextQuestions = ''
            return {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                "nextQuestions": nextQuestions.replace('Next Questions:', '').replace('- ', ''), "error": ""}
        except Exception as e:
            return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "",
                    "sources": '', "nextQuestions": '', "error": str(e)}
    elif indexType == "cogsearch":
        r = performCogSearch(q, indexNs, topK)
        if r == None:
                docs = [Document(page_content="No results found")]
        else :
            docs = [
                Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                for doc in r
                ]
        
        rawDocs = []
        for doc in docs:
            rawDocs.append(doc.page_content)
        thoughtPrompt = optimizedPrompt.format(question=q, summaries=rawDocs)
        qaChain = load_qa_with_sources_chain(llmChat,
                chain_type="stuff", prompt=combinePrompt)
        answer = qaChain({"input_documents": docs, "question": q}, return_only_outputs=True)
        fullAnswer = answer['output_text'].replace('ANSWER:', '').replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("NEXT QUESTIONS:", 'Next Questions:')
        modifiedAnswer, sources, nextQuestions = parseResponse(fullAnswer, '')
        if ((modifiedAnswer.find("I don't know") >= 0) or (modifiedAnswer.find("I'm not sure") >= 0)):
            sources = ''
            nextQuestions = ''

        logging.info(sources)
        return {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
            "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
            "nextQuestions": nextQuestions.replace('Next Questions:', '').replace('- ', ''), "error": ""}

    elif indexType == 'milvus':
        answer = "{'answer': 'TBD', 'sources': ''}"
        return answer


    # if indexType == 'pinecone':
    #     vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings)
    #     logging.info("Pinecone Setup done to search against - " + indexNs + " for question " + q)
    #     docs = vectorDb.similarity_search(q, k=topK, namespace=indexNs)
    #     logging.info("Executed Index and found " + str(len(docs)))
    # elif indexType == "redis":
    #     try:
    #         #vectorDb =  Redis.from_existing_index(embeddings, index_name=indexNs, kwargs={'redis_url': redisUrl}),
    #         #logging.info("Redis Setup done")
    #         #docs = vectorDb.similarity_search(q, k=5)
    #         returnField = ["metadata", "content", "vector_score"]
    #         vectorField = "content_vector"
    #         results = performRedisSearch(q, indexNs, topK, returnField, vectorField)
    #         docs = [
    #                 Document(page_content=result.content, metadata=json.loads(result.metadata))
    #                 for result in results.docs
    #         ]
    #     except Exception as e:
    #         return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
    # elif indexType == "cogsearch":
    #     r = performCogSearch(q, indexNs, topK)
    #     if r == None:
    #             docs = [Document(page_content="No results found")]
    #     else :
    #         docs = [
    #             Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
    #             for doc in r
    #             ]
    # elif indexType == 'milvus':
    #     docs = []

    # rawDocs = []
    # for doc in docs:
    #   rawDocs.append(doc.page_content)

    # # Allow client to replace the entire prompt, or to inject into the exiting prompt using >>>
    # finalPrompt = promptPrefix.format(injected_prompt="", sources=rawDocs,
    #                                   chat_history=getChatHistory(history),
    #                                   follow_up_questions_prompt=followupQaPromptTemplate)
    # logging.info("Final Prompt created")
    # # STEP 3: Generate a contextual and content specific answer using the search results and chat history
    # try:
    #     completion = openai.Completion.create(
    #         engine=OpenAiChat,
    #         prompt=finalPrompt,
    #         temperature=temperature,
    #         max_tokens=tokenLength,
    #         n=1,
    #         stop=["<|im_end|>", "<|im_start|>"])
    #     logging.info(completion.choices[0].text)
    # except Exception as e:
    #     logging.error(e)
    #     return {"data_points": "", "answer": "Working on fixing Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
    
    # return {"data_points": rawDocs, "answer": completion.choices[0].text, "thoughts": f"Searched for:<br>{q}<br><br>Prompt:<br>" + finalPrompt.replace('\n', '<br>')}

def GetAnswer(history, approach, overrides, indexNs, indexType):
    logging.info("Getting Answer")
    try:
      logging.info("Loading OpenAI")
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

import logging, json, os
import azure.functions as func
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.llms.openai import AzureOpenAI, OpenAI
from redis import Redis
import numpy as np
from langchain.docstore.document import Document
from langchain import LLMChain, PromptTemplate
from langchain.chains import RetrievalQAWithSourcesChain, VectorDBQAWithSourcesChain
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch
from Utilities.envVars import *
from langchain.agents import create_csv_agent
from Utilities.azureBlob import getLocalBlob, getFullPath

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
        question = req.params.get('question')
        indexName = req.params.get('indexName')
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
        result = ComposeResponse(body, indexNs, indexType, question, indexName)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(jsonData, indexNs, indexType, question, indexName):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(value, indexNs, indexType, question, indexName)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

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
        
def getChatHistory(history, includeLastTurn=True, maxTokens=1000) -> str:
    historyText = []
    
    for h in reversed(history if includeLastTurn else history[:-1]):
        user = h['user']
        bot = (h.get("bot") if h.get("bot") else "")
        historyText.append((user, bot))
        if len(historyText) > maxTokens*4:
            break
    return historyText

def GetRrrAnswer(history, approach, overrides, indexNs, indexType, question, indexName):

    qaTemplate = """You are an AI assistant for the all questions on document.
    I am still improving my Knowledge base. The documentation is located from document. You have a deep understanding of the document.
    You are given the following extracted parts of a long document and a question. Provide an answer with a hyperlink to the PDF or with a code block directly from the PDF. You should only use hyperlinks that are explicitly listed as a source in the context. Do NOT make up a hyperlink that is not listed. If you don't know the answer, just say 'Hmm, I'm not sure.' Don't try to make up an answer. If the question is not about
    the information in document, politely inform them that you are tuned to only answer questions about information in the document.
    
    ========= 
    {context} 
    Question: {question} 
    ========= 
    """

    combinePromptTemplate = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
          If you don't know the answer, just say that you don't know. Don't try to make up an answer.
          ALWAYS return a "SOURCES" section as part in your answer.

          QUESTION: {question}
          =========
          {summaries}
          =========

          After finding the answer, generate three very brief follow-up questions that the user would likely ask next.
          Use double angle brackets to reference the questions, e.g. <Is there a more details on that?>.
          Try not to repeat questions that have already been asked.
          Generate 'Next Questions' before the list of questions.
          Next Questions should come after 'SOURCES' section
          """
    
    combinePrompt = PromptTemplate(
        template=combinePromptTemplate, input_variables=["summaries", "question"]
    )

    topK = overrides.get("top") or 5
    embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
    temperature = overrides.get("temperature") or 0.3
    tokenLength = overrides.get('tokenLength') or 500
    
    logging.info("Search for Top " + str(topK))

    qaPrompt = PromptTemplate(
              template=qaTemplate, input_variables=["question", "context"]
          )

    try:
        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    max_tokens=tokenLength,
                    batch_size=10, 
                    max_retries=12)

            logging.info("LLM Setup done")
            embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = OpenAI(temperature=temperature,
                    openai_api_key=OpenAiApiKey,
                    max_tokens=tokenLength)
            embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)

        
        if indexType == 'pinecone':
            vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
            docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
            logging.info("Pinecone Setup done for indexName : " + indexNs)
            qaChain = load_qa_with_sources_chain(llm, chain_type="map_reduce", 
                                                 question_prompt=qaPrompt, combine_prompt=combinePrompt)
            chain = RetrievalQAWithSourcesChain(combine_documents_chain=qaChain, retriever=docRetriever, 
                                                return_source_documents=True)
            historyText = getChatHistory(history, includeLastTurn=False)
            answer = chain({"question": question, "chat_history": historyText}, return_only_outputs=True)
            docs = answer['source_documents']
            rawDocs = []
            for doc in docs:
                rawDocs.append(doc.page_content)
            thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
            fullAnswer = answer['answer'].replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("NEXT QUESTIONS:", 'Next Questions:')
            sources = answer['sources']
            modifiedAnswer, sources, nextQuestions = parseResponse(fullAnswer, sources)
            if ((modifiedAnswer.find("I don't know") >= 0) or (modifiedAnswer.find("I'm not sure") >= 0)):
                sources = ''
                nextQuestions = ''

                
            return {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                    "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                    "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                    "nextQuestions": nextQuestions, "error": ""}
        elif indexType == "redis":
            try:
                returnField = ["metadata", "content", "vector_score"]
                vectorField = "content_vector"
                results = performRedisSearch(question, indexNs, topK, returnField, vectorField, embeddingModelType)
                docs = [
                        Document(page_content=result.content, metadata=json.loads(result.metadata))
                        for result in results.docs
                ]
                rawDocs = []
                for doc in docs:
                    rawDocs.append(doc.page_content)
                thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                qaChain = load_qa_with_sources_chain(llm,
                    chain_type="map_reduce", question_prompt=qaPrompt, combine_prompt=combinePrompt)
                answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                fullAnswer = answer['output_text'].replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("NEXT QUESTIONS:", 'Next Questions:')
                modifiedAnswer, sources, nextQuestions = parseResponse(fullAnswer, '')
                if ((modifiedAnswer.find("I don't know") >= 0) or (modifiedAnswer.find("I'm not sure") >= 0)):
                    sources = ''
                    nextQuestions = ''
                return {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                    "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                    "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                    "nextQuestions": nextQuestions, "error": ""}
            except Exception as e:
                return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "",
                        "sources": '', "nextQuestions": '', "error": str(e)}
        elif indexType == "cogsearch" or indexType == "cogsearchvs":
            r = performCogSearch(indexType, embeddingModelType, question, indexNs, topK)
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
            thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
            qaChain = load_qa_with_sources_chain(llm,
                    chain_type="map_reduce", question_prompt=qaPrompt, combine_prompt=combinePrompt)
            answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
            fullAnswer = answer['output_text'].replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("NEXT QUESTIONS:", 'Next Questions:')
            modifiedAnswer, sources, nextQuestions = parseResponse(fullAnswer, '')
            if ((modifiedAnswer.find("I don't know") >= 0) or (modifiedAnswer.find("I'm not sure") >= 0)):
                sources = ''
                nextQuestions = ''

            return {"data_points": rawDocs, "answer": modifiedAnswer.replace("Answer: ", ''), 
                "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'), 
                "sources": sources.replace("SOURCES:", '').replace("SOURCES", "").replace("Sources:", '').replace('- ', ''), 
                "nextQuestions": nextQuestions, "error": ""}
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
        
    except Exception as e:
        logging.info(e)
        return {"data_points": "", "answer": "Error : " + str(e), "thoughts": "",
                "sources": '', "nextQuestions": '', "error": str(e)}

def GetAnswer(history, approach, overrides, indexNs, indexType, question, indexName):
    logging.info("Getting Chat Answer")
    try:
      logging.info("Loading OpenAI")
      if (approach == 'rrr'):
        r = GetRrrAnswer(history, approach, overrides, indexNs, indexType, question, indexName)
      else:
          return json.dumps({"error": "unknown approach"})
      return r
    except Exception as e:
      logging.error(e)
      return func.HttpResponse(
            "Error getting files",
            status_code=500
      )

def TransformValue(record, indexNs, indexType, question, indexName):
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

        summaryResponse = GetAnswer(history, approach, overrides, indexNs, indexType, question, indexName)
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

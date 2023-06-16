import logging, json, os
import azure.functions as func
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains import RetrievalQA
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import RegexParser
from redis import Redis
import numpy as np
from langchain.docstore.document import Document
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch, generateKbEmbeddings, performKbCogVectorSearch, indexDocs
from langchain.prompts import load_prompt
from Utilities.envVars import *
from langchain.agents import create_csv_agent
from Utilities.azureBlob import getLocalBlob, getFullPath
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import uuid
import ast

def QaAnswer(chainType, question, indexType, value, indexNs, approach, overrides):
    logging.info("Calling QaAnswer Open AI")
    answer = ''
    
    try:
        topK = overrides.get("top") or 5
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'

        logging.info("Search for Top " + str(topK) + " and chainType is " + str(overrideChain))
        thoughtPrompt = ''

        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureChatOpenAI(
                    openai_api_base=openai.api_base,
                    openai_api_version=OpenAiVersion,
                    deployment_name=OpenAiChat,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    openai_api_type="azure",
                    max_tokens=tokenLength)
            embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
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
                template = """
                Given the following extracted parts of a long document and a question, create a final answer. 
                If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
                If the answer is not contained within the text below, say \"I don't know\".

                QUESTION: {question}
                =========
                {summaries}
                =========
                """
                #qaPrompt = load_prompt('lc://prompts/qa_with_sources/stuff/basic.json')
                qaPrompt = PromptTemplate(template=template, input_variables=["summaries", "question"])
                #qaChain = load_qa_chain(llm, chain_type=overrideChain, prompt=qaPrompt)
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, prompt=qaPrompt)

                # followupTemplate = """
                # Perform the following steps in a consecutive order Step 1, Step 2, Step 3, and Step 4. 
                # Step 1 Generate 10 questions based on the {context}?. 
                # Step 2 – Generate 5 more questions about "{context}" that do not repeat the above. 
                # Step 3 – Generate 5 more questions about "{context}" that do not repeat the above. 
                # Step 4 – Based on the above Steps 1,2,3 suggest a final list of questions avoiding duplicates or 
                # semantically similar questions.
                # Use double angle brackets to reference the questions, e.g. <>.
                # ALWAYS return a "NEXT QUESTIONS" part in your answer.
                # """
                followupTemplate = """
                Generate three very brief follow-up questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <>.
                Try not to repeat questions that have already been asked.

                Return the questions in the following format:
                <>
                <>
                <>

                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                =========
                {context}
                =========

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
                followupChain = load_qa_chain(llm, chain_type=overrideChain, prompt=followupPrompt)
            elif (overrideChain == "map_rerank"):
                outputParser = RegexParser(
                    regex=r"(.*?)\nScore: (.*)",
                    output_keys=["answer", "score"],
                )

                promptTemplate = """
                
                Use the following pieces of context to answer the question. If you don't know the answer, just say that you don't know, don't try to make up an answer.

                In addition to giving an answer, also return a score of how fully it answered the user's question. This should be in the following format:

                Question: [question here]
                [answer here]
                Score: [score between 0 and 100]

                Begin!

                Context:
                ---------
                {summaries}
                ---------
                Question: {question}

                """
                qaPrompt = PromptTemplate(template=promptTemplate,input_variables=["summaries", "question"],
                                          output_parser=outputParser)
                qaChain = load_qa_with_sources_chain(llm, chain_type=chainType,
                                            prompt=qaPrompt)

                followupTemplate = """
                Generate three very brief follow-up questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <>.
                Try not to repeat questions that have already been asked.

                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                =========
                {context}
                =========

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
                followupChain = load_qa_chain(llm, chain_type='stuff', prompt=followupPrompt)
            elif (overrideChain == "map_reduce"):

                qaTemplate = """Use the following portion of a long document to see if any of the text is relevant to answer the question.
                Return any relevant text.
                {context}
                Question: {question}
                Relevant text, if any :"""

                qaPrompt = PromptTemplate(
                    template=qaTemplate, input_variables=["context", "question"]
                )

                combinePromptTemplate = """
                    Given the following extracted parts of a long document and a question, create a final answer. 
                    If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
                    If the answer is not contained within the text below, say \"I don't know\".

                    QUESTION: {question}
                    =========
                    {summaries}
                    =========
                    """
                combinePrompt = PromptTemplate(
                    template=combinePromptTemplate, input_variables=["summaries", "question"]
                )

               

                #qaChain = load_qa_chain(llm, chain_type=overrideChain, question_prompt=qaPrompt, combine_prompt=combinePrompt)
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, question_prompt=qaPrompt, combine_prompt=combinePrompt)
                
                followupTemplate = """
                Generate three very brief follow-up questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <>.
                Try not to repeat questions that have already been asked.

                Return the questions in the following format:
                <>
                <>
                <>

                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                =========
                {context}
                =========

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
                followupChain = load_qa_chain(llm, chain_type='stuff', prompt=followupPrompt)
            elif (overrideChain == "refine"):
                refineTemplate = (
                    "The original question is as follows: {question}\n"
                    "We have provided an existing answer, including sources: {existing_answer}\n"
                    "We have the opportunity to refine the existing answer"
                    "(only if needed) with some more context below.\n"
                    "------------\n"
                    "{context_str}\n"
                    "------------\n"
                    "Given the new context, refine the original answer to better "
                    "If you do update it, please update the sources as well. "
                    "If the context isn't useful, return the original answer."
                )
                refinePrompt = PromptTemplate(
                    input_variables=["question", "existing_answer", "context_str"],
                    template=refineTemplate,
                )

                qaTemplate = """
                    Given the following extracted parts of a long document and a question, create a final answer. 
                    If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
                    If the answer is not contained within the text below, say \"I don't know\".

                    QUESTION: {question}
                    =========
                    {context_str}
                    =========
                    """
                qaPrompt = PromptTemplate(
                    input_variables=["context_str", "question"], template=qaTemplate
                )
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, question_prompt=qaPrompt, refine_prompt=refinePrompt)

                
                followupTemplate = """
                Generate three very brief follow-up questions that the user would likely ask next.
                Use double angle brackets to reference the questions, e.g. <>.
                Try not to repeat questions that have already been asked.

                Return the questions in the following format:
                <>
                <>
                <>
                
                ALWAYS return a "NEXT QUESTIONS" part in your answer.

                =========
                {context}
                =========

                """
                followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
                followupChain = load_qa_chain(llm, chain_type='stuff', prompt=followupPrompt)

            # Let's verify if the questions is already answered before and check our KB first before asking LLM
            vectorQuestion = generateKbEmbeddings(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, OpenAiEmbedding, embeddingModelType, question)

            # Let's perform the search on the KB first before asking the question to the model
            kbSearch = performKbCogVectorSearch(vectorQuestion, 'vectorQuestion', SearchService, SearchKey, indexType, indexNs, KbIndexName, 1, ["id", "question", "indexType", "indexName", "answer"])

            logging.info("KB Search Count: " + str(kbSearch.get_count()))

            if kbSearch.get_count() > 0:
                for s in kbSearch:
                    logging.info("Found answer from existing KB")
                    if s['@search.score'] >= 0.95:
                        #jsonAnswer = ast.literal_eval(json.dumps(s['answer']))
                        jsonAnswer = json.loads(s['answer'])
                        return jsonAnswer

            kbData = []
            kbId = str(uuid.uuid4())

            if indexType == 'pinecone':
                vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
                docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
                logging.info("Pinecone Setup done")
                chain = RetrievalQA(combine_documents_chain=qaChain, retriever=docRetriever, return_source_documents=True)
                llmAnswer = chain({"query": question}, return_only_outputs=True)
                docs = llmAnswer['source_documents']
                rawDocs = []
                for doc in docs:
                    rawDocs.append(doc.page_content)
                
                if overrideChain == "stuff" or overrideChain == "map_rerank":
                    thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
                elif overrideChain == "map_reduce":
                    thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                elif overrideChain == "refine":
                    thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
                
                answer = llmAnswer['result'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
                modifiedAnswer = answer
                
                # Followup questions
                followupChain = RetrievalQA(combine_documents_chain=followupChain, retriever=docRetriever)
                followupAnswer = followupChain({"query": question}, return_only_outputs=True)
                nextQuestions = followupAnswer['result'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:').replace('NEXT QUESTIONS:', '').replace('NEXT QUESTIONS', '')
                sources = ''                
                if (modifiedAnswer.find("I don't know") >= 0):
                    sources = ''
                    nextQuestions = ''
                else:
                    sources = sources + "\n" + docs[0].metadata['source']

                outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
                        "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                            "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                
                kbData.append({
                        "id": kbId,
                        "question": question,
                        "indexType": indexType,
                        "indexName": indexNs,
                        "vectorQuestion": vectorQuestion,
                        "answer": json.dumps(outputFinalAnswer),
                    })
                
                indexDocs(SearchService, SearchKey, KbIndexName, kbData)

                return outputFinalAnswer            
            elif indexType == "redis":
                try:
                    returnField = ["metadata", "content", "vector_score"]
                    vectorField = "content_vector"
                    results = performRedisSearch(question, indexNs, topK, returnField, vectorField, embeddingModelType)
                    docs = [
                            Document(page_content=result.content, metadata=json.loads(result.metadata))
                            for result in results.docs
                    ]
                    rawDocs=[]
                    for doc in docs:
                        rawDocs.append(doc.page_content)
                    answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    answer = answer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
                    modifiedAnswer = answer

                    if overrideChain == "stuff" or overrideChain == "map_rerank":
                        thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
                    elif overrideChain == "map_reduce":
                        thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                    elif overrideChain == "refine":
                        thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
                    
                    # Followup questions
                    followupAnswer = followupChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    nextQuestions = followupAnswer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:').replace('NEXT QUESTIONS:', '').replace('NEXT QUESTIONS', '')
                    sources = ''                
                    if (modifiedAnswer.find("I don't know") >= 0):
                        sources = ''
                        nextQuestions = ''
                    else:
                        sources = sources + "\n" + docs[0].metadata['source']

                    
                    outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
                            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                                "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                    
                    kbData.append({
                        "id": kbId,
                        "question": question,
                        "indexType": indexType,
                        "indexName": indexNs,
                        "vectorQuestion": vectorQuestion,
                        "answer": json.dumps(outputFinalAnswer),
                    })

                    indexDocs(SearchService, SearchKey, KbIndexName, kbData)

                    return outputFinalAnswer
                                
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
            elif indexType == "cogsearch" or indexType == "cogsearchvs":
                try:
                    r = performCogSearch(indexType, embeddingModelType, question, indexNs, topK)
                    if r == None:
                        docs = [Document(page_content="No results found")]
                    else :
                        docs = [
                            Document(page_content=doc['content'], metadata={"id": doc['id'], "source": doc['sourcefile']})
                            for doc in r
                            ]
                    rawDocs=[]
                    for doc in docs:
                        rawDocs.append(doc.page_content)
                    
                    answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    answer = answer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
                    modifiedAnswer = answer

                    if overrideChain == "stuff" or overrideChain == "map_rerank":
                        thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
                    elif overrideChain == "map_reduce":
                        thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                    elif overrideChain == "refine":
                        thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
                    

                    # Followup questions
                    followupAnswer = followupChain({"input_documents": docs, "question": question}, return_only_outputs=True)
                    nextQuestions = followupAnswer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:').replace('NEXT QUESTIONS:', '').replace('NEXT QUESTIONS', '')
                    sources = ''                
                    if (modifiedAnswer.find("I don't know") >= 0):
                        sources = ''
                        nextQuestions = ''
                    else:
                        sources = sources + "\n" + docs[0].metadata['source']

                    outputFinalAnswer = {"data_points": rawDocs, "answer": modifiedAnswer, 
                            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                                "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                    
                    kbData.append({
                        "id": kbId,
                        "question": question,
                        "indexType": indexType,
                        "indexName": indexNs,
                        "vectorQuestion": vectorQuestion,
                        "answer": json.dumps(outputFinalAnswer),
                    })

                    indexDocs(SearchService, SearchKey, KbIndexName, kbData)
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
      logging.info("Error in QaAnswer Open AI : " + str(e))
      return {"data_points": "", "answer": "Exception during finding answers - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}

    #return answer

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
        logging.info("Input parameters : " + chainType + " " + question + " " + indexType)
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
        result = ComposeResponse(chainType, question, indexType, body, indexNs)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

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

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

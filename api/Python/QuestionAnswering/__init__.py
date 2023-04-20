import logging, json, os
import azure.functions as func
import openai
from langchain.llms.openai import AzureOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
from langchain.chains import RetrievalQAWithSourcesChain, VectorDBQAWithSourcesChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import RegexParser
from redis import Redis
import numpy as np
from langchain.docstore.document import Document
from Utilities.redisIndex import performRedisSearch
from Utilities.cogSearch import performCogSearch
from langchain.prompts import load_prompt

OpenAiKey = os.environ['OpenAiKey']
OpenAiEndPoint = os.environ['OpenAiEndPoint']
OpenAiVersion = os.environ['OpenAiVersion']
OpenAiDavinci = os.environ['OpenAiDavinci']
OpenAiEmbedding = os.environ['OpenAiEmbedding']
OpenAiService = os.environ['OpenAiService']
OpenAiDocStorName = os.environ['OpenAiDocStorName']
OpenAiDocStorKey = os.environ['OpenAiDocStorKey']
OpenAiDocConnStr = f"DefaultEndpointsProtocol=https;AccountName={OpenAiDocStorName};AccountKey={OpenAiDocStorKey};EndpointSuffix=core.windows.net"
OpenAiDocContainer = os.environ['OpenAiDocContainer']
PineconeEnv = os.environ['PineconeEnv']
PineconeKey = os.environ['PineconeKey']
VsIndexName = os.environ['VsIndexName']
SearchService = os.environ['SearchService']
SearchKey = os.environ['SearchKey']

def FindAnswer(chainType, question, indexType, value, indexNs, approach, overrides):
    logging.info("Calling FindAnswer Open AI")
    openai.api_type = "azure"
    openai.api_key = OpenAiKey
    openai.api_version = OpenAiVersion
    openai.api_base = f"https://{OpenAiService}.openai.azure.com"

    answer = ''

    # https://langchain.readthedocs.io/en/latest/modules/indexes/chain_examples/qa_with_sources.html

    try:
        topK = overrides.get("top") or 5
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        logging.info("Search for Top " + str(topK) + " and chainType is " + str(overrideChain))
        thoughtPrompt = ''
        if (approach == 'rtr'):
            llm = AzureOpenAI(deployment_name=OpenAiDavinci,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    max_tokens=tokenLength,
                    batch_size=10)

            logging.info("LLM Setup done")
            embeddings = OpenAIEmbeddings(document_model_name=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)

            if (overrideChain == "stuff"):
                if indexType == 'cogsearch':
                    template = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
                    If you don't know the answer, just say that you don't know. Don't try to make up an answer.
                    ALWAYS return a "SOURCES" part in your answer.

                    Generate three very brief follow-up questions that the user would likely ask next.
                    Use double angle brackets to reference the questions, e.g. <<Is there a more details on that?>>.
                    Try not to repeat questions that have already been asked.
                    Only generate questions and do not generate any text before or after the questions, such as 'Next Questions

                    QUESTION: {question}
                    =========
                    {summaries}
                    =========
                    """
                else:
                    template = "Given the following extracted parts of a long document and a question, create a final answer with references (\"SOURCES\"). \nIf you don't know the answer, just say that you don't know. Don't try to make up an answer.\nALWAYS return a \"SOURCES\" part in your answer.\n\nQUESTION: Which state/country's law governs the interpretation of the contract?\n=========\nContent: This Agreement is governed by English law and the parties submit to the exclusive jurisdiction of the English courts in  relation to any dispute (contractual or non-contractual) concerning this Agreement save that either party may apply to any court for an  injunction or other relief to protect its Intellectual Property Rights.\nSource: 28-pl\nContent: No Waiver. Failure or delay in exercising any right or remedy under this Agreement shall not constitute a waiver of such (or any other)  right or remedy.\n\n11.7 Severability. The invalidity, illegality or unenforceability of any term (or part of a term) of this Agreement shall not affect the continuation  in force of the remainder of the term (if any) and this Agreement.\n\n11.8 No Agency. Except as expressly stated otherwise, nothing in this Agreement shall create an agency, partnership or joint venture of any  kind between the parties.\n\n11.9 No Third-Party Beneficiaries.\nSource: 30-pl\nContent: (b) if Google believes, in good faith, that the Distributor has violated or caused Google to violate any Anti-Bribery Laws (as  defined in Clause 8.5) or that such a violation is reasonably likely to occur,\nSource: 4-pl\n=========\nFINAL ANSWER: This Agreement is governed by English law.\nSOURCES: 28-pl\n\nQUESTION: What did the president say about Michael Jackson?\n=========\nContent: Madam Speaker, Madam Vice President, our First Lady and Second Gentleman. Members of Congress and the Cabinet. Justices of the Supreme Court. My fellow Americans.  \n\nLast year COVID-19 kept us apart. This year we are finally together again. \n\nTonight, we meet as Democrats Republicans and Independents. But most importantly as Americans. \n\nWith a duty to one another to the American people to the Constitution. \n\nAnd with an unwavering resolve that freedom will always triumph over tyranny. \n\nSix days ago, Russia\u2019s Vladimir Putin sought to shake the foundations of the free world thinking he could make it bend to his menacing ways. But he badly miscalculated. \n\nHe thought he could roll into Ukraine and the world would roll over. Instead he met a wall of strength he never imagined. \n\nHe met the Ukrainian people. \n\nFrom President Zelenskyy to every Ukrainian, their fearlessness, their courage, their determination, inspires the world. \n\nGroups of citizens blocking tanks with their bodies. Everyone from students to retirees teachers turned soldiers defending their homeland.\nSource: 0-pl\nContent: And we won\u2019t stop. \n\nWe have lost so much to COVID-19. Time with one another. And worst of all, so much loss of life. \n\nLet\u2019s use this moment to reset. Let\u2019s stop looking at COVID-19 as a partisan dividing line and see it for what it is: A God-awful disease.  \n\nLet\u2019s stop seeing each other as enemies, and start seeing each other for who we really are: Fellow Americans.  \n\nWe can\u2019t change how divided we\u2019ve been. But we can change how we move forward\u2014on COVID-19 and other issues we must face together. \n\nI recently visited the New York City Police Department days after the funerals of Officer Wilbert Mora and his partner, Officer Jason Rivera. \n\nThey were responding to a 9-1-1 call when a man shot and killed them with a stolen gun. \n\nOfficer Mora was 27 years old. \n\nOfficer Rivera was 22. \n\nBoth Dominican Americans who\u2019d grown up on the same streets they later chose to patrol as police officers. \n\nI spoke with their families and told them that we are forever in debt for their sacrifice, and we will carry on their mission to restore the trust and safety every community deserves.\nSource: 24-pl\nContent: And a proud Ukrainian people, who have known 30 years  of independence, have repeatedly shown that they will not tolerate anyone who tries to take their country backwards.  \n\nTo all Americans, I will be honest with you, as I\u2019ve always promised. A Russian dictator, invading a foreign country, has costs around the world. \n\nAnd I\u2019m taking robust action to make sure the pain of our sanctions  is targeted at Russia\u2019s economy. And I will use every tool at our disposal to protect American businesses and consumers. \n\nTonight, I can announce that the United States has worked with 30 other countries to release 60 Million barrels of oil from reserves around the world.  \n\nAmerica will lead that effort, releasing 30 Million barrels from our own Strategic Petroleum Reserve. And we stand ready to do more if necessary, unified with our allies.  \n\nThese steps will help blunt gas prices here at home. And I know the news about what\u2019s happening can seem alarming. \n\nBut I want you to know that we are going to be okay.\nSource: 5-pl\nContent: More support for patients and families. \n\nTo get there, I call on Congress to fund ARPA-H, the Advanced Research Projects Agency for Health. \n\nIt\u2019s based on DARPA\u2014the Defense Department project that led to the Internet, GPS, and so much more.  \n\nARPA-H will have a singular purpose\u2014to drive breakthroughs in cancer, Alzheimer\u2019s, diabetes, and more. \n\nA unity agenda for the nation. \n\nWe can do this. \n\nMy fellow Americans\u2014tonight , we have gathered in a sacred space\u2014the citadel of our democracy. \n\nIn this Capitol, generation after generation, Americans have debated great questions amid great strife, and have done great things. \n\nWe have fought for freedom, expanded liberty, defeated totalitarianism and terror. \n\nAnd built the strongest, freest, and most prosperous nation the world has ever known. \n\nNow is the hour. \n\nOur moment of responsibility. \n\nOur test of resolve and conscience, of history itself. \n\nIt is in this moment that our character is formed. Our purpose is found. Our future is forged. \n\nWell I know this nation.\nSource: 34-pl\n=========\nFINAL ANSWER: The president did not mention Michael Jackson.\nGenerate three very brief follow-up questions that the user would likely ask next.\nUse double angle brackets to reference the questions, e.g. <<Is there a more details on that?>>.\nTry not to repeat questions that have already been asked.\nOnly generate questions and do not generate any text before or after the questions, such as 'Next Questions\nSOURCES:\n\nQUESTION: {question}\n=========\n{summaries}\n=========\nFINAL ANSWER:"
                #qaPrompt = load_prompt('lc://prompts/qa_with_sources/stuff/basic.json')
                qaPrompt = PromptTemplate(template=template, input_variables=["summaries", "question"])
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, prompt=qaPrompt)
            elif (overrideChain == "map_rerank"):
                outputParser = RegexParser(
                    regex=r"(.*?)\nScore: (.*)",
                    output_keys=["answer", "score"],
                )

                promptTemplate = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

                In addition to giving an answer, also return a score of how fully it answered the user's question. This should be in the following format:

                Question: [question here]
                [answer here]
                Score: [score between 0 and 100]

                Begin!

                Context:
                ---------
                {context}
                ---------
                Question: {question}

                """
                qaPrompt = PromptTemplate(
                    template=promptTemplate,
                    input_variables=["context", "question"],
                    output_parser=outputParser,
                )
                qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, metadata_keys=['source'], prompt=qaPrompt)
            elif (overrideChain == "map_reduce"):

                qaTemplate = """Use the following portion of a long document to see if any of the text is relevant to answer the question.
                Return any relevant text.
                {context}
                Question: {question}
                Relevant text, if any :"""

                qaPrompt = PromptTemplate(
                    template=qaTemplate, input_variables=["context", "question"]
                )

                combinePromptTemplate = """Given the following extracted parts of a long document and a question, create a final answer with references ("SOURCES").
                If you don't know the answer, just say that you don't know. Don't try to make up an answer.
                ALWAYS return a "SOURCES" part in your answer.

                QUESTION: {question}
                =========
                {summaries}
                =========
                """
                combinePrompt = PromptTemplate(
                    template=combinePromptTemplate, input_variables=["summaries", "question"]
                )
                qaChain = load_qa_with_sources_chain(llm,
                    chain_type=overrideChain, question_prompt=qaPrompt, combine_prompt=combinePrompt)
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

                qaTemplate = (
                    "Context information is below. \n"
                    "---------------------\n"
                    "{context_str}"
                    "\n---------------------\n"
                    "Given the context information and not prior knowledge, "
                    "answer the question: {question}\n"
                    "\n---------------------\n"
                    # "Generate three very brief follow-up questions that the user would likely ask next.\n"
                    # "Use double angle brackets to reference the questions, e.g. <<Is there a more details on that?>>.\n"
                    # "Try not to repeat questions that have already been asked.\n"
                    # "Only generate questions and do not generate any text before or after the questions, such as 'Next Questions"
                )
                qaPrompt = PromptTemplate(
                    input_variables=["context_str", "question"], template=qaTemplate
                )
                qaChain = load_qa_with_sources_chain(llm,
                chain_type=overrideChain, question_prompt=qaPrompt, refine_prompt=refinePrompt)

            if indexType == 'pinecone':
                vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
                docRetriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
                logging.info("Pinecone Setup done")
                #chain = VectorDBQAWithSourcesChain(combine_documents_chain=qaChain, vectorstore=vectorDb, k=topK,
                #                                search_kwargs={"namespace": indexNs})
                chain = RetrievalQAWithSourcesChain(combine_documents_chain=qaChain, retriever=docRetriever, return_source_documents=True)
                llmAnswer = chain({"question": question}, return_only_outputs=True)
                docs = llmAnswer['source_documents']
                rawDocs = []
                for doc in docs:
                    rawDocs.append(doc.page_content)
                
                if overrideChain == "stuff":
                    try:
                        thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
                    except:
                        try:
                            thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                        except:
                            thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
                    answer = llmAnswer['answer'].replace("Answer: ", '')
                    sourceAndQuestions = llmAnswer['sources'].replace("NEXT QUESTIONS:", 'Next Questions:')
                    try:
                        if sourceAndQuestions.index("Next Questions:") > 0:
                            sources = sourceAndQuestions[:sourceAndQuestions.index("Next Questions:")]
                            nextQuestions = sourceAndQuestions[sourceAndQuestions.index("Next Questions:"):]
                        else:
                            sources = sourceAndQuestions
                            nextQuestions = ''
                    except:
                        sources = sourceAndQuestions
                        nextQuestions = ''     
                    return {"data_points": rawDocs, "answer": answer, 
                            "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                            "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                else:
                    return {"data_points": rawDocs, "answer": llmAnswer['answer'].replace("Answer: ", ''), 
                            "thoughts": llmAnswer['sources'], 
                            "sources": '', "nextQuestions": '', "error": ""}
            elif indexType == "redis":
                try:
                    returnField = ["metadata", "content", "vector_score"]
                    vectorField = "content_vector"
                    results = performRedisSearch(question, indexNs, topK, returnField, vectorField)
                    docs = [
                            Document(page_content=result.content, metadata=json.loads(result.metadata))
                            for result in results.docs
                    ]
                    rawDocs=[]
                    for doc in docs:
                        rawDocs.append(doc.page_content)
                    answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)

                    if overrideChain == "stuff":
                        try:
                            thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
                        except:
                            try:
                                thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                            except:
                                thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
                        fullAnswer = answer['output_text'].replace("Sources:", 'SOURCES:')
                        if fullAnswer.index("SOURCES:") > 0:
                            modifiedAnswer = fullAnswer[:fullAnswer.index("SOURCES:")]
                            thoughts = fullAnswer[fullAnswer.index("SOURCES:"):]
                            thoughts = thoughts.replace("NEXT QUESTIONS:", 'Next Questions:')
                            try:
                                if thoughts.index("Next Questions:") > 0:
                                    sources = thoughts[:thoughts.index("Next Questions:")]
                                    nextQuestions = thoughts[thoughts.index("Next Questions:"):]
                                else:
                                    sources = thoughts
                                    nextQuestions = ''
                            except:
                                if thoughts.index("<<") > 0:
                                    sources = thoughts[:thoughts.index("<<")]
                                    nextQuestions = thoughts[thoughts.index("<<"):]
                                else:
                                    sources = thoughts
                                    nextQuestions = ''
                            return {"data_points": rawDocs, "answer": modifiedAnswer, 
                                    "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                                    "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                        else:
                            return {"data_points": rawDocs, "answer": fullAnswer['output_text'].replace("Answer: ", ''), "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
                    else:
                        return {"data_points": rawDocs, "answer": answer['output_text'].replace("Answer: ", ''), 
                                "thoughts": '', 
                                "sources": '', "nextQuestions": '', "error": ""}
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Redis Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
            elif indexType == "cogsearch":
                try:
                    r = performCogSearch(question, indexNs, topK)
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
                    if overrideChain == "stuff":
                        try:
                            thoughtPrompt = qaPrompt.format(question=question, summaries=rawDocs)
                        except:
                            try:
                                thoughtPrompt = qaPrompt.format(question=question, context=rawDocs)
                            except:
                                thoughtPrompt = qaPrompt.format(question=question, context_str=rawDocs)
                        fullAnswer = answer['output_text'].replace("Source:", 'SOURCES:').replace("Sources:", 'SOURCES:').replace("Answer: ", '')
                        try:
                            if fullAnswer.index("SOURCES:") > 0:
                                modifiedAnswer = fullAnswer[:fullAnswer.index("SOURCES:")]
                                thoughts = fullAnswer[fullAnswer.index("SOURCES:"):]
                                thoughts = thoughts.replace("NEXT QUESTIONS:", 'Next Questions:')
                                try:
                                    if thoughts.index("Next Questions:") > 0:
                                        sources = thoughts[:thoughts.index("Next Questions:")]
                                        nextQuestions = thoughts[thoughts.index("Next Questions:"):]
                                    else:
                                        sources = thoughts
                                        nextQuestions = ''
                                except:
                                    if thoughts.index("<<") > 0:
                                        sources = thoughts[:thoughts.index("<<")]
                                        nextQuestions = thoughts[thoughts.index("<<"):]
                                    else:
                                        sources = thoughts
                                        nextQuestions = ''
                                return {"data_points": rawDocs, "answer": modifiedAnswer, 
                                        "thoughts": f"<br><br>Prompt:<br>" + thoughtPrompt.replace('\n', '<br>'),
                                        "sources": sources, "nextQuestions": nextQuestions, "error": ""}
                            else:
                                return {"data_points": rawDocs, "answer": fullAnswer['output_text'], "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
                        except:
                            return {"data_points": rawDocs, "answer": fullAnswer['output_text'], "thoughts": '', "sources": '', "nextQuestions": '', "error": ""}
                    else:
                        return {"data_points": rawDocs, "answer": answer['output_text'].replace("Answer: ", ''), 
                                "thoughts": '',
                                "sources": '', "nextQuestions": '', "error": ""}
                except Exception as e:
                    return {"data_points": "", "answer": "Working on fixing Cognitive Search Implementation - Error : " + str(e), "thoughts": "", "sources": "", "nextQuestions": "", "error":  str(e)}
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
      logging.info("Error in FindAnswer Open AI : " + str(e))

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

        answer = FindAnswer(chainType, question, indexType, value, indexNs, approach, overrides)
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

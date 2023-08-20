import logging, json, os
import azure.functions as func
from Utilities.envVars import *
import azure.durable_functions as df
from Utilities.envVars import *
# Import required libraries
from Utilities.cogSearchVsRetriever import CognitiveSearchVsRetriever
from langchain.chains import RetrievalQA
from langchain import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from Utilities.evaluator import createEvaluatorDataSearchIndex, indexEvaluatorDataSections, indexDocs
from Utilities.evaluator import searchEvaluatorDocumentIndexedData, createEvaluatorDocumentSearchIndex
from langchain.chains import QAGenerationChain
import json
import time
import pandas as pd
from collections import namedtuple
from Utilities.evaluator import searchEvaluatorDocument, searchEvaluatorRunIdIndex
import uuid
import tempfile
from Utilities.azureBlob import getBlob, getFullPath
from langchain.document_loaders import PDFMinerLoader, UnstructuredFileLoader
from Utilities.evaluator import createEvaluatorQaSearchIndex, searchEvaluatorQaData, searchEvaluatorDocument
from Utilities.evaluator import createEvaluatorDataSearchIndex, indexEvaluatorDataSections
from Utilities.evaluator import createEvaluatorResultIndex, searchEvaluatorRunIdIndex
from json import JSONDecodeError
import random
import itertools
import openai
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.evaluation.qa import QAEvalChain
from Utilities.evaluator import searchEvaluatorRunIndex, createEvaluatorRunIndex, getEvaluatorResult

RunDocs = namedtuple('RunDoc', ['evalatorQaData', 'totalQuestions', 'promptStyle', 'documentId', 
                                        'splitMethods', 'chunkSizes', 'overlaps',
                                        'retrieverType', 'reEvaluate', 'topK', 'model', 'fileName',
                                        'embeddingModelType', 'temperature', 'tokenLength'])

def getPrompts():
    template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible.
    {context}
    Question: {question}
    Helpful Answer:"""

    QaChainPrompt = PromptTemplate(input_variables=["context", "question"],template=template,)

    template = """You are a teacher grading a quiz. 
    You are given a question, the student's answer, and the true answer, and are asked to score the student answer as either Correct or Incorrect.

    Example Format:
    QUESTION: question here
    STUDENT ANSWER: student's answer here
    TRUE ANSWER: true answer here
    GRADE: Correct or Incorrect here

    Grade the student answers based ONLY on their factual accuracy. Ignore differences in punctuation and phrasing between the student answer and true answer. It is OK if the student answer contains more information than the true answer, as long as it does not contain any conflicting statements. If the student answers that there is no specific information provided in the context, then the answer is Incorrect. Begin! 

    QUESTION: {query}
    STUDENT ANSWER: {result}
    TRUE ANSWER: {answer}
    GRADE:"""

    promptStyleFast = PromptTemplate(input_variables=["query", "result", "answer"], template=template)

    template = """You are a teacher grading a quiz. 
    You are given a question, the student's answer, and the true answer, and are asked to score the student answer as either Correct or Incorrect.
    You are also asked to identify potential sources of bias in the question and in the true answer.

    Example Format:
    QUESTION: question here
    STUDENT ANSWER: student's answer here
    TRUE ANSWER: true answer here
    GRADE: Correct or Incorrect here

    Grade the student answers based ONLY on their factual accuracy. Ignore differences in punctuation and phrasing between the student answer and true answer. It is OK if the student answer contains more information than the true answer, as long as it does not contain any conflicting statements. If the student answers that there is no specific information provided in the context, then the answer is Incorrect. Begin! 

    QUESTION: {query}
    STUDENT ANSWER: {result}
    TRUE ANSWER: {answer}
    GRADE:

    Your response should be as follows:

    GRADE: (Correct or Incorrect)
    (line break)
    JUSTIFICATION: (Without mentioning the student/teacher framing of this prompt, explain why the STUDENT ANSWER is Correct or Incorrect, identify potential sources of bias in the QUESTION, and identify potential sources of bias in the TRUE ANSWER. Use one or two sentences maximum. Keep the answer as concise as possible.)
    """

    promptStyleBias = PromptTemplate(input_variables=["query", "result", "answer"], template=template)

    template = """You are assessing a submitted student answer to a question relative to the true answer based on the provided criteria: 
    
        ***
        QUESTION: {query}
        ***
        STUDENT ANSWER: {result}
        ***
        TRUE ANSWER: {answer}
        ***
        Criteria: 
        relevance:  Is the submission referring to a real quote from the text?"
        conciseness:  Is the answer concise and to the point?"
        correct: Is the answer correct?"
        ***
        Does the submission meet the criterion? First, write out in a step by step manner your reasoning about the criterion to be sure that your conclusion is correct. Avoid simply stating the correct answers at the outset. Then print "Correct" or "Incorrect" (without quotes or punctuation) on its own line corresponding to the correct answer.
        Reasoning:
    """

    promptStyleGrading = PromptTemplate(input_variables=["query", "result", "answer"], template=template)

    template = """You are a teacher grading a quiz. 
    You are given a question, the student's answer, and the true answer, and are asked to score the student answer as either Correct or Incorrect.

    Example Format:
    QUESTION: question here
    STUDENT ANSWER: student's answer here
    TRUE ANSWER: true answer here
    GRADE: Correct or Incorrect here

    Grade the student answers based ONLY on their factual accuracy. Ignore differences in punctuation and phrasing between the student answer and true answer. It is OK if the student answer contains more information than the true answer, as long as it does not contain any conflicting statements. If the student answers that there is no specific information provided in the context, then the answer is Incorrect. Begin! 

    QUESTION: {query}
    STUDENT ANSWER: {result}
    TRUE ANSWER: {answer}
    GRADE:

    Your response should be as follows:

    GRADE: (Correct or Incorrect)
    (line break)
    JUSTIFICATION: (Without mentioning the student/teacher framing of this prompt, explain why the STUDENT ANSWER is Correct or Incorrect. Use one or two sentences maximum. Keep the answer as concise as possible.)
    """

    promptStyleDefault = PromptTemplate(input_variables=["query", "result", "answer"], template=template)

    template = """ 
        Given the question: \n
        {query}
        Here are some documents retrieved in response to the question: \n
        {result}
        And here is the answer to the question: \n 
        {answer}
        Criteria: 
        relevance: Are the retrieved documents relevant to the question and do they support the answer?"
        Do the retrieved documents meet the criterion? Print "Correct" (without quotes or punctuation) if the retrieved context are relevant or "Incorrect" if not (without quotes or punctuation) on its own line. """

    gradeDocsPromptFast = PromptTemplate(input_variables=["query", "result", "answer"], template=template)

    template = """ 
        Given the question: \n
        {query}
        Here are some documents retrieved in response to the question: \n
        {result}
        And here is the answer to the question: \n 
        {answer}
        Criteria: 
        relevance: Are the retrieved documents relevant to the question and do they support the answer?"

        Your response should be as follows:

        GRADE: (Correct or Incorrect, depending if the retrieved documents meet the criterion)
        (line break)
        JUSTIFICATION: (Write out in a step by step manner your reasoning about the criterion to be sure that your conclusion is correct. Use one or two sentences maximum. Keep the answer as concise as possible.)
        """

    gradeDocsPromptDefault = PromptTemplate(input_variables=["query", "result", "answer"], template=template)

    return QaChainPrompt, promptStyleFast, promptStyleBias, promptStyleGrading, promptStyleDefault, gradeDocsPromptFast, gradeDocsPromptDefault

def gradeModelAnswer(llm, predictedDataSet, predictions, promptStyle, promptStyleFast, promptStyleBias, promptStyleGrading, promptStyleDefault):

    if promptStyle == "Fast":
        prompt = promptStyleFast
    elif promptStyle == "Descriptive w/ bias check":
        prompt = promptStyleBias
    elif promptStyle == "OpenAI grading prompt":
        prompt = promptStyleGrading
    else:
        prompt = promptStyleDefault

    # Note: GPT-4 grader is advised by OAI 
    evalChain = QAEvalChain.from_llm(llm=llm,
                                      prompt=prompt)
    gradedOutputs = evalChain.evaluate(predictedDataSet,
                                         predictions,
                                         question_key="question",
                                         prediction_key="result")
    return gradedOutputs

def gradeModelRetrieval(llm, getDataSet, predictions, gradeDocsPrompt, gradeDocsPromptFast, gradeDocsPromptDefault):

    if gradeDocsPrompt == "Fast":
        prompt = gradeDocsPromptFast
    else:
        prompt = gradeDocsPromptDefault

    # Note: GPT-4 grader is advised by OAI
    evalChain = QAEvalChain.from_llm(llm=llm,prompt=prompt)
    gradedOutputs = evalChain.evaluate(getDataSet,
                                         predictions,
                                         question_key="question",
                                         prediction_key="result")
    return gradedOutputs

def blobLoad(blobConnectionString, blobContainer, blobName):
    readBytes  = getBlob(blobConnectionString, blobContainer, blobName)
    downloadPath = os.path.join(tempfile.gettempdir(), blobName)
    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
    try:
        with open(downloadPath, "wb") as file:
            file.write(readBytes)
    except Exception as e:
        logging.error(e)

    logging.info("File created " + downloadPath)
    if (blobName.endswith(".pdf")):
        loader = PDFMinerLoader(downloadPath)

    rawDocs = loader.load()

    fullPath = getFullPath(blobConnectionString, blobContainer, blobName)
    for doc in rawDocs:
        doc.metadata['source'] = fullPath
    return rawDocs

def runEvaluator(llm, evaluatorQaData, totalQuestions, chain, retriever, promptStyle, 
                 promptStyleFast, promptStyleBias, promptStyleGrading, promptStyleDefault,
                 gradeDocsPromptFast, gradeDocsPromptDefault) -> list:
    d = pd.DataFrame(columns=['question', 'answer', 'predictedAnswer', 'answerScore', 'retrievalScore', 'latency'])
    for i in range(int(totalQuestions)):
        predictions = []
        retrievedDocs = []
        gtDataSet = []
        latency = []
        currentDataSet = evaluatorQaData[i]
    
        try:
            startTime = time.time()
            predictions.append(chain({"query": currentDataSet["question"]}, return_only_outputs=True))
            gtDataSet.append(currentDataSet)
            endTime = time.time()
            elapsedTime = endTime - startTime
            latency.append(elapsedTime)
        except:
            predictions.append({'result': 'Error in prediction'})
            print("Error in prediction")

        # Extract text from retrieved docs
        retrievedDocText = ""
        docs = retriever.get_relevant_documents(currentDataSet["question"])
        for i, doc in enumerate(docs):
            retrievedDocText += "Doc %s: " % str(i+1) + \
                doc.page_content + " "

        # Log
        retrieved = {"question": currentDataSet["question"],
                    "answer": currentDataSet["answer"], "result": retrievedDocText}
        retrievedDocs.append(retrieved)

        # Grade
        gradedAnswer = gradeModelAnswer(llm, gtDataSet, predictions, promptStyle, promptStyleFast, promptStyleBias, promptStyleGrading, promptStyleDefault)
        gradedRetrieval = gradeModelRetrieval(llm, gtDataSet, retrievedDocs, promptStyle, gradeDocsPromptFast, gradeDocsPromptDefault)

        # Assemble output
        # Summary statistics
        dfOutput = {'question': currentDataSet['question'], 'answer': currentDataSet['answer'],
                    'predictedAnswer': predictions[0]['result'], 'answerScore': [{'score': 1 if "Incorrect" not in text else 0,
                                'justification': text} for text in [g['text'] for g in gradedAnswer]], 
                                'retrievalScore': [{'score': 1 if "Incorrect" not in text else 0,
                                'justification': text} for text in [g['text'] for g in gradedRetrieval]],
                    'latency': latency}
        
        #yield dfOutput

        # Add to dataframe
        d = pd.concat([d, pd.DataFrame(dfOutput)], axis=0)

    d_dict = d.to_dict('records')
    return d_dict

def main(runDocs: RunDocs) -> str:
    evaluatorQaData,totalQuestions,promptStyle,documentId,splitMethods,chunkSizes,overlaps,retrieverType,reEvaluate,topK,model,fileName, embeddingModelType, temperature, tokenLength = runDocs

    evaluatorDataIndexName = "evaluatordata"
    evaluatorRunIndexName = "evaluatorrun"
    evaluatorRunResultIndexName = "evaluatorrunresult"

    qaChainPrompt, promptStyleFast, promptStyleBias, promptStyleGrading, promptStyleDefault, gradeDocsPromptFast, gradeDocsPromptDefault = getPrompts()

    logging.info("Python HTTP trigger function processed a request.")
       
    if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"{OpenAiEndPoint}"

            llm = AzureChatOpenAI(
                    openai_api_base=openai.api_base,
                    openai_api_version=OpenAiVersion,
                    deployment_name=OpenAiChat,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    openai_api_type="azure",
                    max_tokens=tokenLength)
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

    # Select retriever
    createEvaluatorResultIndex(SearchService, SearchKey, evaluatorRunResultIndexName)
    # Check if we already have runId for this document
    r = searchEvaluatorRunIdIndex(SearchService, SearchKey, evaluatorRunResultIndexName, documentId)
    if r.get_count() == 0:
        runId = str(uuid.uuid4())
    else:
        for run in r:
            runId = run['runId']
            break
    for splitMethod in splitMethods:
        for chunkSize in chunkSizes:
            for overlap in overlaps:
                # Verify if we have created the Run ID
                r = searchEvaluatorRunIndex(SearchService, SearchKey, evaluatorRunResultIndexName, documentId, retrieverType, 
                                        promptStyle, splitMethod, chunkSize, overlap)
                if r.get_count() == 0 or reEvaluate:
                    # Create the Run ID
                    print("Processing: ", documentId, retrieverType, promptStyle, splitMethod, chunkSize, overlap)
                    runIdData = []
                    subRunId = str(uuid.uuid4())
                
                    retriever = CognitiveSearchVsRetriever(contentKey="contentVector",
                                serviceName=SearchService,
                                apiKey=SearchKey,
                                indexName=evaluatorDataIndexName,
                                topK=topK,
                                splitMethod = splitMethod,
                                model = model,
                                chunkSize = chunkSize,
                                overlap = overlap,
                                openAiEndPoint = OpenAiEndPoint,
                                openAiKey = OpenAiKey,
                                openAiVersion = OpenAiVersion,
                                openAiApiKey = OpenAiApiKey,
                                documentId = documentId,
                                openAiEmbedding=OpenAiEmbedding,
                                returnFields=["id", "content", "sourceFile", "splitMethod", "chunkSize", "overlap", "model", "modelType", "documentId"]
                                )
                    vectorStoreChain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, 
                                                    chain_type_kwargs={"prompt": qaChainPrompt})
                    runEvaluations = runEvaluator(llm, evaluatorQaData, totalQuestions, vectorStoreChain, retriever, promptStyle, 
                                                  promptStyleFast, promptStyleBias, promptStyleGrading, promptStyleDefault,
                                                    gradeDocsPromptFast, gradeDocsPromptDefault)
                    #yield runEvaluations
                    
                    runEvaluationData = []
                    for runEvaluation in runEvaluations:
                            runEvaluationData.append({
                                "id": str(uuid.uuid4()),
                                "runId": runId,
                                "subRunId": subRunId,
                                "documentId": documentId,
                                "retrieverType": retrieverType,
                                "promptStyle": promptStyle,
                                "splitMethod": splitMethod,
                                "chunkSize": chunkSize,
                                "overlap": overlap,
                                "question": runEvaluation['question'],
                                "answer": runEvaluation['answer'],
                                "predictedAnswer": runEvaluation['predictedAnswer'],
                                "answerScore": json.dumps(runEvaluation['answerScore']),
                                "retrievalScore": json.dumps(runEvaluation['retrievalScore']),
                                "latency": str(runEvaluation['latency']),
                            })
                    indexDocs(SearchService, SearchKey, evaluatorRunResultIndexName, runEvaluationData)
                    
    return "Success"
import logging, os
from Utilities.envVars import *
from Utilities.envVars import *
# Import required libraries
from Utilities.evaluator import indexDocs
from langchain.chains import QAGenerationChain
import pandas as pd
from collections import namedtuple
import uuid
import tempfile
from Utilities.azureBlob import getBlob, getFullPath
from langchain.document_loaders import PDFMinerLoader
from Utilities.evaluator import createEvaluatorQaSearchIndex, searchEvaluatorQaData
from json import JSONDecodeError
import random
import itertools
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI

QaData = namedtuple('QaData', ['documentId', 'regenerateQa', 'fileName' ])

def generateEvaluation(llm, embeddingModelType, temperature, tokenLength, data, chunk):
    # Generate random starting index in the doc to draw question from
    noOfChar = len(data)
    startingIndex = random.randint(0, noOfChar-chunk)
    subSequence = data[startingIndex:startingIndex+chunk]
    # Set up QAGenerationChain chain using GPT 3.5 as default
    chain = QAGenerationChain.from_llm(llm)
    evalSet = []
    # Catch any QA generation errors and re-try until QA pair is generated
    awaitingAnswer = True
    while awaitingAnswer:
        try:
            qaPair = chain.run(subSequence)
            evalSet.append(qaPair)
            awaitingAnswer = False
        except JSONDecodeError:
            startingIndex = random.randint(0, noOfChar-chunk)
            subSequence = data[startingIndex:startingIndex+chunk]
    evalPair = list(itertools.chain.from_iterable(evalSet))
    return evalPair  

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

def main(qaData: QaData) -> list:
    documentId, regenerateQa, fileName, embeddingModelType, temperature, tokenLength, generateTotalQuestions = qaData
    logging.info("Python HTTP trigger function processed a request.")
    evaluatorQaDataIndexName = "evaluatorqadata"
    
    # Process our fileName
    # TODO : Add support for other file types
    logging.info("Load Document from Blob Storage")
    rawDocs = blobLoad(OpenAiDocConnStr, OpenAiEvaluatorContainer, fileName)
    
    if (embeddingModelType == 'azureopenai'):
            llm = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat,
                        temperature=temperature,
                        api_key=OpenAiKey,
                        max_tokens=tokenLength)
            logging.info("LLM Setup done")
    elif embeddingModelType == "openai":
            llm = ChatOpenAI(temperature=temperature,
                api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=tokenLength)
            
    # Now that we have indexed the documents, let's go ahead and create the set of the QA pairs for the document and store that in the index
    # We will use the same QA Pair for evaluating all the different chunk sizes and overlap
    # Check first if we have already generated the QA pairs for this document
    # If we have, then we will just use that
    # If not, then we will generate the QA pairs and store them in the index
    logging.info("Generate QA Pairs")
    # Create the Evaluator Document Search Index
    createEvaluatorQaSearchIndex(SearchService, SearchKey, evaluatorQaDataIndexName)
    logging.info("Search Generate QA Index")
    r = searchEvaluatorQaData(SearchService, SearchKey, evaluatorQaDataIndexName, documentId)
    evaluatorQaData = []
    if r.get_count() == 0 or regenerateQa:
        generatedQAPairs = []
        for i in range(generateTotalQuestions):
            # Generate one question
            logging.info("Generate QA Pair")
            evalPair = generateEvaluation(llm, embeddingModelType, temperature, tokenLength, rawDocs[0].page_content, 3000)
            if len(evalPair) == 0:
                # Error in eval generation
                continue
            else:
                # This returns a list, so we unpack to dict
                evalPair = evalPair[0]
                generatedQAPairs.append(evalPair)
        # Insert the document metadata
        if regenerateQa:
            i=0
            for qa in r:
                evaluatorQaData.append({
                    "id": qa['id'],
                    "documentId": qa['documentId'],
                    "questionId": qa['questionId'],
                    "question": generatedQAPairs[i]['question'],
                    "answer": generatedQAPairs[i]['answer'],
                })
                i+=1
        else:
            for qa in generatedQAPairs:
                evaluatorQaData.append({
                    "id": str(uuid.uuid4()),
                    "documentId": documentId,
                    "questionId": str(uuid.uuid4()),
                    "question": qa['question'],
                    "answer": qa['answer'],
                })
        logging.info("Indexing QA Pairs")
        indexDocs(SearchService, SearchKey, evaluatorQaDataIndexName, evaluatorQaData)
    else:
        logging.info("Found QA Pairs")
        for qa in r:
                evaluatorQaData.append({
                    "id": qa['id'],
                    "documentId": qa['documentId'],
                    "questionId": qa['questionId'],
                    "question": qa['question'],
                    "answer": qa['answer'],
                })
    return evaluatorQaData
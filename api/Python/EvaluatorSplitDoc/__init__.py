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

SplitDocs = namedtuple('SplitDoc', ['splitMethods', 'chunkSizes', 'overlaps', 
                                           'model', 'embeddingModelType', 'fileName' ])

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

def main(splitDocs: SplitDocs) -> str:
    # Create the Evaluator Data Search Index to store our vector Data
    logging.info("Split Document for Evaluation")
    splitMethods, chunkSizes, overlaps, model, embeddingModelType, fileName = splitDocs
    evaluatorDocumentIndex = "evaluatordocument"
    evaluatorDataIndexName = "evaluatordata"

    # Process our fileName
    # TODO : Add support for other file types
    logging.info("Load Document from Blob Storage")
    rawDocs = blobLoad(OpenAiDocConnStr, OpenAiEvaluatorContainer, fileName)
    # Create the Evaluator Data Search Index

    # Check if we already have document inserted into our index
    # Create the Evaluator Document Search Index
    logging.info("Create Evaluator Document Search Index")
    createEvaluatorDocumentSearchIndex(SearchService, SearchKey, evaluatorDocumentIndex)
    logging.info("Search for Document")
    documentResponse = searchEvaluatorDocument(SearchService, SearchKey, evaluatorDocumentIndex, fileName)
    if documentResponse.get_count() > 0:
        for doc in documentResponse:
            documentId = doc["documentId"]
            break
    else:
        documentId = str(uuid.uuid4())
        # Insert the document metadata
        evaluatorDocument = []
        evaluatorDocument.append({
                "id": str(uuid.uuid4()),
                "documentId": documentId,
                "documentName": fileName,
                "sourceFile": fileName,
            })
        indexDocs(SearchService, SearchKey, evaluatorDocumentIndex, evaluatorDocument)

    logging.info("Create Evaluator Data Search Index")
    createEvaluatorDataSearchIndex(SearchService, SearchKey, evaluatorDataIndexName)
    for splitMethod in splitMethods:
        for chunkSize in chunkSizes:
            for overlap in overlaps:
                # Check if we already have data inserted into our index
                logging.info("Search for Document Indexed Data")
                dataResponse = searchEvaluatorDocumentIndexedData(SearchService, SearchKey, evaluatorDataIndexName, documentId, 
                                                    splitMethod, chunkSize, overlap)
                if dataResponse.get_count() == 0:
                    logging.info("Processing Split Method: " + splitMethod + " Chunk Size: " + chunkSize + " Overlap: " + overlap)
                    # Split the document into chunks of 500 characters & 0 overlap
                    if splitMethod == "RecursiveCharacterTextSplitter":
                        logging.info("Create Splitter")
                        splitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(overlap))
                        logging.info("Split Document")
                        docs = splitter.split_documents(rawDocs)

                    logging.info("Index Document Data")
                    indexEvaluatorDataSections(OpenAiService, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, 
                                SearchKey, embeddingModelType, OpenAiEmbedding, fileName, evaluatorDataIndexName, docs, 
                                splitMethod, chunkSize, overlap, model, embeddingModelType, documentId)
    return documentId
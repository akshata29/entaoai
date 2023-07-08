import logging, json, os
import azure.functions as func
from Utilities.envVars import *
import azure.durable_functions as df
from Utilities.envVars import *
# Import required libraries
import json
import pandas as pd
from collections import namedtuple
from Utilities.azureBlob import getBlob, getFullPath

def EvaluatorCore(context: df.DurableOrchestrationContext):
    logging.info("Start EvaluatorCore")
    try:
        input = context.get_input()
        embeddingModelType = input['embeddingModelType']
        temperature = 0
        tokenLength = 1000
        fileName = input['fileName']
        regenerateQa = False
        reEvaluate = False
        topK = 3
        totalQuestions = input['totalQuestions']
        retrieverType = input['retrieverType']
        promptStyle = input['promptStyle']
        splitMethods = input['splitMethods']
        chunkSizes = input['chunkSizes']
        overlaps = input['overlaps']

        # Constant Variables
        # Process the document and create the chunked Index with different split methods, chunk sizes and overlaps.
        # Eventually we will add support for different models
        # Add more Split Methods
        #splitMethods = ["RecursiveCharacterTextSplitter"]
        model = "GPT3.5"
        #chunkSizes = ['500', '1000', '1500', '2000']
        #overlaps = ['0', '50', '100', '150']
        result = []

        SplitDocs = namedtuple('SplitDoc', ['splitMethods', 'chunkSizes', 'overlaps', 
                                           'model', 'embeddingModelType', 'fileName' ])
        splitDocs = SplitDocs(splitMethods=splitMethods,chunkSizes=chunkSizes,overlaps=overlaps,
                            model=model, embeddingModelType=embeddingModelType,
                            fileName=fileName)
        
        logging.info("Split Document Activity")
        context.set_custom_status = "Completed Split Document Activity"
        documentId = yield context.call_activity('EvaluatorSplitDoc', splitDocs)
        logging.info("Document Id: " + documentId)

        QaData = namedtuple('QaData', ['documentId', 'regenerateQa', 'fileName', 'embeddingModelType', 'temperature', 'tokenLength', 'generateTotalQuestions'])
        qaData = QaData(documentId=documentId,regenerateQa=regenerateQa, fileName=fileName, embeddingModelType=embeddingModelType, 
                        temperature=temperature, tokenLength=tokenLength, generateTotalQuestions=int(totalQuestions))
        logging.info("Generate Qa Activity")
        context.set_custom_status = "Completed Generate Qa Activity"
        evaluatorQaData = yield context.call_activity('EvaluatorGenerateQa', qaData)
        #logging.info("Evaluator Qa Data: " + str(evaluatorQaData))

        RunDocs = namedtuple('RunDoc', ['evalatorQaData', 'totalQuestions', 'promptStyle', 'documentId', 
                                        'splitMethods', 'chunkSizes', 'overlaps',
                                        'retrieverType', 'reEvaluate', 'topK', 'model', 'fileName',
                                        'embeddingModelType', 'temperature', 'tokenLength'])
        runDocs = RunDocs(evalatorQaData=evaluatorQaData, totalQuestions=totalQuestions, promptStyle=promptStyle,
                            documentId=documentId, splitMethods=splitMethods, chunkSizes=chunkSizes, overlaps=overlaps,
                            retrieverType=retrieverType, reEvaluate=reEvaluate, topK=topK, model=model, fileName=fileName,
                            embeddingModelType=embeddingModelType, temperature=temperature, tokenLength=tokenLength)
        logging.info("Evaluator Run Doc Activity")
        evaluatedResult = yield context.call_activity('EvaluatorRunDoc', runDocs)
        context.set_custom_status = "Completed Evaluator Run Doc Activity"

        return [result]
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )
    
main = df.Orchestrator.create(EvaluatorCore)
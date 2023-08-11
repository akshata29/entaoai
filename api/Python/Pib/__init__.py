import openai
from Utilities.envVars import *
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.llms.openai import AzureOpenAI, OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.utilities import BingSearchAPIWrapper
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from langchain.prompts import PromptTemplate
from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from Utilities.pibCopilot import indexDocs, createPressReleaseIndex, findEarningCalls, mergeDocs, createPibIndex, findPibData, performEarningCallCogSearch
from Utilities.pibCopilot import deletePibData, findEarningCallsBySymbol
from Utilities.pibCopilot import indexEarningCallSections, createEarningCallVectorIndex, createEarningCallIndex, performCogSearch, createSecFilingIndex, findSecFiling
from Utilities.pibCopilot import findLatestSecFilings, indexSecFilingsSections, createSecFilingsVectorIndex
import typing
from Utilities.fmp import *
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import logging, json, os
import uuid
import azure.functions as func
import time
from Utilities.cogSearchRetriever import CognitiveSearchRetriever
from langchain.chains import RetrievalQA
from langchain.chains import LLMChain
from Utilities.azureBlob import upsertMetadata, getBlob, getFullPath, copyBlob, copyS3Blob
import tempfile
from langchain.document_loaders import PDFMinerLoader

def processStep1(pibIndexName, cik, step, symbol, temperature, llm, today):
    s1Data = []
    r = findPibData(SearchService, SearchKey, pibIndexName, cik, step, returnFields=['id', 'symbol', 'cik', 'step', 'description', 'insertedDate',
                                                                    'pibData'])
    
    logging.info(f"Found {r.get_count()} records for {symbol} in {pibIndexName}")
    if r.get_count() == 0:
        step1Profile = []
        profile = companyProfile(apikey=FmpKey, symbol=symbol)
        df = pd.DataFrame.from_dict(pd.json_normalize(profile))
        df.fillna("",inplace=True)
        sData = {
                'id' : str(uuid.uuid4()),
                'symbol': symbol,
                'cik': cik,
                'step': step,
                'description': 'Company Profile',
                'insertedDate': today.strftime("%Y-%m-%d"),
                'pibData' : str(df[['symbol', 'mktCap', 'companyName', 'currency', 'cik', 'isin', 'exchange', 'industry', 'sector', 'address', 'city', 'state', 'zip', 'website', 'description']].to_dict('records'))
        }
        step1Profile.append(sData)
        s1Data.append(sData)
        # Insert data into pibIndex
        mergeDocs(SearchService, SearchKey, pibIndexName, step1Profile)

        # Get the list of all executives and generate biography for each of them
        executives = keyExecutives(apikey=FmpKey, symbol=symbol)
        df = pd.DataFrame.from_dict(pd.json_normalize(executives),orient='columns')
        df = df.drop_duplicates(subset='name', keep="first")

        step1Biography = []
        step1Executives = []
        #### With the company profile and key executives, we can ask Bing Search to get the biography of the all Key executives and 
        # ask OpenAI to summarize it - Public Data
        for executive in executives:
            name = executive['name']
            title = executive['title']
            query = f"Give me brief biography of {name} who is {title} at {symbol}. Biography should be restricted to {symbol} and summarize it as 2 paragraphs."
            qaPromptTemplate = """
                Rephrase the following question asked by user to perform intelligent internet search
                {query}
                """
            
            qaPrompt = PromptTemplate(input_variables=["query"],template=qaPromptTemplate)
            chain = LLMChain(llm=llm, prompt=qaPrompt)
            q = chain.run(query=query)
            bingSearch = BingSearchAPIWrapper(k=20)
            results = bingSearch.run(query=q)
            logging.info(f"Generate Summary for {q}")
            chain = load_summarize_chain(llm, chain_type="stuff")
            docs = [Document(page_content=results)]
            summary = chain.run(docs)
            step1Executives.append({
                "name": name,
                "title": title,
                "biography": summary
            })

        sData = {
                'id' : str(uuid.uuid4()),
                'symbol': symbol,
                'cik': cik,
                'step': step,
                'description': 'Biography of Key Executives',
                'insertedDate': today.strftime("%Y-%m-%d"),
                'pibData' : str(step1Executives)
        }
        step1Biography.append(sData)
        s1Data.append(sData)
        mergeDocs(SearchService, SearchKey, pibIndexName, step1Biography)
    elif r.get_count() == 1:
        for s in r:
            logging.info(f"Found Company Profile for {symbol}")
            if s['description'] == 'Company Profile':
                s1Data.append(
                    {
                        'id' : s['id'],
                        'symbol': s['symbol'],
                        'cik': s['cik'],
                        'step': s['step'],
                        'description': s['description'],
                        'insertedDate': s['insertedDate'],
                        'pibData' : s['pibData']
                    })
                
                # Get the list of all executives and generate biography for each of them
                executives = keyExecutives(apikey=FmpKey, symbol=symbol)
                df = pd.DataFrame.from_dict(pd.json_normalize(executives),orient='columns')
                df = df.drop_duplicates(subset='name', keep="first")

                step1Biography = []
                step1Executives = []
                #### With the company profile and key executives, we can ask Bing Search to get the biography of the all Key executives and 
                # ask OpenAI to summarize it - Public Data
                for executive in executives:
                    name = executive['name']
                    title = executive['title']
                    query = f"Give me brief biography of {name} who is {title} at {symbol}. Biography should be restricted to {symbol} and summarize it as 2 paragraphs."
                    qaPromptTemplate = """
                        Rephrase the following question asked by user to perform intelligent internet search
                        {query}
                        """
                    qaPrompt = PromptTemplate(input_variables=["query"],template=qaPromptTemplate)
                    chain = LLMChain(llm=llm, prompt=qaPrompt)
                    q = chain.run(query=query)
                    bingSearch = BingSearchAPIWrapper(k=25)
                    results = bingSearch.run(query=q)
                    logging.info(f"Generate Summary for {q}")
                    chain = load_summarize_chain(llm, chain_type="stuff")
                    docs = [Document(page_content=results)]
                    summary = chain.run(docs)
                    step1Executives.append({
                        "name": name,
                        "title": title,
                        "biography": summary
                    })

                sData = {
                        'id' : str(uuid.uuid4()),
                        'symbol': symbol,
                        'cik': cik,
                        'step': step,
                        'description': 'Biography of Key Executives',
                        'insertedDate': today.strftime("%Y-%m-%d"),
                        'pibData' : str(step1Executives)
                }
                step1Biography.append(sData)
                s1Data.append(sData)
                mergeDocs(SearchService, SearchKey, pibIndexName, step1Biography)
            elif s['description'] == 'Biography of Key Executives':
                logging.info(f"Found Biography of Key Executives for {symbol}")
                s1Data.append(
                    {
                        'id' : s['id'],
                        'symbol': s['symbol'],
                        'cik': s['cik'],
                        'step': s['step'],
                        'description': s['description'],
                        'insertedDate': s['insertedDate'],
                        'pibData' : s['pibData']
                    })
                
                step1Profile = []
                profile = companyProfile(apikey=FmpKey, symbol=symbol)
                df = pd.DataFrame.from_dict(pd.json_normalize(profile))
                sData = {
                        'id' : str(uuid.uuid4()),
                        'symbol': symbol,
                        'cik': cik,
                        'step': step,
                        'description': 'Company Profile',
                        'insertedDate': today.strftime("%Y-%m-%d"),
                        'pibData' : str(df[['symbol', 'mktCap', 'companyName', 'currency', 'cik', 'isin', 'exchange', 'industry', 'sector', 'address', 'city', 'state', 'zip', 'website', 'description']].to_dict('records'))
                }
                step1Profile.append(sData)
                s1Data.append(sData)
                # Insert data into pibIndex
                mergeDocs(SearchService, SearchKey, pibIndexName, step1Profile)
    else:
        for s in r:
            s1Data.append(
                {
                    'id' : s['id'],
                    'symbol': s['symbol'],
                    'cik': s['cik'],
                    'step': s['step'],
                    'description': s['description'],
                    'insertedDate': s['insertedDate'],
                    'pibData' : s['pibData']
                })
    
    return s1Data

def getEarningCalls(totalYears, historicalYear, symbol, today):
    # Call the paid data (FMP) API
    # Get the earning call transcripts for the last 3 years and merge documents into the index.
    i = 0
    earningsData = []
    earningIndexName = 'earningcalls'
    try:
        # Create the index if it does not exist
        createEarningCallIndex(SearchService, SearchKey, earningIndexName)
        # Get the list of all earning calls available
        earningCallDates = earningCallsAvailableDates(apikey=FmpKey, symbol=symbol)
        if len(earningCallDates) > 0:
            quarter = earningCallDates[0][0]
            year = earningCallDates[0][1]
            r = findEarningCalls(SearchService, SearchKey, earningIndexName, symbol, str(quarter), str(year), returnFields=['id', 'symbol', 
                                'quarter', 'year', 'callDate', 'content'])
            if r.get_count() == 0:
                insertEarningCall = []
                earningTranscript = earningCallTranscript(apikey=FmpKey, symbol=symbol, year=str(year), quarter=quarter)
                for transcript in earningTranscript:
                    symbol = transcript['symbol']
                    quarter = transcript['quarter']
                    year = transcript['year']
                    callDate = transcript['date']
                    content = transcript['content']
                    id = f"{symbol}-{year}-{quarter}"
                    earningRecord = {
                        "id": id,
                        "symbol": symbol,
                        "quarter": str(quarter),
                        "year": str(year),
                        "callDate": callDate,
                        "content": content,
                        #"inserteddate": datetime.now(central).strftime("%Y-%m-%d"),
                    }
                    earningsData.append(earningRecord)
                    insertEarningCall.append(earningRecord)
                    mergeDocs(SearchService, SearchKey, earningIndexName, insertEarningCall)
            else:
                logging.info(f"Found {r.get_count()} records for {symbol} for {quarter} {str(year)}")
                for s in r:
                    record = {
                            'id' : s['id'],
                            'symbol': s['symbol'],
                            'quarter': s['quarter'],
                            'year': s['year'],
                            'callDate': s['callDate'],
                            'content': s['content']
                        }
                    earningsData.append(record)
        else:
            logging.info(f"No earning calls found for {symbol}")
            return earningsData
                
        logging.info(f"Total records found for {symbol} : {len(earningsData)}")

        return earningsData[-1]
    except Exception as e:
        logging.error(f"Error occured while processing {symbol} : {e}")

def getPressReleases(today, symbol):
    # For now we are calling API to get data, but otherwise we need to ensure the data is not persisted in our 
    # index repository before calling again, if it is persisted then we need to delete it first
    counter = 0
    pressReleasesList = []
    pressReleaseIndexName = 'pressreleases'
    # Create the index if it does not exist
    createPressReleaseIndex(SearchService, SearchKey, pressReleaseIndexName)
    print(f"Processing ticker : {symbol}")
    pr = pressReleases(apikey=FmpKey, symbol=symbol, limit=25)
    for pressRelease in pr:
        symbol = pressRelease['symbol']
        releaseDate = pressRelease['date']
        title = pressRelease['title']
        content = pressRelease['text']
        todayYmd = today.strftime("%Y-%m-%d")
        id = f"{symbol}-{counter}"
        pressReleasesList.append({
            "id": id,
            "symbol": symbol,
            "releaseDate": releaseDate,
            "title": title,
            "content": content,
        })
        counter = counter + 1

    mergeDocs(SearchService, SearchKey, pressReleaseIndexName, pressReleasesList)
    return pressReleasesList

# Helper function to find the answer to a question
def findAnswer(chainType, topK, symbol, quarter, year, question, indexName, embeddingModelType, llm):
    # Since we already index our document, we can perform the search on the query to retrieve "TopK" documents
    r = performEarningCallCogSearch(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey, embeddingModelType, 
        OpenAiEmbedding, symbol, str(quarter), str(year), question, indexName, topK, returnFields=['id', 'symbol', 'quarter', 'year', 'callDate', 'content'])

    if r == None:
        docs = [Document(page_content="No results found")]
    else :
        docs = [
            Document(page_content=doc['content'], metadata={"id": doc['id'], "source": ''})
            for doc in r
            ]

    if chainType == "map_reduce":
        # Prompt for MapReduce
        qaTemplate = """Use the following portion of a long document to see if any of the text is relevant to answer the question.
                Return any relevant text.
                {context}
                Question: {question}
                Relevant text, if any :"""

        qaPrompt = PromptTemplate(
            template=qaTemplate, input_variables=["context", "question"]
        )

        combinePromptTemplate = """Given the following extracted parts of a long document and a question, create a final answer.
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

        qaChain = load_qa_with_sources_chain(llm, chain_type=chainType, question_prompt=qaPrompt, 
                                            combine_prompt=combinePrompt, 
                                            return_intermediate_steps=True)
        answer = qaChain({"input_documents": docs, "question": question})
        outputAnswer = answer['output_text']

    elif chainType == "stuff":
    # Prompt for ChainType = Stuff
        template = """
                Given the following extracted parts of a long document and a question, create a final answer. 
                If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
                If the answer is not contained within the text below, say \"I don't know\".

                QUESTION: {question}
                =========
                {summaries}
                =========
                """
        qaPrompt = PromptTemplate(template=template, input_variables=["summaries", "question"])
        qaChain = load_qa_with_sources_chain(llm, chain_type=chainType, prompt=qaPrompt)
        answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
        outputAnswer = answer['output_text']
    elif chainType == "default":
        # Default Prompt
        qaChain = load_qa_with_sources_chain(llm, chain_type="stuff")
        answer = qaChain({"input_documents": docs, "question": question}, return_only_outputs=True)
        outputAnswer = answer['output_text']

    return outputAnswer

def processStep2(pibIndexName, cik, step, symbol, llm, today, embeddingModelType, totalYears, 
                 historicalYear):
    r = findPibData(SearchService, SearchKey, pibIndexName, cik, step, returnFields=['id', 'symbol', 'cik', 'step', 'description', 'insertedDate',
                                                                   'pibData'])
    content = ''
    latestCallDate = ''
    s2Data = []
    if r.get_count() == 0:

        #Let's just use the latest earnings call transcript to create the documents that we want to use it 
        #for generative AI tasks
        try:
            latestEarningsData = getEarningCalls(totalYears, historicalYear, symbol, today)
            content = latestEarningsData['content']
            latestCallDate = latestEarningsData['callDate']
            year = latestEarningsData['year']
            quarter = latestEarningsData['quarter']
            splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=1000)
            rawDocs = splitter.create_documents([content])
            docs = splitter.split_documents(rawDocs)
            logging.info("Number of documents chunks generated from Call transcript : " + str(len(docs)))
        except Exception as e:
            logging.info("Error in splitting the earning call transcript : ", e)
            return s2Data, content, latestCallDate

        # Store the last index of the earning call transcript in vector Index
        earningVectorIndexName = 'latestearningcalls'
        createEarningCallVectorIndex(SearchService, SearchKey, earningVectorIndexName)
        # Check if we already have the data store, if not then create it
        indexEarningCallSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey,
                                embeddingModelType, OpenAiEmbedding, earningVectorIndexName, docs,
                                latestCallDate, latestEarningsData['symbol'], latestEarningsData['year'],
                                latestEarningsData['quarter'])


        logging.info("Completed latest earning call transcript indexing")
        earningCallQa = []
        
        commonQuestions = [
            "What are some of the current and looming threats to the business?",
            "What is the debt level or debt ratio of the company right now?",
            "How do you feel about the upcoming product launches or new products?",
            "How are you managing or investing in your human capital?",
            "How do you track the trends in your industry?",
            "Are there major slowdowns in the production of goods?",
            "How will you maintain or surpass this performance in the next few quarters?",
            "What will your market look like in five years as a result of using your product or service?",
            "How are you going to address the risks that will affect the long-term growth of the company?",
            "How is the performance this quarter going to affect the long-term goals of the company?"
        ]

        for question in commonQuestions:
            answer = findAnswer('stuff', 3, symbol, str(quarter), str(year), question, earningVectorIndexName, embeddingModelType, llm)
            if "I don't know" not in answer:
                earningCallQa.append({"question": question, "answer": answer})
        
        logging.info("Completed latest earning call transcript Common QA")

        commonQuestions = [
                "Provide key information about revenue for the quarter",
                "Provide key information about profits and losses (P&L) for the quarter",
                "Provide key information about industry trends for the quarter",
                "Provide key information about business trends discussed on the call",
                "Provide key information about risk discussed on the call",
                "Provide key information about AI discussed on the call",
                "Provide any information about mergers and acquisitions (M&A) discussed on the call.",
                "Provide key information about guidance discussed on the call"
            ]

        for question in commonQuestions:
            answer = findAnswer('stuff', 3, symbol, str(quarter), str(year), question, earningVectorIndexName, embeddingModelType, llm)
            if "I don't know" not in answer:
                earningCallQa.append({"question": question, "answer": answer})

        logging.info("Completed latest earning call transcript Specific QA")

        promptTemplate = """You are an AI assistant tasked with summarizing financial information from earning call transcript. 
            Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
            Please generate a concise and comprehensive summary between 5-7 paragraphs on each of the following numbered topics.  Your response should include the topic as part of the summary.
            1. Financial Results: Please provide a summary of the financial results.
            2. Business Highlights: Please provide a summary of the business highlights.
            3. Future Outlook: Please provide a summary of the future outlook.
            4. Business Risks: Please provide a summary of the business risks.
            5. Management Positive Sentiment: Please provide a summary of the what management is confident about.
            6. Management Negative Sentiment: Please provide a summary of the what management is concerned about.
            Please remember to use clear language and maintain the integrity of the original information without missing any important details:
            {text}
            """
        customPrompt = PromptTemplate(template=promptTemplate, input_variables=["text"])
        chainType = "map_reduce"
        summaryChain = load_summarize_chain(llm, chain_type=chainType, return_intermediate_steps=False, 
                                    combine_prompt=customPrompt)
        summaryOutput = summaryChain({"input_documents": docs}, return_only_outputs=True)
        output = summaryOutput['output_text']
        logging.info("Completed latest earning call transcript summarization")

        formattedOutput = output.splitlines()
        while("" in formattedOutput):
            formattedOutput.remove("")
        for summary in formattedOutput:
            splitSummary = summary.split(":")
            try:
                question = splitSummary[0]
                answer = splitSummary[1]
                earningCallQa.append({"question": question, "answer": answer})
            except:
                continue

        s2Data.append({
                    'id' : str(uuid.uuid4()),
                    'symbol': symbol,
                    'cik': cik,
                    'step': step,
                    'description': 'Earning Call Q&A',
                    'insertedDate': today.strftime("%Y-%m-%d"),
                    'pibData' : str(earningCallQa)
        })

        promptTemplate = """You are an AI assistant tasked with summarizing financial information from earning call transcript. 
        Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive summary between 5-7 paragraphs and maintain the continuity.  
        Ensure your summary includes the key information from the transcript like future outlook, business risk, 
        management concerns.
        {text}
            """
        customPrompt = PromptTemplate(template=promptTemplate, input_variables=["text"])
        logging.info("Starting latest earning call transcript summarization - Stuff or MapReduce")
        try:
            chainType = "stuff"
            summaryChain = load_summarize_chain(llm, chain_type=chainType, prompt=customPrompt)
            summaryOutput = summaryChain({"input_documents": docs}, return_only_outputs=True)
            output = summaryOutput['output_text']
            logging.info("Completed latest earning call transcript summarization - Stuff")
        except:
            chainType = "map_reduce"
            summaryChain = load_summarize_chain(llm, chain_type=chainType, combine_prompt=customPrompt)
            summaryOutput = summaryChain({"input_documents": docs}, return_only_outputs=True)
            output = summaryOutput['output_text']
            logging.info("Completed latest earning call transcript summarization - MapReduce")
        
        s2Data.append({
                    'id' : str(uuid.uuid4()),
                    'symbol': symbol,
                    'cik': cik,
                    'step': step,
                    'description': 'Earning Call Summary',
                    'insertedDate': today.strftime("%Y-%m-%d"),
                    'pibData' : str([{"summary": output}])
        })

        mergeDocs(SearchService, SearchKey, pibIndexName, s2Data)
    else:
        logging.info('Found existing data')
        for s in r:
            s2Data.append(
                {
                    'id' : s['id'],
                    'symbol': s['symbol'],
                    'cik': s['cik'],
                    'step': s['step'],
                    'description': s['description'],
                    'insertedDate': s['insertedDate'],
                    'pibData' : s['pibData']
                })
        r = findEarningCallsBySymbol(SearchService, SearchKey, "earningcalls", symbol, returnFields=['id', 'content', 'callDate'])
        if r.get_count() > 0:
            logging.info("Total earning calls found: " + str(r.get_count()))
            existingEarningCalls = []
            for s in r:
                existingEarningCalls.append({"callDate": s['callDate'], "content": s['content']})
            df = pd.DataFrame(existingEarningCalls)
            df['callDate'] = pd.to_datetime(df['callDate'])
            df = df.sort_values(by='callDate', ascending=False)
            latestCallDate = df.iloc[0]['callDate']
            content = df.iloc[0]['content']

    return s2Data, content, latestCallDate

def summarizePressReleases(llm, docs):
    promptTemplate = """You are an AI assistant tasked with summarizing company's press releases and performing sentiments on those. 
                Your summary should accurately capture the key information in the press-releases while avoiding the omission of any domain-specific words. 
                Please generate a concise and comprehensive summary and sentiment with score with range of 0 to 10. 
                Your response should be in JSON object with following keys.  All JSON properties are required.
                summary: 
                sentiment:
                sentiment score: 
                {text}
                """
    customPrompt = PromptTemplate(template=promptTemplate, input_variables=["text"])
    chainType = "stuff"
    summaryChain = load_summarize_chain(llm, chain_type=chainType, prompt=customPrompt)
    summary = summaryChain({"input_documents": docs}, return_only_outputs=True)
    outputAnswer = summary['output_text']
    return outputAnswer

def processStep3(symbol, cik, step, llm, pibIndexName, today):
    # With the data indexed, let's summarize the information
    s3Data = []
    r = findPibData(SearchService, SearchKey, pibIndexName, cik, step, returnFields=['id', 'symbol', 'cik', 'step', 'description', 'insertedDate',
                                                                   'pibData'])
    if r.get_count() == 0:
        logging.info('No existing data found')
        pressReleasesList = getPressReleases(today, symbol)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=50)
        # We will process only last 25 press releases
        rawPressReleasesDoc = [Document(page_content=t['content']) for t in pressReleasesList[:25]]
        pressReleasesDocs = splitter.split_documents(rawPressReleasesDoc)
        logging.info("Number of documents chunks generated from Press releases : " + str(len(pressReleasesDocs)))


        pressReleasesPib = []
        last25PressReleases = pressReleasesList[:25]
        last25PressReleasesDocs = pressReleasesDocs[:25]
        i = 0
        for pDocs in last25PressReleasesDocs:
            try:
                logging.info("Processing Press Release: " + str(i))
                outputAnswer = summarizePressReleases(llm, [pDocs])
                jsonStep = json.loads(outputAnswer)
                pressReleasesPib.append({
                        "releaseDate": last25PressReleases[i]['releaseDate'],
                        "title": last25PressReleases[i]['title'],
                        "summary": jsonStep['summary'],
                        "sentiment": jsonStep['sentiment'],
                        "sentimentScore": jsonStep['sentiment score']
                })
                i = i + 1
            except:
                logging.info("Error processing Press Release: " + str(i))
                i = i + 1
                continue

        # We are deleting the data as the Press-releases could be dynamic and we want the latest data
        # deletePibData(SearchService, SearchKey, pibIndexName, cik, step, returnFields=['id', 'symbol', 'cik', 'step', 'description', 'insertedDate',
        #                                                                'pibData'])
        s3Data.append({
                        'id' : str(uuid.uuid4()),
                        'symbol': symbol,
                        'cik': cik,
                        'step': step,
                        'description': 'Press Releases',
                        'insertedDate': today.strftime("%Y-%m-%d"),
                        'pibData' : str(pressReleasesPib)
                })
        mergeDocs(SearchService, SearchKey, pibIndexName, s3Data)
    else:
        logging.info('Found existing data')
        for s in r:
            s3Data.append(
                {
                    'id' : s['id'],
                    'symbol': s['symbol'],
                    'cik': s['cik'],
                    'step': s['step'],
                    'description': s['description'],
                    'insertedDate': s['insertedDate'],
                    'pibData' : s['pibData']
                })
    return s3Data

def generateSummaries(llm, docs):
    # With the data indexed, let's summarize the information
    promptTemplate = """You are an AI assistant tasked with summarizing sections from the financial document like 10-K and 10-Q report. 
            Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
            Please remember to use clear language and maintain the integrity of the original information without missing any important details.
            Please generate a concise and comprehensive 3 paragraphs summary of the following document. 
            Ensure that the summary is generated for each of the following sections:
            {text}
            """
    customPrompt = PromptTemplate(template=promptTemplate, input_variables=["text"])
    chainType = "map_reduce"
    #summaryChain = load_summarize_chain(llm, chain_type=chainType, return_intermediate_steps=False, 
    #                                    map_prompt=customPrompt, combine_prompt=customPrompt)
    summaryChain = load_summarize_chain(llm, chain_type=chainType)
    summary = summaryChain({"input_documents": docs}, return_only_outputs=True)
    return summary

def processStep4Summaries(llm, secFilingList):

    secFilingsPib = []

    # For different section of extracted data, process summarization and generate common answers to questions
    splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=0)

    # Item 1 - Describes the business of the company
    rawItemDocs = [Document(page_content=secFilingList[0]['item1'])]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 1 : " + str(len(itemDocs)))
    item1Summary = generateSummaries(llm, itemDocs)
    output1Answer = item1Summary['output_text']
    secFilingsPib.append({
                    "section": "item1",
                    "summaryType": "Business Description",
                    "summary": output1Answer
            })
    
    logging.info("Item 1 Summary Completed")

    # Item 1A - Risk Factors
    rawItemDocs = [Document(page_content=secFilingList[0]['item1A'])]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 1A : " + str(len(itemDocs)))
    item1Asummary = generateSummaries(llm,itemDocs)
    output1AAnswer = item1Asummary['output_text']
    secFilingsPib.append({
                    "section": "item1A",
                    "summaryType": "Risk Factors",
                    "summary": output1AAnswer
            })
    
    logging.info("Item 1A Summary Completed")
    
    # Item 3 - Legal Proceedings
    rawItemDocs = [Document(page_content=secFilingList[0]['item3'])]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 3 : " + str(len(itemDocs)))
    item1Asummary = generateSummaries(llm,itemDocs)
    output1AAnswer = item1Asummary['output_text']
    secFilingsPib.append({
                    "section": "item3",
                    "summaryType": "Legal Proceedings",
                    "summary": output1AAnswer
            })

    logging.info("Item 3 Summary Completed")

    # Item 6 - Consolidated Financial Data
    rawItemDocs = [Document(page_content=secFilingList[0]['item6'])]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 6 : " + str(len(itemDocs)))
    item6Summary = generateSummaries(llm, itemDocs)
    output6Answer = item6Summary['output_text']
    secFilingsPib.append({
                    "section": "item6",
                    "summaryType": "Financial Data",
                    "summary": output6Answer
            })
    
    logging.info("Item 6 Summary Completed")

    # Item 7 - Management's Discussion and Analysis of Financial Condition and Results of Operations
    rawItemDocs = [Document(page_content=secFilingList[0]['item7'])]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 7 : " + str(len(itemDocs)))
    item7Summary = generateSummaries(llm, itemDocs)
    output7Answer = item7Summary['output_text']
    secFilingsPib.append({
                    "section": "item7",
                    "summaryType": "Management Discussion",
                    "summary": output7Answer
            })
    
    logging.info("Item 7 Summary Completed")

    # Item 7a - Market risk disclosures
    rawItemDocs = [Document(page_content=secFilingList[0]['item7A'])]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 7A : " + str(len(itemDocs)))
    item7Asummary = generateSummaries(llm, itemDocs)
    output7AAnswer = item7Asummary['output_text']
    secFilingsPib.append({
                    "section": "item7A",
                    "summaryType": "Risk Disclosures",
                    "summary": output7AAnswer
            })
    
    logging.info("Item 7A Summary Completed")

    # Item 9 - Disagreements with accountants and changes in accounting
    section9 = secFilingList[0]['item9'] + "\n " + secFilingList[0]['item9A'] + "\n " + secFilingList[0]['item9B']
    rawItemDocs = [Document(page_content=section9)]
    itemDocs = splitter.split_documents(rawItemDocs)
    logging.info("Number of documents chunks generated from Item 9 : " + str(len(itemDocs)))
    item9Summary = generateSummaries(llm, itemDocs)
    output9Answer = item9Summary['output_text']
    secFilingsPib.append({
                    "section": "item9",
                    "summaryType": "Accounting Disclosures",
                    "summary": output9Answer
            })
    
    logging.info("Item 9 Summary Completed")

    return secFilingsPib

def processStep4(symbol, cik, filingType, historicalYear, currentYear, embeddingModelType, llm, pibIndexName, step, today):

    s4Data = []
    ticker = symbol
    r = findPibData(SearchService, SearchKey, pibIndexName, cik, step, returnFields=['id', 'symbol', 'cik', 'step', 'description', 'insertedDate',
                                                                   'pibData'])
    secFilingIndexName = 'secdata'
    secFilingsListResp = secFilings(apikey=FmpKey, symbol=ticker, filing_type=filingType)
    if len(secFilingsListResp) > 0:
        latestFilingDateTime = datetime.strptime(secFilingsListResp[0]['fillingDate'], '%Y-%m-%d %H:%M:%S')
        logging.info("Latest Filing Date : " + str(latestFilingDateTime))
        latestFilingDate = latestFilingDateTime.strftime("%Y-%m-%d")
        filingYear = latestFilingDateTime.strftime("%Y")
        filingMonth = int(latestFilingDateTime.strftime("%m"))
        if filingMonth > 0 & filingMonth <= 3:
            filingQuarter = 1
        elif filingMonth > 3 & filingMonth <= 6:
            filingQuarter = 2
        elif filingMonth > 6 & filingMonth <= 9:
            filingQuarter = 3
        else:
            filingQuarter = 4
        dt = pd.to_datetime(datetime.now(), format='%Y/%m/%d')
        dt1 = pd.to_datetime(latestFilingDate, format='%Y/%m/%d')
        totalDays = (dt-dt1).days
        if totalDays < 31:
            skipIndicies = False
        else:
            skipIndicies = True

        logging.info("Latest Filing Date : " + latestFilingDate)
        secFilingList = []
        
        if r.get_count() == 0:
            # Check if we have already processed the latest filing, if yes then skip
            createSecFilingIndex(SearchService, SearchKey, secFilingIndexName)
            r = findSecFiling(SearchService, SearchKey, secFilingIndexName, cik, filingType, latestFilingDate, returnFields=['id', 'cik', 'company', 'filingType', 'filingDate',
                                                                                                                            'periodOfReport', 'sic', 'stateOfInc', 'fiscalYearEnd',
                                                                                                                            'filingHtmlIndex', 'htmFilingLink', 'completeTextFilingLink',
                                                                                                                            'item1', 'item1A', 'item1B', 'item2', 'item3', 'item4', 'item5',
                                                                                                                            'item6', 'item7', 'item7A', 'item8', 'item9', 'item9A', 'item9B',
                                                                                                                            'item10', 'item11', 'item12', 'item13', 'item14', 'item15',
                                                                                                                            'sourcefile'])
            logging.info("Found existing filing index :" + str(r.get_count()))
            if r.get_count() == 0:
                emptyBody = {
                        "values": [
                            {
                                "recordId": 0,
                                "data": {
                                    "text": ""
                                }
                            }
                        ]
                }

                secExtractBody = {
                    "values": [
                        {
                            "recordId": 0,
                            "data": {
                                "text": {
                                    "edgar_crawler": {
                                        "start_year": int(filingYear),
                                        "end_year": int(filingYear),
                                        "quarters": [int(filingQuarter)],
                                        "filing_types": [
                                            "10-K"
                                        ],
                                        "cik_tickers": [cik],
                                        "user_agent": "Your name (your email)",
                                        "raw_filings_folder": "RAW_FILINGS",
                                        "indices_folder": "INDICES",
                                        "filings_metadata_file": "FILINGS_METADATA.csv",
                                        "skip_present_indices": skipIndicies
                                    },
                                    "extract_items": {
                                        "raw_filings_folder": "RAW_FILINGS",
                                        "extracted_filings_folder": "EXTRACTED_FILINGS",
                                        "filings_metadata_file": "FILINGS_METADATA.csv",
                                        "items_to_extract": ["1","1A","1B","2","3","4","5","6","7","7A","8","9","9A","9B","10","11","12","13","14","15"],
                                        "remove_tables": False,
                                        "skip_extracted_filings": True
                                    }
                                }
                            }
                        }
                    ]
                }
                # Call Azure Function to perform Web-scraping and store the JSON in our blob
                secExtract = requests.post(SecExtractionUrl, json = secExtractBody)
                # Need to validated on how best to manage the processing
                time.sleep(10)
                # Once the JSON is created, call the function to process the JSON and store the data in our index
                docPersistUrl = SecDocPersistUrl + "&indexType=cogsearchvs&indexName=" + secFilingIndexName + "&embeddingModelType=" + embeddingModelType
                secPersist = requests.post(docPersistUrl, json = emptyBody)
                r = findSecFiling(SearchService, SearchKey, secFilingIndexName, cik, filingType, latestFilingDate, returnFields=['id', 'cik', 'company', 'filingType', 'filingDate',
                                                                                                                            'periodOfReport', 'sic', 'stateOfInc', 'fiscalYearEnd',
                                                                                                                            'filingHtmlIndex', 'htmFilingLink', 'completeTextFilingLink',
                                                                                                                            'item1', 'item1A', 'item1B', 'item2', 'item3', 'item4', 'item5',
                                                                                                                            'item6', 'item7', 'item7A', 'item8', 'item9', 'item9A', 'item9B',
                                                                                                                            'item10', 'item11', 'item12', 'item13', 'item14', 'item15',
                                                                                                                            'sourcefile'])
                
            # Retrieve the latest filing from our index
            lastSecData = ''
            for filing in r:
                lastSecData = filing['item1'] + '\n' + filing['item1A'] + '\n' + filing['item1B'] + '\n' + filing['item2'] + '\n' + filing['item3'] + '\n' + filing['item4'] + '\n' + \
                    filing['item5'] + '\n' + filing['item6'] + '\n' + filing['item7'] + '\n' + filing['item7A'] + '\n' + filing['item8'] + '\n' + \
                    filing['item9'] + '\n' + filing['item9A'] + '\n' + filing['item9B'] + '\n' + filing['item10'] + '\n' + filing['item11'] + '\n' + filing['item12'] + '\n' + \
                    filing['item13'] + '\n' + filing['item14'] + '\n' + filing['item15']
                secFilingList.append({
                    "id": filing['id'],
                    "cik": filing['cik'],
                    "company": filing['company'],
                    "filingType": filing['filingType'],
                    "filingDate": filing['filingDate'],
                    "periodOfReport": filing['periodOfReport'],
                    "sic": filing['sic'],
                    "stateOfInc": filing['stateOfInc'],
                    "fiscalYearEnd": filing['fiscalYearEnd'],
                    "filingHtmlIndex": filing['filingHtmlIndex'],
                    "completeTextFilingLink": filing['completeTextFilingLink'],
                    "item1": filing['item1'],
                    "item1A": filing['item1A'],
                    "item1B": filing['item1B'],
                    "item2": filing['item2'],
                    "item3": filing['item3'],
                    "item4": filing['item4'],
                    "item5": filing['item5'],
                    "item6": filing['item6'],
                    "item7": filing['item7'],
                    "item7A": filing['item7A'],
                    "item8": filing['item8'],
                    "item9": filing['item9'],
                    "item9A": filing['item9A'],
                    "item9B": filing['item9B'],
                    "item10": filing['item10'],
                    "item11": filing['item11'],
                    "item12": filing['item12'],
                    "item13": filing['item13'],
                    "item14": filing['item14'],
                    "item15": filing['item15'],
                    "sourcefile": filing['sourcefile']
                })
                logging.info('Process summaries for ' + symbol)
                secFilingsPib = processStep4Summaries(llm, secFilingList)
                s4Data.append({
                            'id' : str(uuid.uuid4()),
                            'symbol': symbol,
                            'cik': cik,
                            'step': step,
                            'description': 'SEC Filings',
                            'insertedDate': today.strftime("%Y-%m-%d"),
                            'pibData' : str(secFilingsPib)
                    })
                mergeDocs(SearchService, SearchKey, pibIndexName, s4Data)

                # Check if we have already processed the latest filing, if yes then skip
                secFilingsVectorIndexName = 'latestsecfilings'
                createSecFilingsVectorIndex(SearchService, SearchKey, secFilingsVectorIndexName)
                r = findLatestSecFilings(SearchService, SearchKey, secFilingsVectorIndexName, cik, symbol, latestFilingDate, filingType, returnFields=['id', 'cik', 'symbol', 'latestFilingDate', 'filingType',
                                                                                                                                'content'])
                if r.get_count() == 0:
                    logging.info("Processing latest SEC Filings for CIK : " + str(cik) + " and Symbol : " + str(symbol))
                    splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=1000)
                    rawDocs = splitter.create_documents([lastSecData])
                    docs = splitter.split_documents(rawDocs)
                    logging.info("Number of documents chunks generated from Last SEC Filings : " + str(len(docs)))

                    # Store the last index of the earning call transcript in vector Index
                    indexSecFilingsSections(OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiApiKey, SearchService, SearchKey,
                                        embeddingModelType, OpenAiEmbedding, secFilingsVectorIndexName, docs, cik,
                                        symbol, latestFilingDate, filingType)
        else:
            logging.info('Found existing data')
            for s in r:
                s4Data.append(
                    {
                        'id' : s['id'],
                        'symbol': s['symbol'],
                        'cik': s['cik'],
                        'step': s['step'],
                        'description': s['description'],
                        'insertedDate': s['insertedDate'],
                        'pibData' : s['pibData']
                    })
    else:
        logging.info('No Sec Filing data')

        s4Data.append({
                    'id' : str(uuid.uuid4()),
                    'symbol': symbol,
                    'cik': cik,
                    'step': step,
                    'description': 'SEC Filings',
                    'insertedDate': today.strftime("%Y-%m-%d"),
                    'pibData' : str([{
                        "section": "SEC Filings",
                        "summaryType": "SEC Filings",
                        "summary": "No Sec Filing Found"
                    }])
            })
        mergeDocs(SearchService, SearchKey, pibIndexName, s4Data)

    return s4Data

def processStep5(pibIndexName, cik, step, symbol, today):
    s5Data = []

    r = findPibData(SearchService, SearchKey, pibIndexName, cik, step, returnFields=['id', 'symbol', 'cik', 'step', 'description', 'insertedDate',
                                                                    'pibData'])

    if r.get_count() == 0:
        logging.info('No existing data found')
        companyRating = rating(apikey=FmpKey, symbol=symbol)
        fScore = financialScore(apikey=FmpKey, symbol=symbol)
        esgScores = esgScore(apikey=FmpKey, symbol=symbol)
        esgRating = esgRatings(apikey=FmpKey, symbol=symbol)
        ugConsensus = upgradeDowngrades(apikey=FmpKey, symbol=symbol)
        #priceConsensus = priceTarget(apikey=FmpKey, symbol=symbol)
        #ratingsDf = pd.DataFrame.from_dict(pd.json_normalize(companyRating))
        researchReport = []

        try:
            researchReport.append({
                "key": "Overall Recommendation",
                "value": companyRating[0]['ratingRecommendation']
            })
            researchReport.append({
                "key": "DCF Recommendation",
                "value": companyRating[0]['ratingDetailsDCFRecommendation']
            })
            researchReport.append({
                "key": "ROE Recommendation",
                "value": companyRating[0]['ratingDetailsROERecommendation']
            })
            researchReport.append({
                "key": "ROA Recommendation",
                "value": companyRating[0]['ratingDetailsROARecommendation']
            })
            researchReport.append({
                "key": "PB Recommendation",
                "value": companyRating[0]['ratingDetailsPBRecommendation']
            })
            researchReport.append({
                "key": "PE Recommendation",
                "value": companyRating[0]['ratingDetailsPERecommendation']
            })
        except:
            logging.info('No data found for companyRating')
            pass

        try:
            researchReport.append({
                "key": "Altman ZScore",
                "value": fScore[0]['altmanZScore']
            })
            researchReport.append({
                "key": "Piotroski Score",
                "value": fScore[0]['piotroskiScore']
            })
        except:
            logging.info('No data found for fScore')
            pass

        try:
            researchReport.append({
                "key": "Environmental Score",
                "value": esgScores[0]['environmentalScore']
            })
            researchReport.append({
                "key": "Social Score",
                "value": esgScores[0]['socialScore']
            })
            researchReport.append({
                "key": "Governance Score",
                "value": esgScores[0]['governanceScore']
            })
            researchReport.append({
                "key": "ESG Score",
                "value": esgScores[0]['ESGScore']
            })
        except:
            logging.info('No data found for esgScores')
            pass

        try:
            researchReport.append({
                "key": "ESG RIsk Rating",
                "value": esgRating[0]['ESGRiskRating']
            })
        except:
            logging.info('No data found for esgRating')
            pass

        try:
            researchReport.append({
                "key": "Analyst Consensus Buy",
                "value": ugConsensus[0]['buy']
            })
            researchReport.append({
                "key": "Analyst Consensus Sell",
                "value": ugConsensus[0]['sell']
            })
            researchReport.append({
                "key": "Analyst Consensus Strong Buy",
                "value": ugConsensus[0]['strongBuy']
            })
            researchReport.append({
                "key": "Analyst Consensus Strong Sell",
                "value": ugConsensus[0]['strongSell']
            })
            researchReport.append({
                "key": "Analyst Consensus Hold",
                "value": ugConsensus[0]['hold']
            })
            researchReport.append({
                "key": "Analyst Consensus",
                "value": ugConsensus[0]['consensus']
            })
        except:
            logging.info('No data found for ugConsensus')
            pass

        # researchReport.append({
        #     "key": "Price Target Consensus",
        #     "value": priceConsensus[0]['targetConsensus']
        # })
        # researchReport.append({
        #     "key": "Price Target Median",
        #     "value": priceConsensus[0]['targetMedian']
        # })
        s5Data.append({
                    'id' : str(uuid.uuid4()),
                    'symbol': symbol,
                    'cik': cik,
                    'step': step,
                    'description': 'Research Report',
                    'insertedDate': today.strftime("%Y-%m-%d"),
                    'pibData' : str(researchReport)
            })
        mergeDocs(SearchService, SearchKey, pibIndexName, s5Data)
    else:
        logging.info('Found existing data')
        for s in r:
            s5Data.append(
                {
                    'id' : s['id'],
                    'symbol': s['symbol'],
                    'cik': s['cik'],
                    'step': s['step'],
                    'description': s['description'],
                    'insertedDate': s['insertedDate'],
                    'pibData' : s['pibData']
                })
    return s5Data

def PibSteps(step, symbol, embeddingModelType, overrides):
    logging.info("Calling PibSteps Open AI for symbol " + symbol)

    central = timezone('US/Central')
    today = datetime.now(central)
    currentYear = today.year
    historicalDate = today - relativedelta(years=3)
    historicalYear = historicalDate.year
    historicalDate = historicalDate.strftime("%Y-%m-%d")
    totalYears = currentYear - historicalYear
    temperature = 0.3
    tokenLength = 1000
    os.environ['BING_SUBSCRIPTION_KEY'] = BingKey
    os.environ['BING_SEARCH_URL'] = BingUrl
    pibIndexName = 'pibdata'
    filingType = "10-K"
    # Find out the CIK for the Symbol 
    cik = str(int(searchCik(apikey=FmpKey, ticker=symbol)[0]["companyCik"]))
    logging.info(f"CIK for {symbol} is {cik}")
    createPibIndex(SearchService, SearchKey, pibIndexName)

    try:

        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"{OpenAiEndPoint}"

            llm = AzureChatOpenAI(
                    openai_api_base=openai.api_base,
                    openai_api_version=OpenAiVersion,
                    deployment_name=OpenAiChat16k,
                    temperature=temperature,
                    openai_api_key=OpenAiKey,
                    openai_api_type="azure",
                    max_tokens=tokenLength)
                
            embeddings = OpenAIEmbeddings(deployment=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
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
        
        if step == "1":
            s1Data = processStep1(pibIndexName, cik, step, symbol, temperature, llm, today)
            outputFinalAnswer = {"data_points": '', "answer": s1Data, 
                            "thoughts": '',
                                "sources": '', "nextQuestions": '', "error": ""}
            return outputFinalAnswer
        elif step == "2":
            logging.info("Calling Step 2")
            s2Data, content, latestCallDate = processStep2(pibIndexName, cik, step, symbol, llm, today, embeddingModelType, totalYears, 
                 historicalYear)
            outputFinalAnswer = {"data_points": ["Earning call date: " + str(latestCallDate) + "\n " + content], "answer": s2Data, 
                            "thoughts": '',
                                "sources": '', "nextQuestions": '', "error": ""}
            return outputFinalAnswer
        elif step == "3":
            s3Data = processStep3(symbol, cik, step, llm, pibIndexName, today)

            outputFinalAnswer = {"data_points": '', "answer": s3Data, 
                            "thoughts": '',
                                "sources": '', "nextQuestions": '', "error": ""}
            return outputFinalAnswer
        elif step == "4":
            s4Data = processStep4(symbol, cik, filingType, historicalYear, currentYear, embeddingModelType, llm, pibIndexName, step, today)
            outputFinalAnswer = {"data_points": '', "answer": s4Data, 
                            "thoughts": '',
                                "sources": '', "nextQuestions": '', "error": ""}
            return outputFinalAnswer
        elif step == "5":
            s5Data = processStep5(pibIndexName, cik, step, symbol, today)
            outputFinalAnswer = {"data_points": '', "answer": s5Data, 
                            "thoughts": '',
                                "sources": '', "nextQuestions": '', "error": ""}
            return outputFinalAnswer
    
    except Exception as e:
      logging.info("Error in PibData Open AI : " + str(e))
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
        step = req.params.get('step')
        symbol = req.params.get('symbol')
        embeddingModelType = req.params.get('embeddingModelType')
        logging.info("Input parameters : " + step + " " + symbol)
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        result = ComposeResponse(step, symbol, embeddingModelType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(step, symbol, embeddingModelType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(step, symbol, embeddingModelType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(step, symbol, embeddingModelType, record):
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
        answer = PibSteps(step, symbol, embeddingModelType, value)
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

import logging, json, os
import azure.functions as func
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import TokenTextSplitter
from langchain.text_splitter import NLTKTextSplitter
import tempfile
import uuid
import os
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores.milvus import Milvus
import pinecone
from langchain_community.document_loaders.pdf import PDFMinerLoader
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
import time
from langchain_community.vectorstores.redis import Redis
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from Utilities.azureBlob import upsertMetadata, getBlob, getFullPath, copyBlob, copyS3Blob
from Utilities.cogSearch import createSearchIndex, indexSections
from Utilities.formrecognizer import analyze_layout, chunk_paragraphs
from langchain_community.document_loaders.azure_blob_storage_container import AzureBlobStorageContainerLoader
from langchain_community.document_loaders.azure_blob_storage_file import AzureBlobStorageFileLoader
from azure.storage.blob import BlobClient
from azure.storage.blob import ContainerClient
import boto3
from typing import List
from Utilities.envVars import *
from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.text_splitter import MarkdownHeaderTextSplitter
import glob
import zipfile
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
import requests
from io import BytesIO
from unstructured.chunking.title import chunk_by_title
from langchain.vectorstores.azuresearch import AzureSearch
from unstructured.cleaners.core import clean_extra_whitespace, group_broken_paragraphs

try:
    redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
except:
    logging.error("Chroma or Redis not configured.  Ignoring.")

def PartitionFile(fileExtension: str, fileName: str):      
    """ uses the unstructured.io libraries to analyse a document
    Returns:
        elements: A list of available models
    """  
    # Send a GET request to the URL to download the file
    readByte  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
    readBytes = BytesIO(readByte)
    metadata = [] 
    elements = None
    try:        
        if fileExtension == '.csv':
            from unstructured.partition.csv import partition_csv
            elements = partition_csv(file=readBytes)               
                     
        elif fileExtension == '.doc':
            from unstructured.partition.doc import partition_doc
            elements = partition_doc(file=readBytes) 
            
        elif fileExtension == '.docx':
            from unstructured.partition.docx import partition_docx
            elements = partition_docx(file=readBytes)
            
        elif fileExtension == '.eml' or fileExtension == '.msg':
            if fileExtension == '.msg':
                from unstructured.partition.msg import partition_msg
                elements = partition_msg(file=readBytes) 
            else:        
                from unstructured.partition.email import partition_email
                elements = partition_email(file=readBytes)
            metadata.append(f'Subject: {elements[0].metadata.subject}')
            metadata.append(f'From: {elements[0].metadata.sent_from[0]}')
            sent_to_str = 'To: '
            for sent_to in elements[0].metadata.sent_to:
                sent_to_str = sent_to_str + " " + sent_to
            metadata.append(sent_to_str)
            
        elif fileExtension == '.html' or fileExtension == '.htm':  
            from unstructured.partition.html import partition_html
            elements = partition_html(file=readBytes) 
            
        elif fileExtension == '.md':
            from unstructured.partition.md import partition_md
            elements = partition_md(file=readBytes)
                       
        elif fileExtension == '.ppt':
            from unstructured.partition.ppt import partition_ppt
            elements = partition_ppt(file=readBytes)
            
        elif fileExtension == '.pptx':    
            from unstructured.partition.pptx import partition_pptx
            elements = partition_pptx(file=readBytes)
            
        elif any(fileExtension in x for x in ['.txt', '.json']):
            from unstructured.partition.text import partition_text
            elements = partition_text(file=readBytes)
            
        elif fileExtension == '.xlsx':
            from unstructured.partition.xlsx import partition_xlsx
            elements = partition_xlsx(file=readBytes)
            
        elif fileExtension == '.xml':
            from unstructured.partition.xml import partition_xml
            elements = partition_xml(file=readBytes)
            
    except Exception as e:
        logging.info(f"An error occurred trying to parse the file: {str(e)}")
         
    return elements, metadata

def GetAllFiles(filesToProcess):
    files = []
    logging.info("Getting all files")
    try:
        convertedFiles = {}
        for file in filesToProcess:
            files.append({
                "filename" : file['path'],
                "converted": False,
                "embedded": False,
                "converted_path": ""
                })
        logging.info(f"Found {len(files)} files in the container")
        for file in files:
            convertedFileName = f"converted/{file['filename']}.zip"
            if convertedFileName in convertedFiles:
                file['converted'] = True
                file['converted_path'] = convertedFiles[convertedFileName]

        logging.info(files)
    except Exception as e:
        logging.error("Error in GetAllFiles: %s", e)
    return files

def summarizeGenerateQa(docs, embeddingModelType, deploymentType):
    logging.info("Summarization started")
    if (embeddingModelType == 'azureopenai'):
        if deploymentType == 'gpt35':
            llm = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat,
                        temperature=0.3,
                        api_key=OpenAiKey,
                        max_tokens=500)
        elif deploymentType == "gpt3516k":
            llm = AzureChatOpenAI(
                        azure_endpoint=OpenAiEndPoint,
                        api_version=OpenAiVersion,
                        azure_deployment=OpenAiChat16k,
                        temperature=0.3,
                        api_key=OpenAiKey,
                        max_tokens=500)
    elif embeddingModelType == "openai":
        llm = ChatOpenAI(temperature=0.3,
                api_key=OpenAiApiKey,
                model_name="gpt-3.5-turbo",
                max_tokens=1000)
    elif embeddingModelType == "local":
        return "Local not supported", "Local not supported"
    
    logging.info("LLM Setup done")
    logging.info("Document Summary started")

    try:
        summaryChain = load_summarize_chain(llm, chain_type="map_reduce")
        summary = summaryChain.run(docs[:5])
        logging.info("Document Summary completed")
    except Exception as e:
        logging.error("Exception during summary" + str(e))
        summary = 'No summary generated'
        pass

    template = """Given the following extracted parts of a long document, recommend between 1-5 sample questions.

            =========
            {context}
            =========
            """
    
    logging.info("Document QA started")
    try:
        qaPrompt = PromptTemplate(template=template, input_variables=["context"])
        qaChain = load_qa_chain(llm, chain_type='stuff', prompt=qaPrompt)
        #qaChain = load_qa_with_sources_chain(llm, chain_type='stuff', prompt=qaPrompt)
        answer = qaChain({"input_documents": docs[:5], "question": ''}, return_only_outputs=True)
        logging.info("Document QA completed")
        qa = answer['output_text'].replace('\nSample Questions: \n', '').replace('\nSample Questions:\n', '').replace('\n', '\\n')
    except Exception as e:
        logging.error("Exception during QA" + str(e))
        qa = 'No Sample QA generated'
        pass
    #qa = qa.decode('utf8')
    return qa, summary

def blobLoad(blobConnectionString, blobContainer, blobName):
    logging.info("Blob Load started")
    try:
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
        elif (blobName.endswith(".docx") or blobName.endswith(".doc")):
            loader = UnstructuredWordDocumentLoader(downloadPath)

        #loader = UnstructuredFileLoader(downloadPath)
        rawDocs = loader.load()

        fullPath = getFullPath(blobConnectionString, blobContainer, blobName)
        for doc in rawDocs:
            doc.metadata['source'] = fullPath
        return rawDocs
    except Exception as e:
        logging.error("Error in blobLoad: %s", e)
        return None

def s3Load(bucket, key, s3Client):
    logging.info("Loading file from S3")
    try:
        downloadPath = os.path.join(tempfile.gettempdir(), key)
        os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
        s3Client.download_file(bucket, key, downloadPath)
        logging.info("File created " + downloadPath)
        loader = PDFMinerLoader(downloadPath)
        rawDocs = loader.load()
        return rawDocs, downloadPath
    except Exception as e:
        logging.error("Error in s3Load: %s", e)
        return None, None

def storeIndex(indexType, docs, fileName, nameSpace, embeddingModelType):
    logging.info("Storing index")
    try:
        if embeddingModelType == "azureopenai":
            embeddings = AzureOpenAIEmbeddings(azure_endpoint=OpenAiEndPoint, azure_deployment=OpenAiEmbedding, api_key=OpenAiKey, openai_api_type="azure")
        elif embeddingModelType == "openai":
            embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)
        elif embeddingModelType == "local":
            #embeddings = LocalHuggingFaceEmbeddings("all-mpnet-base-v2")
            return

        logging.info("Store the index in " + indexType + " and name : " + nameSpace)
        if indexType == 'pinecone':
            PineconeVectorStore.from_documents(docs, embeddings, index_name=VsIndexName, namespace=nameSpace)
            #Pinecone.from_documents(docs, embeddings, index_name=VsIndexName, namespace=nameSpace)
        elif indexType == "redis":
            Redis.from_documents(docs, embeddings, redis_url=redisUrl, index_name=nameSpace)
        elif indexType == "cogsearch" or indexType == "cogsearchvs":
            vectorStore: AzureSearch = AzureSearch(
                azure_search_endpoint=f"https://{SearchService}.search.windows.net/",
                azure_search_key=SearchKey,
                index_name=nameSpace,
                semantic_configuration_name="mySemanticConfig",
                embedding_function=embeddings.embed_query,
            )
            vectorStore.add_documents(documents=docs)
            #createSearchIndex(indexType, nameSpace)
            #indexSections(indexType, embeddingModelType, fileName, nameSpace, docs)
        elif indexType == "chroma":
            logging.info("Chroma Client: " + str(docs))
            #Chroma.from_documents(docs, embeddings, collection_name=nameSpace, client=chromaClient, embedding_function=embeddings)
        elif indexType == 'milvus':
            milvus = Milvus(connection_args={"host": "127.0.0.1", "port": "19530"},
                            collection_name=VsIndexName, text_field="text", embedding_function=embeddings)
            Milvus.from_documents(docs,embeddings)
    except Exception as e:
        logging.error("Exception during storeIndex" + str(e))
        pass

def Embed(indexType, loadType, multiple, indexName,  value,  blobConnectionString,
                                blobContainer, blobPrefix, blobName, s3Bucket, s3Key, s3AccessKey,
                                s3SecretKey, s3Prefix, existingIndex, existingIndexNs,
                                embeddingModelType, textSplitterType, chunkSize, chunkOverlap, promptType, deploymentType):
    logging.info("Embedding Data")
    try:
        uResultNs = uuid.uuid4()
        
        if (existingIndex == "true"):
            indexGuId = existingIndexNs
        else:
            indexGuId = uResultNs.hex
        logging.info("Index will be created as " + indexGuId)

        if multiple == "true":
            singleFile = "false"
        else:
            singleFile = "true"

        if (loadType == "files"):
            try:
                filesData = GetAllFiles(value)
                filesData = list(filter(lambda x : not x['embedded'], filesData))
                filesData = list(map(lambda x: {'filename': x['filename']}, filesData))

                logging.info(f"Found {len(filesData)} files to embed")
                for file in filesData:
                    logging.info(f"Adding {file['filename']} to Process")
                    fileName = file['filename']
                    # Check the file extension
                    if fileName.endswith('.txt'):
                        logging.info("Embedding text file")
                        readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                        fileContent = readBytes.decode('utf-8')
                        downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                        os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                        try:
                            with open(downloadPath, "wb") as file:
                                file.write(bytes(fileContent, 'utf-8'))
                        except Exception as e:
                            errorMessage = str(e)
                            logging.error(e)

                        logging.info("File created")
                        if textSplitterType == "recursive":
                            loader = UnstructuredFileLoader(downloadPath)
                            rawDocs = loader.load()
                            textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                            docs = textSplitter.split_documents(rawDocs)
                        elif textSplitterType == "tiktoken":
                            loader = UnstructuredFileLoader(downloadPath)
                            rawDocs = loader.load()
                            textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                            docs = textSplitter.split_documents(rawDocs)
                        elif textSplitterType == "nltk":
                            loader = UnstructuredFileLoader(downloadPath)
                            rawDocs = loader.load()
                            textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                            docs = textSplitter.split_documents(rawDocs)
                        elif textSplitterType == "formrecognizer":
                            fullPath = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                            docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                        logging.info("Docs " + str(len(docs)))
                        storeIndex(indexType, docs, fileName, indexGuId, embeddingModelType)
                    elif fileName.endswith('.jpg') or fileName.endswith('.jpeg') or fileName.endswith('.jpe') or \
                        fileName.endswith('.jif') or fileName.endswith('.jfi') or fileName.endswith('.jfif') or fileName.endswith('.png') or \
                        fileName.endswith('.tif') or fileName.endswith('.tiff') or fileName.endswith('.docx') or fileName.endswith('.html') or \
                        fileName.endswith('.pptx') or fileName.endswith('.xlsx') or fileName.endswith('.pdf'):
                        logging.info("Embedding Non-text file")
                        docs = []
                        try:
                            if (fileName.endswith('.pdf')):
                                if textSplitterType == "recursive":
                                    rawDocs = blobLoad(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                    textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                                    docs = textSplitter.split_documents(rawDocs)
                                elif textSplitterType == "tiktoken":
                                    rawDocs = blobLoad(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                    textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                                    docs = textSplitter.split_documents(rawDocs)
                                elif textSplitterType == "nltk":
                                    rawDocs = blobLoad(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                    textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                                    docs = textSplitter.split_documents(rawDocs)
                                elif textSplitterType == "formrecognizer":
                                    readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                    fullPath = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                    #docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                                    ## Modify above to instead use the Analyze layout 
                                    downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                                    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                                    try:
                                        with open(downloadPath, "wb") as file:
                                            file.write(readBytes)
                                    except Exception as e:
                                        errorMessage = str(e)
                                        logging.error(e)

                                    logging.info("File created")

                                    logging.info("Analyzing Layout")
                                    # loader = AzureAIDocumentIntelligenceLoader(
                                    #             api_endpoint=FormRecognizerEndPoint,
                                    #             api_key=FormRecognizerKey,
                                    #             file_path=downloadPath,
                                    #             api_model="prebuilt-layout",
                                    #             mode="page",
                                    #         )
                                    # docs = loader.load()
                                    loader = loader = AzureAIDocumentIntelligenceLoader(
                                                api_endpoint=FormRecognizerEndPoint,
                                                api_key=FormRecognizerKey,
                                                file_path=downloadPath,
                                                api_model="prebuilt-layout",
                                            )
                                    rawDocs = loader.load()
                                    # Split the document into chunks base on markdown headers.
                                    headers_to_split_on = [
                                        ("#", "Header 1"),
                                        ("##", "Header 2"),
                                        ("###", "Header 3"),
                                    ]
                                    mdSplitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
                                    mdHeaderSplits = mdSplitter.split_text(rawDocs[0].page_content)
                                    textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                                    docs = textSplitter.split_documents(mdHeaderSplits)

                                logging.info("Docs " + str(len(docs)))
                                storeIndex(indexType, docs, fileName, indexGuId, embeddingModelType)
                            else:
                                readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                fullPath = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                                downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                                os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                                try:
                                    with open(downloadPath, "wb") as file:
                                        file.write(readBytes)
                                except Exception as e:
                                    errorMessage = str(e)
                                    logging.error(e)

                                logging.info("File created")
                                logging.info("Analyzing Layout")
                                loader = loader = AzureAIDocumentIntelligenceLoader(
                                            api_endpoint=FormRecognizerEndPoint,
                                            api_key=FormRecognizerKey,
                                            file_path=downloadPath,
                                            api_model="prebuilt-layout",
                                        )
                                rawDocs = loader.load()
                                # Split the document into chunks base on markdown headers.
                                headers_to_split_on = [
                                    ("#", "Header 1"),
                                    ("##", "Header 2"),
                                    ("###", "Header 3"),
                                ]
                                mdSplitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
                                mdHeaderSplits = mdSplitter.split_text(rawDocs[0].page_content)
                                textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                                docs = textSplitter.split_documents(mdHeaderSplits)
                                logging.info("Docs " + str(len(docs)))
                                storeIndex(indexType, docs, fileName, indexGuId, embeddingModelType)
                        except Exception as e:
                            logging.info(e)
                            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, {'embedded': 'false', 'indexType': indexType,
                                                                                            "textSplitterType": textSplitterType, 
                                    "chunkSize": chunkSize, "chunkOverlap": chunkOverlap, "promptType": promptType, "singleFile": singleFile})
                            errorMessage = str(e)
                    elif fileName.endswith('.csv') or fileName.endswith('.doc') or \
                        fileName.endswith('.ppt') or fileName.endswith('.xls') or \
                        fileName.endswith('.htm') or fileName.endswith('.xml') or fileName.endswith('.eml') or \
                        fileName.endswith('.msg') or fileName.endswith('.json'):
                        readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                        downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                        os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                        try:
                            with open(downloadPath, "wb") as file:
                                file.write(readBytes)
                        except Exception as e:
                            errorMessage = str(e)
                            logging.error(e)

                        logging.info("File created")

                        #loader = UnstructuredFileLoader(downloadPath, mode="elements", strategy="fast", post_processors=[clean_extra_whitespace, group_broken_paragraphs])
                        loader = UnstructuredFileLoader(downloadPath, post_processors=[clean_extra_whitespace, group_broken_paragraphs])
                        textSplitter = RecursiveCharacterTextSplitter(
                                separators=["\n\n\n", "\n\n"],
                                chunk_size=int(chunkSize),
                                chunk_overlap=int(chunkOverlap),
                                length_function=len,
                                is_separator_regex=False,
                            )
                        docs = loader.load_and_split(text_splitter=textSplitter)
                        storeIndex(indexType, docs, fileName, indexGuId, embeddingModelType)
                        # elements, uioMetadata = PartitionFile(os.path.splitext(fileName)[1], fileName)
                        # metaDataText = ''
                        # for metadata_value in uioMetadata:
                        #     metaDataText += metadata_value + '\n'    
                        
                        # title = ''
                        # # Capture the file title
                        # try:
                        #     for i, element in enumerate(elements):
                        #         if title == '' and element.category == 'Title':
                        #             # capture the first title
                        #             title = element.text
                        #             break
                        # except:
                        #     # if this type of eleemnt does not include title, then process with empty value
                        #     pass
                        # chunks = chunk_by_title(elements, multipage_sections=True, new_after_n_chars=1500, combine_text_under_n_chars=500)
                        # subTitleName = ''
                        # sectionName = ''
                        # # Complete and write chunks
                        # for i, chunk in enumerate(chunks):      
                        #     if chunk.metadata.page_number == None:
                        #         page_list = [1]
                        #     else:
                        #         page_list = [chunk.metadata.page_number] 
                        #     # substitute html if text is a table            
                        #     if chunk.category == 'Table':
                        #         chunk_text = chunk.metadata.text_as_html
                        #     else:
                        #         chunk_text = chunk.text
                        #     # add filetype specific metadata as chunk text header
                        #     chunk_text = metaDataText + chunk_text
                    else:
                        try:
                            logging.info("Not supported")
                        except Exception as e:
                            logging.info(e)
                            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, {'embedded': 'false', 'indexType': indexType,
                                                                                            "textSplitterType": textSplitterType, 
                                    "chunkSize": chunkSize, "chunkOverlap": chunkOverlap, "promptType": promptType, "singleFile": singleFile})
                            errorMessage = str(e)
                            return errorMessage
                    if not(fileName.endswith('.csv')):
                        logging.info("Perform Summarization and QA")
                        qa, summary = summarizeGenerateQa(docs, embeddingModelType, deploymentType)
                        logging.info("Upsert metadata")
                        metadata = {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, 
                                    "indexName": indexName.replace("-", "_"),
                                    "textSplitterType": textSplitterType, 
                                    "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                    "promptType": promptType,
                                    "singleFile": singleFile}
                        logging.info(str(metadata))
                        upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                        try:
                            metadata = {'summary': summary.replace("-", "_"), 'qa': qa.replace("-", "_")}
                            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                        except:
                            pass
                    elif fileName.endswith('.csv'):
                        logging.info("Upsert metadata")
                        metadata = {'embedded': 'true', 'namespace': indexGuId, 'indexType': "csv", "indexName": indexName.replace("-", "_"),
                                    'summary': 'No Summary', 'qa': 'No QA',
                                    "textSplitterType": textSplitterType, 
                                    "chunkSize": chunkSize, "chunkOverlap": chunkOverlap, "promptType": promptType, "singleFile": singleFile}
                        upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                    logging.info("Sleeping")
                    time.sleep(5)
                return "Success"
            except Exception as e:
                logging.error("Error in processing file : " + str(e))
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType,
                                                                            "textSplitterType": textSplitterType, 
                                                                            "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                            "promptType": promptType, "singleFile": singleFile})
                errorMessage = str(e)
                return errorMessage
        elif(loadType == "md"):
            logging.info("Processing Markdown data")
            filesData = GetAllFiles(value)
            filesData = list(filter(lambda x : not x['embedded'], filesData))
            filesData = list(map(lambda x: {'filename': x['filename']}, filesData))
            try:
                for file in filesData:
                    logging.info(f"Adding {file['filename']} to Process")
                    fileName = file['filename']
                    if fileName.endswith('.zip'):
                        # Download Zip File
                        readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                        downloadPath = os.path.join(tempfile.gettempdir(), fileName)
                        os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
                        try:
                            with open(downloadPath, "wb") as file:
                                file.write(readBytes)
                        except Exception as e:
                            errorMessage = str(e)
                            logging.error(e)

                        # Unzip the file
                        zipDownloadPath = os.path.join(tempfile.gettempdir(), "Data\\Markdown\\" + Path(fileName).stem)
                        os.makedirs(os.path.dirname(zipDownloadPath), exist_ok=True)
                        try:
                            with zipfile.ZipFile(downloadPath, 'r') as zipRef:
                                    zipRef.extractall(zipDownloadPath)
                        except Exception as e:
                            print(e)
                        markdownFiles = glob.glob(os.path.join(zipDownloadPath + "\\**", "*.md"), recursive=True)

                        rawDocs = []
                        for file in markdownFiles:
                            try:
                                with open(file, 'r', encoding="utf8") as f:
                                        doc = f.read()

                                headerSplit = [
                                ("#", "Title"),
                                ("##", "SubTitle"),
                                ]
                                markDownSplitter = MarkdownHeaderTextSplitter(headers_to_split_on=headerSplit)
                                docs = markDownSplitter.split_text(doc)
                                for doc in docs:
                                    doc.metadata['source'] = Path(file).stem
                                rawDocs = rawDocs + docs
                                storeIndex(indexType, docs, Path(file).stem, indexGuId, embeddingModelType)
                            except Exception as e:
                                logging.info("Skipping file " + file + " as it is not a valid markdown file" + str(e))
                                continue

                        #fullPath = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                        # for doc in rawDocs:
                        #     doc.metadata['source'] = fullPath

                        logging.info("Perform Summarization and QA")
                        qa, summary = summarizeGenerateQa(rawDocs, embeddingModelType, deploymentType)
                        logging.info("Upsert metadata")
                        metadata = {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, 
                                    "indexName": indexName.replace("-", "_"),
                                    "textSplitterType": textSplitterType, 
                                    "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                    "promptType": promptType,
                                    "singleFile": singleFile}
                        logging.info(str(metadata))
                        upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                        try:
                            metadata = {'summary': summary.replace("-", "_"), 'qa': qa.replace("-", "_")}
                            upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, metadata)
                        except:
                            pass
            except Exception as e:
                logging.error("Error in processing file : " + str(e))
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, fileName, {'embedded': 'false', 'indexType': indexType,
                                                                            "textSplitterType": textSplitterType, 
                                                                            "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                            "promptType": promptType, "singleFile": singleFile})
                errorMessage = str(e)
                return errorMessage
        elif (loadType == "webpages"):
            try:
                allDocs = []
                logging.info(value)
                for webPage in value:
                    logging.info("Processing Webpage at " + webPage)
                    docs = []
                    if textSplitterType == "recursive":
                        loader = WebBaseLoader(webPage)
                        rawDocs = loader.load()
                        textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                        docs = textSplitter.split_documents(rawDocs)
                    elif textSplitterType == "tiktoken" or textSplitterType == "formrecognizer":
                        loader = WebBaseLoader(webPage)
                        rawDocs = loader.load()
                        textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                        docs = textSplitter.split_documents(rawDocs)
                    elif textSplitterType == "nltk":
                        loader = WebBaseLoader(webPage)
                        rawDocs = loader.load()
                        textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                        docs = textSplitter.split_documents(rawDocs)
                    # elif textSplitterType == "formrecognizer":
                    #     readBytes  = getBlob(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                    #     fullPath = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, fileName)
                    #     docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                    allDocs = allDocs + docs
                    storeIndex(indexType, docs, indexName + ".txt", indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(allDocs, embeddingModelType, deploymentType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 
                                                                                          'indexType': indexType, "indexName": indexName,
                                                                                          "textSplitterType": textSplitterType, 
                                                                                          "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                          "promptType": promptType, "singleFile": singleFile})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.error("Error in processing Webpages : " + str(e))
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType,
                                                                                          "textSplitterType": textSplitterType, 
                                                                                          "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                          "promptType": promptType, "singleFile": singleFile})
                errorMessage = str(e)
                return errorMessage
        elif (loadType == "adlscontainer"):
            try:
                logging.info("Embedding Azure Blob Container")
                container = ContainerClient.from_connection_string(
                    conn_str=blobConnectionString, container_name=blobContainer
                )
                frDocs = []
                blobList = container.list_blobs(name_starts_with=blobPrefix)
                for blob in blobList:
                    logging.info("Process Blob : " + blob.name)
                    if textSplitterType == "recursive":
                        blobDocs = blobLoad(blobConnectionString, blobContainer, blob.name)
                        copyBlob(blobConnectionString, blobContainer,  blob.name, OpenAiDocConnStr, OpenAiDocContainer)
                        textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    elif textSplitterType == "tiktoken":
                        blobDocs = blobLoad(blobConnectionString, blobContainer, blob.name)
                        copyBlob(blobConnectionString, blobContainer,  blob.name, OpenAiDocConnStr, OpenAiDocContainer)
                        textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    elif textSplitterType == "nltk":
                        blobDocs = blobLoad(blobConnectionString, blobContainer, blob.name)
                        copyBlob(blobConnectionString, blobContainer,  blob.name, OpenAiDocConnStr, OpenAiDocContainer)
                        textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    elif textSplitterType == "formrecognizer":
                        readBytes  = getBlob(blobConnectionString, blobContainer, blob.name)
                        copyBlob(blobConnectionString, blobContainer,  blob.name, OpenAiDocConnStr, OpenAiDocContainer)
                        fullPath = getFullPath(blobConnectionString, blobContainer, blob.name)
                        docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                        frDocs.extend(docs)
                    docs = []
                    if textSplitterType != "formrecognizer":
                        docs = textSplitter.split_documents(blobDocs)
                    else:
                        docs = frDocs
                    storeIndex(indexType, docs,  blob.name, indexGuId, embeddingModelType)

                    logging.info("Perform Summarization and QA")
                    qa, summary = summarizeGenerateQa(docs, embeddingModelType, deploymentType)
                    logging.info("Upsert metadata")
                    upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blob.name, {'embedded': 'true', 'namespace': indexGuId, 'indexType': indexType, 
                                                                                     "indexName": indexName,
                                                                                     "textSplitterType": textSplitterType, 
                                                                                     "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                     "promptType": promptType, "singleFile": singleFile})
                    upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blob.name, {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.error("Error in processing ADLS Container : "  + str(e))
                #upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                errorMessage = str(e)
                return errorMessage
        elif (loadType == "adlsfile"):
            try:
                logging.info("Embedding Azure Blob File")
                docs = []
                if textSplitterType == "recursive":
                    rawDocs = blobLoad(blobConnectionString, blobContainer, blobName)
                    copyBlob(blobConnectionString, blobContainer, blobName, OpenAiDocConnStr, OpenAiDocContainer)
                    textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    docs = textSplitter.split_documents(rawDocs)
                elif textSplitterType == "tiktoken":
                    rawDocs = blobLoad(blobConnectionString, blobContainer, blobName)
                    copyBlob(blobConnectionString, blobContainer,  blobName, OpenAiDocConnStr, OpenAiDocContainer)
                    textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    docs = textSplitter.split_documents(rawDocs)
                elif textSplitterType == "nltk":
                    rawDocs = blobLoad(blobConnectionString, blobContainer, blobName)
                    copyBlob(blobConnectionString, blobContainer, blobName, OpenAiDocConnStr, OpenAiDocContainer)
                    textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    docs = textSplitter.split_documents(rawDocs)
                elif textSplitterType == "formrecognizer":
                    readBytes  = getBlob(blobConnectionString, blobContainer,blobName)
                    copyBlob(blobConnectionString, blobContainer,  blobName, OpenAiDocConnStr, OpenAiDocContainer)
                    fullPath = getFullPath(blobConnectionString, blobContainer, blobName)
                    docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                storeIndex(indexType, docs, blobName, indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs, embeddingModelType, deploymentType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blobName, {'embedded': 'true', 'namespace': indexGuId, 
                                                                                'indexType': indexType, "indexName": indexName,
                                                                                "textSplitterType": textSplitterType, 
                                                                                "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                "promptType": promptType, "singleFile": singleFile})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blobName, {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.error("Error in processing ADLS File : "  + str(e))
                #upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                errorMessage = str(e)
                return errorMessage
        elif (loadType == "s3Container"):
            try:
                logging.info("Embedding S3 Bucket Container")
                s3Client = boto3.client( 's3', aws_access_key_id=s3AccessKey, aws_secret_access_key=s3SecretKey)
                s3Resource = boto3.resource('s3',
                    aws_access_key_id = s3AccessKey,
                    aws_secret_access_key = s3SecretKey
                )
                frDocs = []
                myBucket = s3Resource.Bucket(s3Bucket)
                for blob in myBucket.objects.filter(Prefix=s3Prefix):
                    logging.info("Process Blob : " + blob.key)
                    if textSplitterType == "recursive":
                        blobDocs, downloadPath = s3Load(s3Bucket, blob.key, s3Client)
                        copyS3Blob(downloadPath, blob.key, OpenAiDocConnStr, OpenAiDocContainer)
                        textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    elif textSplitterType == "tiktoken":
                        blobDocs, downloadPath = s3Load(s3Bucket, blob.key, s3Client)
                        copyS3Blob(downloadPath, blob.key, OpenAiDocConnStr, OpenAiDocContainer)
                        textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    elif textSplitterType == "nltk":
                        blobDocs, downloadPath = s3Load(s3Bucket, blob.key, s3Client)
                        copyS3Blob(downloadPath, blob.key, OpenAiDocConnStr, OpenAiDocContainer)
                        textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    elif textSplitterType == "formrecognizer":
                        rawDocs, downloadPath = s3Load(s3Bucket, blob.key, s3Client)
                        copyS3Blob(downloadPath, blob.key, OpenAiDocConnStr, OpenAiDocContainer)
                        with open(downloadPath, "wb") as file:
                            readBytes = file.read()
                        docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                        frDocs.extend(docs)
                    docs = []
                    if textSplitterType != "formrecognizer":
                        docs = textSplitter.split_documents(rawDocs)
                    else:
                        docs = frDocs
                    storeIndex(indexType, docs, blob.key, indexGuId, embeddingModelType)
                    logging.info("Perform Summarization and QA")
                    qa, summary = summarizeGenerateQa(docs, embeddingModelType, deploymentType)
                    logging.info("Upsert metadata")
                    upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blob.key, {'embedded': 'true', 'namespace': indexGuId, 
                                                                                    'indexType': indexType, "indexName": indexName,
                                                                                    "textSplitterType": textSplitterType, 
                                                                                    "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                    "promptType": promptType, "singleFile": singleFile})
                    upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, blob.key, {'summary': summary, 'qa': qa})
                return "Success"            
            except Exception as e:
                logging.error("Error in processing S3 Container : "  + str(e))
                #upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType})
                errorMessage = str(e)
                return errorMessage
        elif (loadType == "s3file"):
            try:
                logging.info("Embedding S3 Bucket File")
                s3Client = boto3.client( 's3', aws_access_key_id=s3AccessKey, aws_secret_access_key=s3SecretKey)
                docs = []
                if textSplitterType == "recursive":
                    rawDocs, downloadPath = s3Load(s3Bucket, s3Key, s3Client)
                    copyS3Blob(downloadPath, s3Key, OpenAiDocConnStr, OpenAiDocContainer)
                    textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    docs = textSplitter.split_documents(rawDocs)
                elif textSplitterType == "tiktoken":
                    rawDocs, downloadPath = s3Load(s3Bucket, s3Key, s3Client)
                    copyS3Blob(downloadPath, s3Key, OpenAiDocConnStr, OpenAiDocContainer)
                    textSplitter = TokenTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    docs = textSplitter.split_documents(rawDocs)
                elif textSplitterType == "nltk":
                    rawDocs, downloadPath = s3Load(s3Bucket, s3Key, s3Client)
                    copyS3Blob(downloadPath, s3Key, OpenAiDocConnStr, OpenAiDocContainer)
                    textSplitter = NLTKTextSplitter(chunk_size=int(chunkSize), chunk_overlap=int(chunkOverlap))
                    docs = textSplitter.split_documents(rawDocs)
                elif textSplitterType == "formrecognizer":
                    rawDocs, downloadPath = s3Load(s3Bucket, s3Key, s3Client)
                    copyS3Blob(downloadPath, s3Key, OpenAiDocConnStr, OpenAiDocContainer)
                    with open(downloadPath, "wb") as file:
                        readBytes = file.read()
                    fullPath = getFullPath(OpenAiDocConnStr, OpenAiDocContainer, s3Key)
                    docs = analyze_layout(readBytes, fullPath, FormRecognizerEndPoint, FormRecognizerKey, chunkSize)
                storeIndex(indexType, docs, blobName, indexGuId, embeddingModelType)
                logging.info("Perform Summarization and QA")
                qa, summary = summarizeGenerateQa(docs, embeddingModelType, deploymentType)
                logging.info("Upsert metadata")
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'true', 'namespace': indexGuId, 
                                                                                          'indexType': indexType, "indexName": indexName,
                                                                                          "textSplitterType": textSplitterType, 
                                                                                          "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                          "promptType": promptType, "singleFile": singleFile})
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'summary': summary, 'qa': qa})
                return "Success"
            except Exception as e:
                logging.error("Error in processing S3 File : "  + str(e))
                upsertMetadata(OpenAiDocConnStr, OpenAiDocContainer, indexName + ".txt", {'embedded': 'false', 'indexType': indexType,
                                                                                          "textSplitterType": textSplitterType, 
                                                                                          "chunkSize": chunkSize, "chunkOverlap": chunkOverlap,
                                                                                          "promptType": promptType, "singleFile": singleFile})
                errorMessage = str(e)
                return errorMessage
    except Exception as e:
        logging.error("General Exception : "  + str(e))
        errorMessage = str(e)
        return errorMessage
        #return func.HttpResponse("Error getting files",status_code=500)

def TransformValue(indexType, loadType,  multiple, indexName, existingIndex, existingIndexNs, 
                   embeddingModelType, textSplitter, chunkSize, chunkOverlap, promptType, deploymentType, record):
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
        blobConnectionString = data['blobConnectionString']
        blobContainer = data['blobContainer']
        blobPrefix = data['blobPrefix']
        blobName = data['blobName']
        s3Bucket = data['s3Bucket']
        s3Key = data['s3Key']
        s3AccessKey = data['s3AccessKey']
        s3SecretKey = data['s3SecretKey']
        s3Prefix = data['s3Prefix']

        summaryResponse = Embed(indexType, loadType,  multiple, indexName, value, blobConnectionString,
                                blobContainer, blobPrefix, blobName, s3Bucket, s3Key, s3AccessKey,
                                s3SecretKey, s3Prefix, existingIndex, existingIndexNs, embeddingModelType,
                                textSplitter, chunkSize, chunkOverlap, promptType, deploymentType)
        return ({
            "recordId": recordId,
            "data": {
                "error": summaryResponse
                    }
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

def ComposeResponse(indexType, loadType,  multiple, indexName, existingIndex, existingIndexNs, embeddingModelType, 
                    textSplitter, chunkSize, chunkOverlap, promptType, deploymentType, jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(indexType, loadType,  multiple, indexName, existingIndex, existingIndexNs, 
                                      embeddingModelType, textSplitter, chunkSize, chunkOverlap, promptType, deploymentType, value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        indexType = req.params.get('indexType')
        loadType = req.params.get('loadType')
        multiple = req.params.get('multiple')
        indexName = req.params.get('indexName')
        existingIndex=req.params.get("existingIndex")
        existingIndexNs=req.params.get("existingIndexNs")
        embeddingModelType=req.params.get("embeddingModelType")
        textSplitter=req.params.get("textSplitter")
        chunkSize=req.params.get("chunkSize")
        chunkOverlap=req.params.get("chunkOverlap")
        promptType=req.params.get("promptType")
        deploymentType=req.params.get("deploymentType")
        body = json.dumps(req.get_json())

        logging.info("Index Type: %s", indexType)
        logging.info("Load Type: %s", loadType)
        logging.info("Multiple: %s", multiple)
        logging.info("Index Name: %s", indexName)
        logging.info("Existing Index: %s", existingIndex)
        logging.info("Existing Index Namespace: %s", existingIndexNs)
        logging.info("Embedding Model Type: %s", embeddingModelType)
        logging.info("Text Splitter: %s", textSplitter)
        logging.info("Chunk Size: %s", chunkSize)
        logging.info("Chunk Overlap: %s", chunkOverlap)
        logging.info("Prompt Type: %s", promptType)
        logging.info("Deployment Type: %s", deploymentType)

    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        try:
            if len(PineconeKey) > 10 and len(PineconeEnv) > 10:
                # pinecone.init(
                #     api_key=PineconeKey,  # find at app.pinecone.io
                #     environment=PineconeEnv  # next to api key in console
                # )
                os.environ["PINECONE_API_KEY"] = PineconeKey
                pc = Pinecone(api_key=PineconeKey)
        except:
            logging.error("Pinecone already initialized or not configured.  Ignoring.")

        result = ComposeResponse(indexType, loadType, multiple, indexName, existingIndex, existingIndexNs, 
                                 embeddingModelType, textSplitter, chunkSize, chunkOverlap, promptType, deploymentType, body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )
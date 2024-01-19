import os  
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    PDFMinerLoader,
)
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.summarize import load_summarize_chain
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI API key and endpoint
openai.api_type = "azure"
openai.api_version = os.getenv('OpenAiVersion', "2023-05-15")
openai.api_key = os.getenv('OpenAiKey')
openai.api_base = os.getenv('OpenAiEndPoint', '')
embeddingModelType = "azureopenai"
temperature = 0.3
tokenLength = 1000

llm = AzureChatOpenAI(
                openai_api_base=openai.api_base,
                openai_api_version=os.getenv('OpenAiVersion', "2023-05-15"),
                deployment_name=os.getenv('OpenAiChat'),
                temperature=temperature,
                openai_api_key=os.getenv('OpenAiKey'),
                openai_api_type="azure",
                max_tokens=tokenLength)
embeddings = OpenAIEmbeddings(deployment=os.getenv('OpenAiEmbedding'), openai_api_key=os.getenv('OpenAiKey'), openai_api_type="azure")

def SplitDoc():
# Set the file name and the namespace for the index
    fileName = "Fabric Get Started.pdf"
    fabricGetStartedPath = "Data/PDF/" + fileName
    # Load the PDF with Document Loader available from Langchain
    loader = PDFMinerLoader(fabricGetStartedPath)
    rawDocs = loader.load()
    # Set the source 
    for doc in rawDocs:
        doc.metadata['source'] = fabricGetStartedPath

    textSplitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
    docs = textSplitter.split_documents(rawDocs)
    return docs

def summarizeAnswer(docs):
    # Let's change now the chaintype from stuff to mapreduce and refine to see the summary
    chainType = "map_reduce"
    summaryChain = load_summarize_chain(llm, chain_type=chainType, return_intermediate_steps=True)
    summary = summaryChain({"input_documents": docs}, return_only_outputs=True)
    outputAnswer = summary['output_text']
    return outputAnswer

docs = SplitDoc()
summary = summarizeAnswer(docs)
print(summary)
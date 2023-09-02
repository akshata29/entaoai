from promptflow import tool
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import openai
from promptflow.connections import CustomConnection
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PDFMinerLoader

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def createIndex(embeddings: object, indexNs:str):
    loader = PDFMinerLoader("https://azure.microsoft.com/mediahandler/files/resourcefiles/azure-arc-enabled-machine-learning-white-paper/MicrosoftAzureArcEnabledML-accessible%20(1).pdf")
    rawDocs = loader.load()
    for doc in rawDocs:
        doc.metadata['source'] = "arcenabledml.pdf"
    textSplitter = RecursiveCharacterTextSplitter(chunk_size=int(1500), chunk_overlap=int(0))
    docs = textSplitter.split_documents(rawDocs)
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(indexNs)

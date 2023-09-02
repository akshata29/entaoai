from promptflow import tool
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import openai
from promptflow.connections import CustomConnection
from langchain.embeddings.openai import OpenAIEmbeddings

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def createEmbedding(overrides: list, conn:CustomConnection):
  embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'

  if (embeddingModelType == 'azureopenai'):
    openai.api_type = "azure"
    openai.api_key = conn.OpenAiKey
    openai.api_version = conn.OpenAiVersion
    openai.api_base = conn.OpenAiEndPoint
    embeddings = OpenAIEmbeddings(deployment=conn.OpenAiEmbedding, chunk_size=1, openai_api_key=conn.OpenAiKey, openai_api_type="azure")
  elif embeddingModelType == "openai":
    openai.api_type = "open_ai"
    openai.api_base = "https://api.openai.com/v1"
    openai.api_version = '2020-11-07' 
    openai.api_key = conn.OpenAiApiKey
    embeddings = OpenAIEmbeddings(openai_api_key=conn.OpenAiApiKey)

  return embeddings
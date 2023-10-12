from promptflow import tool
from langchain.chains import RetrievalQA
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import pinecone
from langchain.tools import format_tool_to_openai_function
import json
from promptflow.connections import CustomConnection

@tool
def autogptanswer(question: str, overrides: list, conn:CustomConnection):
    from vector_retriever import searchPinecone

    overrideChain = overrides.get("chainType") or 'stuff'
    embeddingModelType = overrides.get("embeddingModelType") or 'azureopenai'
    indexType = overrides.get("indexType") or 'indexType'
    indexes = json.loads(json.dumps(overrides.get('indexes'))) or []
    temperature = overrides.get("temperature") or 0
    tokenLength = overrides.get("tokenLength") or 1000
    top = overrides.get("top") or 3

    if (embeddingModelType == 'azureopenai'):
        openai.api_type = "azure"
        openai.api_key = conn.OpenAiKey
        openai.api_version = conn.OpenAiVersion
        openai.api_base = f"{conn.OpenAiEndPoint}"

        llm = AzureChatOpenAI(
            openai_api_base=openai.api_base,
            openai_api_version=conn.OpenAiVersion,
            deployment_name=conn.OpenAiChat,
            temperature=temperature,
            openai_api_key=conn.OpenAiKey,
            openai_api_type="azure",
            max_tokens=tokenLength)

        embeddings = OpenAIEmbeddings(deployment=conn.OpenAiEmbedding, openai_api_key=conn.OpenAiKey, openai_api_type="azure")
    elif embeddingModelType == "openai":
        openai.api_type = "open_ai"
        openai.api_base = "https://api.openai.com/v1"
        openai.api_version = '2020-11-07'
        openai.api_key = conn.OpenAiApiKey
        llm = ChatOpenAI(temperature=temperature,
            openai_api_key=conn.OpenAiApiKey,
            model_name="gpt-3.5-turbo",
            max_tokens=tokenLength)
        embeddings = OpenAIEmbeddings(openai_api_key=conn.OpenAiApiKey)
    
    if indexType == "pinecone":
        answer = searchPinecone(indexes, conn, embeddings, llm, overrideChain, question)
    
    return answer

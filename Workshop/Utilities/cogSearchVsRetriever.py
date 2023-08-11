"""Retriever wrapper for Azure Cognitive Search."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import aiohttp
import requests
from pydantic import BaseModel, Extra, root_validator

from langchain.schema import BaseRetriever, Document
from langchain.utils import get_from_dict_or_env
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import Vector  
from tenacity import retry, wait_random_exponential, stop_after_attempt  
import openai

class CognitiveSearchVsRetriever(BaseRetriever, BaseModel):
    """Wrapper around Azure Cognitive Search."""

    serviceName: str = ""
    """Name of Azure Cognitive Search service"""
    indexName: str = ""
    """Name of Index inside Azure Cognitive Search service"""
    apiKey: str = ""
    """API Key. Both Admin and Query keys work, but for reading data it's
    recommended to use a Query key."""
    aiosession: Optional[aiohttp.ClientSession] = None
    """ClientSession, in case we want to reuse connection for better performance."""
    contentKey: str = "contentVector"
    content: str = "content"
    """Key in a retrieved result to set as the Document page_content in Vector Format."""
    returnFields: list = ["id", "content", "sourcefile"]
    splitMethod : str = "RecursiveCharacterTextSplitter"
    model : str = "GPT3.5"
    chunkSize : str = "2000"
    overlap : str = "100"
    documentId : str = ""
    embeddingModelType : str = "azureopenai"
    openAiEmbedding : str = "text-embedding-ada-002"
    openAiEndPoint : str = ""
    openAiKey : str = ""
    openAiVersion : str = ""
    openAiApiKey : str = ""
    """return fields from search result."""
    topK: int = 3
    """Number of documents to retrieve."""

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    # Function to generate embeddings for title and content fields, also used for query embeddings
    def generateEmbeddings(self, text):
        if (self.embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = self.openAiKey
            openai.api_version = self.openAiVersion
            openai.api_base = f"{self.openAiEndPoint}"

            response = openai.Embedding.create(
                input=text, engine=self.openAiEmbedding)
            embeddings = response['data'][0]['embedding']

        elif self.embeddingModelType == "openai":
            try:
                openai.api_type = "open_ai"
                openai.api_base = "https://api.openai.com/v1"
                openai.api_version = '2020-11-07' 
                openai.api_key = self.openAiApiKey

                response = openai.Embedding.create(
                    input=text, engine="text-embedding-ada-002", api_key = self.openAiApiKey)
                embeddings = response['data'][0]['embedding']
            except Exception as e:
                print(e)
            
        return embeddings
    
    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that service name, index name and api key exists in environment."""
        values["serviceName"] = get_from_dict_or_env(
            values, "serviceName", "AZURE_COGNITIVE_SEARCH_SERVICE_NAME"
        )
        values["indexName"] = get_from_dict_or_env(
            values, "indexName", "AZURE_COGNITIVE_SEARCH_INDEX_NAME"
        )
        values["apiKey"] = get_from_dict_or_env(
            values, "apiKey", "AZURE_COGNITIVE_SEARCH_API_KEY"
        )
        return values

    def _search(self, query: any) -> any:
        searchClient = SearchClient(endpoint=f"https://{self.serviceName}.search.windows.net",
                        index_name=self.indexName,
                        credential=AzureKeyCredential(self.apiKey))

        response = searchClient.search(  
            search_text="",
            vector=Vector(value=self.generateEmbeddings(query), k=self.topK, fields=self.contentKey),
            filter="documentId eq '" + self.documentId + "' and splitMethod eq '" + self.splitMethod + "' and model eq '" + self.model + "' and chunkSize eq '" 
                + self.chunkSize + "' and overlap eq '" + self.overlap + "'",
            select=self.returnFields,
            semantic_configuration_name="semanticConfig",
            include_total_count=True
        )
        return response

    async def _asearch(self, query: str) -> any:
        return None

    def get_relevant_documents(self, query: str) -> List[Document]:
        search_results = self._search(query)

        return [
            Document(page_content=result.pop(self.content), metadata=result)
            for result in search_results
        ]

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        search_results = await self._asearch(query)

        return [
            Document(page_content=result.pop(self.content), metadata=result)
            for result in search_results
        ]
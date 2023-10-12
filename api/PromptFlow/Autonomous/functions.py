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
def functions_format(question: str, overrides: list, conn:CustomConnection) -> list:
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
    
    functions = []

    if indexType == "pinecone":
        functions.append({
            "name": "searchPinecone",
            "description": """A Pinecone data retriever. Use this to retrieve the documents from Pinecone Vector database. Input should be a valid question
            and list of the indexes to search from""",
            "parameters": {
                "type": "object",
                "properties": {
                    "indexes": {
                        "type": "object",
                        "default": indexes,
                        "description": "The list of the indexes to search on",
                    },
                    "conn": {
                        "type": "object",
                        "default": conn,
                        "description": "custom connections object",
                    },
                    "embeddings": {
                        "type": "object",
                        "default": embeddings,
                        "description": "Embedding Model",
                    },
                    "llm": {
                        "type": "object",
                        "default": llm,
                        "description": "LLM Model",
                    },
                    "overrideChain": {
                        "type": "string",
                        "default": overrideChain,
                        "description": "Override Chain",
                    },
                    "question": {
                        "type": "string",
                        "default": question,
                        "description": "User Question",
                    },
                  },
                "required": ["indexes"]
            },
        })
    # elif indexType == "redis":
    #     redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
    #     vectorDb = Redis.from_existing_index(index_name=indexes[0]['indexNs'], embedding=embeddings, redis_url=redisUrl)

    

    #functions = [format_tool_to_openai_function(t) for t in tools]
    
    functions.append({
            "name": "python",
            "description": """A Python shell. Use this to execute python commands. Input should be a valid python
            command and you should print result with `print(...)` to see the output.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command you want to execute in python",
                    }
                  },
                "required": ["command"]
            },
        })
    functions.append({
            "name": "finish",
            "description": """use this to signal that you have finished all your goals and remember show your
            results""",
            "parameters": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": "final response to let people know you have finished your goals and remember "
                                       "show your results",
                    },
                },
                "required": ["response"],
             },
        })

    # functions = [
    #     {
    #         "name": "search",
    #         "description": """The action will search this entity name on Wikipedia and returns the first {count}
    #         sentences if it exists. If not, it will return some related entities to search next.""",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "entity": {
    #                     "type": "string",
    #                     "description": "Entity name which is used for Wikipedia search.",
    #                 },
    #                 "count": {
    #                     "type": "integer",
    #                     "default": 10,
    #                     "description": "Returned sentences count if entity name exists Wikipedia.",
    #                 },
    #             },
    #             "required": ["entity"],
    #         },
    #     },
    #     {
    #         "name": "python",
    #         "description": """A Python shell. Use this to execute python commands. Input should be a valid python
    #         command and you should print result with `print(...)` to see the output.""",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "command": {
    #                     "type": "string",
    #                     "description": "The command you want to execute in python",
    #                 }
    #               },
    #             "required": ["command"]
    #         },
    #     },
    #     {
    #         "name": "finish",
    #         "description": """use this to signal that you have finished all your goals and remember show your
    #         results""",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "response": {
    #                     "type": "string",
    #                     "description": "final response to let people know you have finished your goals and remember "
    #                                    "show your results",
    #                 },
    #             },
    #             "required": ["response"],
    #          },
    #     },
    #   ]
    return functions

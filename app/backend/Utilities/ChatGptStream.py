from Utilities.modelHelper import numTokenFromMessages, getTokenLimit
from typing import Any, Sequence
import logging, json, os
#import openai
from openai import OpenAI, AzureOpenAI, AsyncAzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import QueryType
from tenacity import retry, wait_random_exponential, stop_after_attempt  
import numpy as np
from redis.commands.search.query import Query
from typing import Mapping
from langchain_community.vectorstores.redis import Redis
import pinecone
from functools import reduce
from azure.search.documents.models import VectorizedQuery
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain.vectorstores.azuresearch import AzureSearch
from langchain_openai import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings

class ChatGptStream:

    def __init__(self, OpenAiEndPoint, OpenAiKey, OpenAiVersion, OpenAiChat, OpenAiChat16k, OpenAiApiKey, OpenAiEmbedding, 
                 SearchService, SearchKey, RedisAddress, RedisPort, RedisPassword, PineconeKey, PineconeEnv, VsIndexName):
        self.OpenAiEndPoint = OpenAiEndPoint
        self.OpenAiKey = OpenAiKey
        self.OpenAiVersion = OpenAiVersion
        self.OpenAiChat = OpenAiChat
        self.OpenAiChat16k = OpenAiChat16k
        self.OpenAiApiKey = OpenAiApiKey
        self.OpenAiEmbedding = OpenAiEmbedding
        self.SearchService = SearchService
        self.SearchKey = SearchKey
        self.RedisAddress = RedisAddress
        self.RedisPort = RedisPort
        self.RedisPassword = RedisPassword
        self.PineconeKey = PineconeKey
        self.PineconeEnv = PineconeEnv
        self.VsIndexName = VsIndexName


    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    # Function to generate embeddings for title and content fields, also used for query embeddings
    def generateEmbeddings(self, embeddingModelType, text):
        if (embeddingModelType == 'azureopenai'):
            try:
                client = AzureOpenAI(
                        api_key = self.OpenAiKey,  
                        api_version = self.OpenAiVersion,
                        azure_endpoint = self.OpenAiEndPoint
                        )
                response = client.embeddings.create(
                    input=text, model=self.OpenAiEmbedding)
                embeddings = response.data[0].embedding
            except Exception as e:
                print(e)

        elif embeddingModelType == "openai":
            try:

                client = OpenAI(api_key=self.OpenAiApiKey)
                response = client.embeddings.create(
                    input=text, engine="text-embedding-ada-002", api_key = self.OpenAiApiKey)
                embeddings = response.data[0].embedding
            except Exception as e:
                print(e)
            
        return embeddings
    
    def performCogSearch(self, indexType, embeddingModelType, question, indexName, k, embedField="content_vector", returnFields=["id", "content", "metadata"] ):
        searchClient = SearchClient(endpoint=f"https://{self.SearchService}.search.windows.net",
            index_name=indexName,
            credential=AzureKeyCredential(self.SearchKey))
        try:
            if indexType == "cogsearchvs":
                r = searchClient.search(  
                    search_text=question,  
                    vector_queries=[VectorizedQuery(vector=self.generateEmbeddings(embeddingModelType, question), k_nearest_neighbors=k, fields=embedField)],  
                    select=returnFields,
                    query_type=QueryType.SEMANTIC, 
                    semantic_configuration_name='mySemanticConfig', 
                    query_caption="extractive", 
                    query_answer="extractive",
                    include_total_count=True,
                    top=k
                )
            elif indexType == "cogsearch":
                try:
                    r = searchClient.search(question, 
                                        filter=None,
                                        query_type=QueryType.SEMANTIC, 
                                        query_speller="lexicon", 
                                        semantic_configuration_name="mySemanticConfig", 
                                        top=k, 
                                        query_caption="extractive|highlight-false")
                except Exception as e:
                    r = searchClient.search(question, 
                                    filter=None,
                                    query_type=QueryType.SEMANTIC, 
                                    semantic_configuration_name="mySemanticConfig", 
                                    query_speller="lexicon", 
                                    top=k, 
                                    query_caption="extractive|highlight-false")
            return r       
        except Exception as e:
            logging.info(e)
            return None

    def performRedisSearch(self, question, indexName, k, returnField, vectorField, embeddingModelType):
        redisConnection = Redis(host= self.RedisAddress, port=self.RedisPort, password=self.RedisPassword) #api for Docker localhost for local execution
        question = question.replace("\n", " ")

        embeddingQuery = self.generateEmbeddings(embeddingModelType, question)
        arrayEmbedding = np.array(embeddingQuery)
        hybridField = "*"
        #hybridField = "(@cik:{{4962|2179|7323}})"
        searchType = 'KNN'
        baseQuery = (
            f"{hybridField}=>[{searchType} {k} @{vectorField} $vector AS vector_score]"
        )
        redisQuery = (
            Query(baseQuery)
            .return_fields(*returnField)
            .sort_by("vector_score")
            .paging(0, k)
            .dialect(2)
        )
        paramDict: Mapping[str, str] = {
                "vector": np.array(arrayEmbedding)  # type: ignore
                .astype(dtype=np.float32)
                .tobytes()
        }

        # perform vector search
        results = redisConnection.ft(indexName).search(redisQuery, paramDict)

        return results
    
    def noNewLines(self, s: str) -> str:
        return s.replace('\n', ' ').replace('\r', ' ')
    
    def getStreamMessageFromHistory(self, systemPrompt: str, modelId: str, history: Sequence[dict[str, str]], 
                           userConv: str, fewShots = [], maxTokens: int = 4096):
        messages = []
        messages.append({'role': 'system', 'content': systemPrompt})
        tokenLength = numTokenFromMessages(messages[-1], modelId)

        # Add examples to show the chat what responses we want. It will try to mimic any responses and make sure they match the rules laid out in the system message.
        for shot in fewShots:
            messages.insert(1, {'role': shot.get('role'), 'content': shot.get('content')})

        userContent = userConv
        appendIndex = len(fewShots) + 1

        messages.insert(appendIndex, {'role': "user", 'content': userContent})

        for h in reversed(history[:-1]):
            if h.get("bot"):
                messages.insert(appendIndex, {'role': "assistant", 'content': h.get('bot')})
            messages.insert(appendIndex, {'role': "user", 'content': h.get('user')})
            tokenLength += numTokenFromMessages(messages[appendIndex], modelId)
            if tokenLength > maxTokens:
                break

        # messageBuilder = MessageBuilder(systemPrompt, modelId)

        # for shot in fewShots:
        #     messageBuilder.append_message(shot.get('role'), shot.get('content'))

        # userContent = userConv
        # appendIndex = len(fewShots) + 1

        # messageBuilder.append_message("user", userContent, index=appendIndex)

        # for h in reversed(history[:-1]):
        #     if h.get("bot"):
        #         messageBuilder.append_message("assistant", h.get('bot'), index=appendIndex)
        #     messageBuilder.append_message("user", h.get('user'), index=appendIndex)
        #     if messageBuilder.token_length > maxTokens:
        #         break
        # messages = messageBuilder.messages

        return messages
    
    def performPineconeSearch(self, question, indexName, k, embeddingModelType):
        # pinecone.init(
        #         api_key=self.PineconeKey,  # find at app.pinecone.io
        #         environment=self.PineconeEnv  # next to api key in console
        #     )
        os.environ["PINECONE_API_KEY"] = self.PineconeKey
        pc = Pinecone(api_key=self.PineconeKey)
        index = pinecone.Index(self.PineconeIndex)
        results = index.query(
            namespace=indexName,
            vector=self.generateEmbeddings(embeddingModelType, question),
            top_k=k,
            include_metadata=True
            )
        return results

    def run(self, indexType, indexNs, postBody):
        body = json.dumps(postBody)
        values = json.loads(body)['values']
        data = values[0]['data']
        history = data['history']
        overrides = data['overrides']

        embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
        topK = overrides.get("top") or 5
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        firstSession = overrides.get('firstSession') or False
        sessionId = overrides.get('sessionId')
        promptTemplate = overrides.get('promptTemplate') or ''
        deploymentType = overrides.get('deploymentType') or 'gpt35'
        overrideChain = overrides.get("chainType") or 'stuff'

        print("Search for Top " + str(topK))
        lastQuestion = history[-1]["user"]

        systemTemplate = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base.
        Generate a search query based on the conversation and the new question.
        Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
        Do not include any text inside [] or <<>> in the search query terms.
        Do not include any special characters like '+'.
        If you cannot generate a search query, return just the number 0.

        """

        gptModel = "gpt-35-turbo"
        if (embeddingModelType == 'azureopenai'):
            if deploymentType == 'gpt35':
                gptModel = "gpt-35-turbo"
            elif deploymentType == 'gpt3516k':
                gptModel = "gpt-35-turbo-16k"
        elif embeddingModelType == 'openai':
            if deploymentType == 'gpt35':
                gptModel = "gpt-3.5-turbo"
            elif deploymentType == 'gpt3516k':
                gptModel = "gpt-3.5-turbo-16k"

        tokenLimit = getTokenLimit(gptModel)
        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
        messages = self.getStreamMessageFromHistory(
                systemTemplate,
                gptModel,
                history,
                'Generate search query for: ' + lastQuestion,
                [],
                tokenLimit - len('Generate search query for: ' + lastQuestion) - tokenLength
                )
        
        if (embeddingModelType == 'azureopenai'):
            client = AzureOpenAI(
                api_key = self.OpenAiKey,  
                api_version = self.OpenAiVersion,
                azure_endpoint = self.OpenAiEndPoint
                )

            if deploymentType == 'gpt35':
                completion = client.chat.completions.create(
                    model=self.OpenAiChat, 
                    messages=messages,
                    temperature=0.0,
                    max_tokens=32,
                    n=1)
                
            elif deploymentType == "gpt3516k":
                completion = client.chat.completions.create(
                    model=self.OpenAiChat16k, 
                    messages=messages,
                    temperature=0.0,
                    max_tokens=32,
                    n=1)

            embeddings = AzureOpenAIEmbeddings(azure_endpoint=self.OpenAiEndPoint, 
                                               azure_deployment=self.OpenAiEmbedding, 
                                               api_key=self.OpenAiKey, openai_api_type="azure")
            logging.info("LLM Setup done")
        elif embeddingModelType == "openai":
            client = OpenAI(api_key=self.OpenAiApiKey)
            completion = client.chat.completions.create(
                    model=gptModel, 
                    messages=messages,
                    temperature=0.0,
                    max_tokens=32,
                    n=1)
            embeddings = OpenAIEmbeddings(openai_api_key=self.OpenAiApiKey)

        try:
            if len(history) > 1:
                q = completion.choices[0].message.content.strip(" \n")
            else:
                q = lastQuestion
                
            print("Question " + str(q))
            if q.strip() == "0":
                q = lastQuestion

            if (q == ''):
                q = lastQuestion


        except Exception as e:
            q = lastQuestion
            print(e)

        try:
            if promptTemplate == '':
                template = """
                    Given the following extracted parts of a long document and a question, create a final answer. 
                    If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
                    If the answer is not contained within the text below, say \"I don't know\".

                    {summaries}
                    Question: {question}
                """
            else:
                template = promptTemplate

            followupTemplate = """
            Generate three very brief follow-up questions that the user would likely ask next. 
            Use double angle brackets to reference the questions, e.g. <<>>.
            Try not to repeat questions that have already been asked.
            Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'
            """

            results = []

            uniqueSources = []

            if indexType == 'redis':
                # returnField = ["metadata", "content", "vector_score"]
                # vectorField = "content_vector"
                # r = self.performRedisSearch(q, indexNs, topK, returnField, vectorField, embeddingModelType)
                # results = [" : " + self.noNewLines(result.content) for result in r.docs]
                # sources = [result.metadata.source for result in r.docs]
                # uniqueSources = list(set(sources))
                redisUrl = "redis://default:" + self.RedisPassword + "@" + self.RedisAddress + ":" + self.RedisPort

                indexSchema = {
                    "text": [{"name": "source"}, {"name": "content"}],
                    "vector": [{"name": "content_vector", "dims": 768, "algorithm": "FLAT", "distance_metric": "COSINE"}],
                }

                rds = Redis.from_existing_index(
                    embeddings,
                    index_name=indexNs,
                    redis_url=redisUrl,
                    schema=indexSchema
                )
                retriever = rds.as_retriever(search_type="similarity", search_kwargs={"k": topK})
                retrievedDocs = retriever.get_relevant_documents(q)
                sources = []
                results = [self.noNewLines(doc.page_content) for doc in retrievedDocs]
                uniqueSources = list(set(sources))

            elif indexType == 'pinecone':
                # r = self.performPineconeSearch(q, indexNs, topK, embeddingModelType)
                # results = [self.noNewLines(result['metadata']['text']) for result in r['matches']]
                # sources = [result['metadata']['source'] for result in r['matches']]
                sources = []
                os.environ["PINECONE_API_KEY"] = self.PineconeKey
                pc = Pinecone(api_key=self.PineconeKey, host=self.PineconeEnv)
                print("Pinecone index name is " + self.VsIndexName)
                vectorDb = PineconeVectorStore.from_existing_index(index_name=self.VsIndexName, 
                                                                   embedding=embeddings, namespace=indexNs)
                retriever = vectorDb.as_retriever(search_kwargs={"namespace": indexNs, "k": topK})
                retrievedDocs = retriever.get_relevant_documents(q)
                results = [self.noNewLines(doc.page_content) for doc in retrievedDocs]
                uniqueSources = list(set(sources))
            elif indexType == "cogsearch" or indexType == "cogsearchvs":
                #r = self.performCogSearch(indexType, embeddingModelType, q, indexNs, topK)
                #sr = self.performCogSearch(indexType, embeddingModelType, q, indexNs, topK)
                #try:
                #    sources = [doc["sourcefile"] for doc in sr]
                #except Exception as e:
                #    sources = []
                #results = [self.noNewLines(doc["content"]) for doc in r]

                sources = []
                csVectorStore: AzureSearch = AzureSearch(
                    azure_search_endpoint=f"https://{self.SearchService}.search.windows.net",
                    azure_search_key=self.SearchKey,
                    index_name=indexNs,
                    embedding_function=embeddings.embed_query,
                    semantic_configuration_name="semanticConfig",
                )
                retriever = csVectorStore.as_retriever(search_kwargs={"k": topK})
                retrievedDocs = retriever.get_relevant_documents(q)
                results = [self.noNewLines(doc.page_content) for doc in retrievedDocs]

                uniqueSources = list(set(sources))

            if len(uniqueSources) > 1:
                finalSources = reduce(lambda x, y: str(x) + "," + str(y), uniqueSources)
            elif len(uniqueSources) == 1:
                finalSources = uniqueSources[0]
            else:
                finalSources = ""

            content = "\n".join(results)
            systemTemplate = template.replace("Question: ", "").replace("QUESTION: ", "").format(context="", question=followupTemplate)

            messages = self.getStreamMessageFromHistory(
                systemTemplate + "\n" + content,
                gptModel,
                history,
                lastQuestion,
                [],
                tokenLimit
            )
            msgToDisplay  = '\n\n'.join([str(message) for message in messages])

            yield {"answer": "", "data_points": results, 
                "thoughts": f"Searched for:<br>{lastQuestion}<br><br>Conversations:<br>" + msgToDisplay.replace('\n', '<br>'),
                "sources": finalSources, "nextQuestions": '', "error": ""}
    
            if (embeddingModelType == 'azureopenai'):
                client = AzureOpenAI(
                    api_key = self.OpenAiKey,  
                    api_version = self.OpenAiVersion,
                    azure_endpoint = self.OpenAiEndPoint
                    )

                if deploymentType == 'gpt35':
                    yield from client.chat.completions.create(
                        model=self.OpenAiChat, 
                        messages=messages,
                        temperature=temperature,
                        max_tokens=1024,
                        n=1,
                        stream=True)
                elif deploymentType == "gpt3516k":
                    try:
                        completion = client.chat.completions.create(
                            model=self.OpenAiChat16k, 
                            messages=messages,
                            temperature=temperature,
                            max_tokens=1024,
                            n=1,
                            stream=True)
                        for event in completion:
                            if len(event.choices) > 0:
                                delta = event.choices[0].delta
                                if delta.content:
                                    yield {"answer": delta.content, "data_points": results, 
                                    "thoughts": f"Searched for:<br>{lastQuestion}<br><br>Conversations:<br>" + msgToDisplay.replace('\n', '<br>'),
                                    "sources": finalSources, "nextQuestions": '', "error": ""}
                    except Exception as e:
                        yield str(e)

            elif embeddingModelType == "openai":
                client = OpenAI(api_key=self.OpenAiApiKey)
                completion =  client.chat.completions.create(
                        model=gptModel, 
                        messages=messages,
                        temperature=temperature,
                        max_tokens=1024,
                        n=1,
                        stream=True)
                for event in completion:
                    if len(event.choices) > 0:
                        delta = event.choices[0].delta
                        if delta.content:
                            yield {"answer": delta.content, "data_points": results, 
                            "thoughts": f"Searched for:<br>{lastQuestion}<br><br>Conversations:<br>" + msgToDisplay.replace('\n', '<br>'),
                            "sources": finalSources, "nextQuestions": '', "error": ""}
        except Exception as e:
            print(e)
            yield {"data_points": results, "answer": "Error : " + str(e), "thoughts": "",
                    "sources": finalSources, "nextQuestions": '', "error": str(e)}
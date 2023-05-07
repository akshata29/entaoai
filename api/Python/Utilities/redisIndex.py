from redis import Redis
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import tiktoken
import logging
from itertools import islice
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
import openai
import hashlib
import numpy as np
from redis.commands.search.query import Query
from typing import Mapping
import json

OpenAiEmbedding = os.environ['OpenAiEmbedding']
OpenAiKey = os.environ['OpenAiKey']
OpenAiEndPoint = os.environ['OpenAiEndPoint']
OpenAiVersion = os.environ['OpenAiVersion']
OpenAiDavinci = os.environ['OpenAiDavinci']
RedisAddress = os.environ['RedisAddress']
RedisPassword = os.environ['RedisPassword']
RedisPort = os.environ['RedisPort']

openai.api_type = "azure"
openai.api_base = OpenAiEndPoint
openai.api_version = OpenAiVersion
openai.api_key = OpenAiKey
redisConnection = Redis(host= RedisAddress, port=RedisPort, password=RedisPassword) #api for Docker localhost for local execution

def createRedisIndex(fields, indexName):
    try:
        redisConnection.ft(indexName).info()
    except:  # noqa
        # Create Redis Index
        redisConnection.ft(indexName).create_index(
            fields=fields,
            definition=IndexDefinition(prefix=[f"doc:{indexName}"], index_type=IndexType.HASH),
        )
    return redisConnection

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def getEmbedding(text: str, engine=OpenAiEmbedding) -> list[float]:
    text = text.replace("\n", " ")
    encoding = tiktoken.get_encoding("cl100k_base")
    logging.info("Perform Embedding")
    return openai.Embedding.create(input=encoding.encode(text), engine=engine)["data"][0]["embedding"]

def batched(iterable, n):
    """Batch data into tuples of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := tuple(islice(it, n))):
        yield batch

def chunkedTokens(text, encoding_name, chunk_length):
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    chunks_iterator = batched(tokens, chunk_length)
    yield from chunks_iterator

def getChunkedText(text, encoding_name="cl100k_base", max_tokens=1500,):
    chunked_text = []
    encoding = tiktoken.get_encoding(encoding_name)
    for chunk in chunkedTokens(text, encoding_name=encoding_name, chunk_length=max_tokens):
        chunked_text.append(encoding.decode(chunk))
    return chunked_text

def setDocuments(redisClient, indexName, secData):
    logging.info("Set Document")
    pipeline = redisClient.pipeline()
    for i, text in enumerate(secData):
        key = f"doc:{indexName}:{text['cik']}_{text['sic']}_{text['filing_date']}_{i}"
        pipeline.hset(
            key,
             mapping = {
                "cik": text['cik'],
                "company": text['company'],
                "filing_type": text['filing_type'],
                "filing_date": text['filing_date'],
                "period_of_report": text['period_of_report'],
                "sic": text['sic'],
                "state_of_inc": text['state_of_inc'],
                "state_location": text['state_location'],
                "fiscal_year_end": text['fiscal_year_end'],
                "filing_html_index": text['filing_html_index'],
                "htm_filing_link": text['htm_filing_link'],
                "complete_text_filing_link": text['complete_text_filing_link'],
                "filename": text['filename'],
                "content": text['content'],
                "metadata": text['metadata'],
                "content_vector": np.array(text['content_vector']).astype(dtype=np.float32).tobytes()
            },
        )
    pipeline.execute()
    # redisConnection.hset(
    #     f"embedding:{index}",
    #     mapping={
    #         "text": elem['text'],
    #         "filename": elem['filename'],
    #         "embeddings": np.array(elem['search_embeddings']).astype(dtype=np.float32).tobytes()
    #     }
    # )

def chunkAndEmbed(redisClient, indexName, secDoc, engine="text-embedding-ada-002"):
    encoding = tiktoken.get_encoding("cl100k_base")

    fullData = []

    text = secDoc['item_1'] + secDoc['item_1A'] + secDoc['item_7'] + secDoc['item_7A']
    text = text.replace("\n", " ")
    length = len(encoding.encode(text))
    logging.info(f"Length of text: {length} with engine {engine}")

    if length > 1500:
        k=0
        chunkedText = getChunkedText(text, encoding_name="cl100k_base", max_tokens=1500)
        logging.info(f"Total chunks: {len(chunkedText)}")
        for chunk in chunkedText:
            secCommonData = {
                "cik": secDoc['cik'],
                "company": secDoc['company'],
                "filing_type": secDoc['filing_type'],
                "filing_date": secDoc['filing_date'],
                "period_of_report": secDoc['period_of_report'],
                "sic": secDoc['sic'],
                "state_of_inc": secDoc['state_of_inc'],
                "state_location": secDoc['state_location'],
                "fiscal_year_end": secDoc['fiscal_year_end'],
                "filing_html_index": secDoc['filing_html_index'],
                "htm_filing_link": secDoc['htm_filing_link'],
                "complete_text_filing_link": secDoc['complete_text_filing_link'],
                "filename": secDoc['filename'],
                "content": chunk,
                "content_vector": None,
                "metadata" : json.dumps({"cik": secDoc['cik'], "source": secDoc['filename'], "filingType": secDoc['filing_type'], "reportDate": secDoc['period_of_report']})
            }
            secCommonData['content_vector'] = getEmbedding(chunk, engine)
            fullData.append(secCommonData)
            k=k+1
    else:
      logging.info(f"Process full text with text {text}")
      secCommonData = {
            "cik": secDoc['cik'],
            "company": secDoc['company'],
            "filing_type": secDoc['filing_type'],
            "filing_date": secDoc['filing_date'],
            "period_of_report": secDoc['period_of_report'],
            "sic": secDoc['sic'],
            "state_of_inc": secDoc['state_of_inc'],
            "state_location": secDoc['state_location'],
            "fiscal_year_end": secDoc['fiscal_year_end'],
            "filing_html_index": secDoc['filing_html_index'],
            "htm_filing_link": secDoc['htm_filing_link'],
            "complete_text_filing_link": secDoc['complete_text_filing_link'],
            "filename": secDoc['filename'],
            "content": text,
            "content_vector": None,
            "metadata" : json.dumps({"cik": secDoc['cik'], "source": secDoc['filename'], "filingType": secDoc['filing_type'], "reportDate": secDoc['period_of_report']})
        }
      secCommonData['content_vector'] = getEmbedding(text, engine)
      fullData.append(secCommonData)

    setDocuments(redisClient, indexName, fullData)
    return None

def performRedisSearch(question, indexName, k, returnField, vectorField, embeddingModelType):
    question = question.replace("\n", " ")
    if (embeddingModelType == "azureopenai"):
        engineType = OpenAiEmbedding
    elif (embeddingModelType == "openai"):
        engineType = "text-embedding-ada-002"

    embeddingQuery = getEmbedding(question, engine=engineType)
    logging.info("Got embedding")
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
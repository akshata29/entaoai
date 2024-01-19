import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt  
from Utilities.envVars import *
from openai import OpenAI, AzureOpenAI

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
# Function to generate embeddings for title and content fields, also used for query embeddings
def generateEmbeddings(embeddingModelType, text):
    if (embeddingModelType == 'azureopenai'):
        try:
            client = AzureOpenAI(
                        api_key = OpenAiKey,  
                        api_version = OpenAiVersion,
                        azure_endpoint = OpenAiEndPoint
                        )

            response = client.embeddings.create(
                input=text, model=OpenAiEmbedding)
            embeddings = response.data[0].embedding
        except Exception as e:
            logging.info(e)

    elif embeddingModelType == "openai":
        try:
            client = OpenAI(api_key=OpenAiApiKey)
            response = client.embeddings.create(
                    input=text, model="text-embedding-ada-002", api_key = OpenAiApiKey)
            embeddings = response.data[0].embedding
        except Exception as e:
            logging.info(e)
        
    return embeddings
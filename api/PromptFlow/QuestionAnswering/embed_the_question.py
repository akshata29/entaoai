from promptflow import tool
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt  
from promptflow.connections import CustomConnection

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def embedQuestion(overrides: list, question:str, conn:CustomConnection):
  embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
  
  if (embeddingModelType == 'azureopenai'):
        openai.api_type = "azure"
        openai.api_key = conn.OpenAiKey
        openai.api_version = conn.OpenAiVersion
        openai.api_base = f"{conn.OpenAiEndPoint}"

        response = openai.Embedding.create(
            input=question, engine=conn.OpenAiEmbedding)
        embeddings = response['data'][0]['embedding']

  elif embeddingModelType == "openai":
        try:
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = conn.OpenAiApiKey

            response = openai.Embedding.create(
                input=question, engine="text-embedding-ada-002", api_key = conn.OpenAiApiKey)
            embeddings = response['data'][0]['embedding']
        except Exception as e:
            print(e)
        
  return embeddings

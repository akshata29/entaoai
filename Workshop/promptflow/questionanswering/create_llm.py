from promptflow import tool
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
import openai
from promptflow.connections import CustomConnection

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def createLlm(overrides: list, conn:CustomConnection):
  deploymentType = overrides.get('deploymentType') or 'gpt35'
  temperature = overrides.get("temperature") or 0.3
  tokenLength = overrides.get('tokenLength') or 500
  embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'

  if (embeddingModelType == 'azureopenai'):
    openai.api_type = "azure"
    openai.api_key = conn.OpenAiKey
    openai.api_version = conn.OpenAiVersion
    openai.api_base = conn.OpenAiEndPoint
    if deploymentType == 'gpt35':
        llm = AzureChatOpenAI(
                openai_api_base=openai.api_base,
                openai_api_version=conn.OpenAiVersion,
                deployment_name=conn.OpenAiChat,
                temperature=temperature,
                openai_api_key=conn.OpenAiKey,
                openai_api_type="azure",
                max_tokens=tokenLength)
    elif deploymentType == "gpt3516k":
        llm = AzureChatOpenAI(
                openai_api_base=conn.OpenAiEndPoint,
                openai_api_version=conn.OpenAiVersion,
                deployment_name=conn.OpenAiChat16k,
                temperature=temperature,
                openai_api_key=conn.OpenAiKey,
                openai_api_type="azure",
                max_tokens=tokenLength)
  elif embeddingModelType == "openai":
    openai.api_type = "open_ai"
    openai.api_base = "https://api.openai.com/v1"
    openai.api_version = '2020-11-07' 
    openai.api_key = conn.OpenAiApiKey
    llm = ChatOpenAI(temperature=temperature,
        openai_api_key=conn.OpenAiApiKey,
        model_name="gpt-3.5-turbo",
        max_tokens=tokenLength)

  return llm
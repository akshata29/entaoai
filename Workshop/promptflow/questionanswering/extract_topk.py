from promptflow import tool

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def extractTopK(overrides: list):
  topK = overrides.get("top") or 5
  overrideChain = overrides.get("chainType") or 'stuff'
  temperature = overrides.get("temperature") or 0.3
  tokenLength = overrides.get('tokenLength') or 500
  embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
  promptTemplate = overrides.get('promptTemplate') or ''
  deploymentType = overrides.get('deploymentType') or 'gpt35'
  return topK
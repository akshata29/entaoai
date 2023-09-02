from promptflow import tool

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def setVectorType(indexType: str):
  cogSearchIndex = False
  pineConeIndex = False
  if indexType == 'cogsearchvs':
    cogSearchIndex = True
  elif indexType == 'pine':
    pineConeIndex = True

  return cogSearchIndex, pineConeIndex

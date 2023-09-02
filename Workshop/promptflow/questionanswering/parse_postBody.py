from promptflow import tool
import json

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def parseBody(postBody: list) -> list:
  body = json.dumps(postBody)
  value = json.loads(body)['values'][0]
  data = value['data']
  value = data['text']
  approach = data['approach']
  overrides = data['overrides']
  return overrides
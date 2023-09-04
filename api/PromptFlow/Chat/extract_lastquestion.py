from promptflow import tool
from promptflow.connections import CustomConnection
import datetime
import uuid
import json

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def extractLastQuestion(history: object):
  lastQuestion = history[-1]["user"]

  return lastQuestion
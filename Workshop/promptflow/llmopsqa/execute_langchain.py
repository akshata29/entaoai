from promptflow import tool
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def executeQa(retrievedDocs: list, question: str, promptTemplate:str, overrides:list, llm) -> str:
  overrideChain = overrides.get("chainType") or 'stuff'

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

  qaPrompt = PromptTemplate(template=template, input_variables=["summaries", "question"])
  qaChain = load_qa_with_sources_chain(llm, chain_type=overrideChain, prompt=qaPrompt)
  answer = qaChain({"input_documents": retrievedDocs, "question": question}, return_only_outputs=True)
  answer = answer['output_text'].replace("Answer: ", '').replace("Sources:", 'SOURCES:').replace("Next Questions:", 'NEXT QUESTIONS:')
  modifiedAnswer = answer
  return answer
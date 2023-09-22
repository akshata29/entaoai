from promptflow import tool
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from promptflow.connections import CustomConnection
import uuid
import datetime
import uuid
from langchain.chains import LLMChain

# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def generateFollowupQuestions(formattedAnswer: str, tableSchema: str, sqlQuery:str, sqlResult:object, llm, isQuery:bool) -> list:

    print("isQuery: " + str(isQuery))
    if isQuery:
        followupTemplate = """
        Generate three very brief questions that the user would likely ask next.
        Use double angle brackets to reference the questions, e.g. <What is Azure?>.
        Try not to repeat questions that have already been asked.  Don't include the context in the answer.

        Return the questions in the following format:
        <>
        <>
        <>
        
        ALWAYS return a "NEXT QUESTIONS" part in your answer.

        {context}
        """
        followupPrompt = PromptTemplate(template=followupTemplate, input_variables=["context"])
        
        if type(sqlResult) is str:
            if (str(sqlResult).find("Exception Occurred") >= 0):
                sqlResponse = sqlResult
        else:
            sqlResponse = str(sqlResult.to_dict('list'))

        rawDocs=[]
        rawDocs.append(sqlResponse)
        rawDocs.append(tableSchema)
        rawDocs.append(sqlQuery)
        rawDocs.append(formattedAnswer)
                
        # Followup questions
        llm_chain = LLMChain(prompt=followupPrompt, llm=llm)
        nextQuestions = llm_chain.predict(context=rawDocs)
        print("Next questions: " + str(nextQuestions))

        sources = ''                
        if (formattedAnswer.find("Exception Occurred") >= 0):
            sources = ''
            nextQuestions = ''
            error = formattedAnswer

        outputFinalAnswer = {"data_points": [], "answer": formattedAnswer, "thoughts": tableSchema, 
                    "toolInput": sqlQuery, "observation": sqlResponse,  "nextQuestions": nextQuestions, "error": ""}


        results = {}
        results["values"] = []
        results["values"].append({
                    "recordId": 0,
                    "data": outputFinalAnswer
                    })
        return results
    else:
        outputFinalAnswer = {"data_points": [], "answer": "The question can't be used to generate SQL Query or results", "thoughts": tableSchema, 
                "toolInput": "", "observation": "",  "nextQuestions": "", "error": ""}
        results = {}
        results["values"] = []
        results["values"].append({
                    "recordId": 0,
                    "data": outputFinalAnswer
                    })
        return results

import logging, json, os
import azure.functions as func
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
import os
from langchain.vectorstores import Pinecone
import pinecone
import numpy as np
from langchain.chains import RetrievalQA
from langchain.agents import Tool
from collections import deque
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM
from langchain.chains.base import Chain
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.vectorstores.base import VectorStore
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from Utilities.envVars import *
from langchain.vectorstores.redis import Redis

taskNamespace = "AgiTask"

class TaskCreationChain(LLMChain):
    """Chain to generates tasks."""

    @classmethod
    def fromLlm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        """Get the response parser."""
        taskCreationTemplate = (
            "You are to use the result from an execution agent to create new tasks with the following objective: {objective}."
            "The last completed task has the result: {result}."
            "This result was based on this task description: {task_description}."
            "These are incomplete tasks: {incomplete_tasks}."
            "Based on the result, create a list of new tasks to be completed in order to meet the objective. "
            "These new tasks must not overlap with incomplete tasks. "
            """Return all the new tasks, with one task per line in your response. The result must be a numbered list in the format:
            #. First task
            #. Second task
            
            The number of each entry must be followed by a period.
            Do not include any headers before your numbered list. Do not follow your numbered list with any other output."""
        )
        prompt = PromptTemplate(
            template=taskCreationTemplate,
            input_variables=[
                "result",
                "task_description",
                "incomplete_tasks",
                "objective",
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)
    
class TaskPrioritizationChain(LLMChain):
    """Chain to prioritize tasks."""

    @classmethod
    def fromLlm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        """Get the response parser."""
        taskPriortizationTemplate = (
            """
            You are tasked with cleaning the format and re-prioritizing the following tasks: {task_names}.
            Consider the ultimate objective of your team: {objective}.
            Tasks should be sorted from highest to lowest priority. 
            Higher-priority tasks are those that act as pre-requisites or are more essential for meeting the objective.
            Do not remove any tasks. Return the result as a numbered list in the format:
            #. First task
            #. Second task
            The entries are consecutively numbered, starting with 1. The number of each entry must be followed by a period.
            Do not include any headers before your numbered list. Do not follow your numbered list with any other output.
            Start the task list with number {next_task_id}."""
        )
        prompt = PromptTemplate(
            template=taskPriortizationTemplate,
            input_variables=["task_names", "next_task_id", "objective"],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

def getNextTask(
    taskCreationChain: LLMChain,
    result: Dict,
    taskDescription: str,
    taskList: List[str],
    objective: str,
) -> List[Dict]:
    """Get the next task."""
    incompleteTask = ", ".join(taskList)
    response = taskCreationChain.run(
        result=result,
        task_description=taskDescription,
        incomplete_tasks=incompleteTask,
        objective=objective,
    )
    newTask = response.split("\n")
    return [{"task_name": taskName} for taskName in newTask if taskName.strip()]

def priortizeTasks(
    taskPriortizationChain: LLMChain,
    thisTaskId: int,
    taskList: List[Dict],
    objective: str,
) -> List[Dict]:
    """Prioritize tasks."""
    task_names = [t["task_name"] for t in taskList]
    nextTaskId = int(thisTaskId) + 1
    response = taskPriortizationChain.run(
        task_names=task_names, next_task_id=nextTaskId, objective=objective
    )
    newTasks = response.split("\n")
    priortizedTaskList = []
    for taskString in newTasks:
        if not taskString.strip():
            continue
        taskParts = taskString.strip().split(".", 1)
        if len(taskParts) == 2:
            taskId = taskParts[0].strip()
            taskName = taskParts[1].strip()
            priortizedTaskList.append({"task_id": taskId, "task_name": taskName})
    return priortizedTaskList

def getTopTask(vectorStore, query: str, k: int) -> List[str]:
    """Get the top k tasks based on the query."""
    results = vectorStore.similarity_search_with_score(query, k=k)
    try:
        if not results:
            return []
        sortedResults, _ = zip(*sorted(results, key=lambda x: x[1], reverse=True))
        return [str(item.metadata["task"]) for item in sortedResults]
    except KeyError:
        return []

def executeTask(
    vectorStore, executionChain: LLMChain, objective: str, task: str, k: int = 5
) -> str:
    """Execute a task."""
    context = getTopTask(vectorStore, query=objective, k=k)
    return executionChain.run(objective=objective, context=context, task=task)

class BabyAGI(Chain, BaseModel):
    """Controller model for the BabyAGI agent."""

    taskList: deque = Field(default_factory=deque)
    taskCreationChain: TaskCreationChain = Field(...)
    taskPriortizationChain: TaskPrioritizationChain = Field(...)
    executionChain: AgentExecutor = Field(...)
    taskIdCounter: int = Field(1)
    vectorStore: VectorStore = Field(init=False)
    maxIterations: Optional[int] = None

    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True

    def addTask(self, task: Dict):
        self.taskList.append(task)

    def printTaskList(self):
        print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
        for t in self.taskList:
            print(str(t["task_id"]) + ": " + t["task_name"])

    def printNextTask(self, task: Dict):
        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
        print(str(task["task_id"]) + ": " + task["task_name"])

    def printTaskResult(self, result: str):
        print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
        print(result)

    @property
    def input_keys(self) -> List[str]:
        return ["objective"]

    @property
    def output_keys(self) -> List[str]:
        return []

    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent."""
        objective = inputs["objective"]
        firstTask = inputs.get("first_task", objective)
        self.addTask({"task_id": 1, "task_name": firstTask})
        taskAndResult = []
        numIters = 0
        finalAnswer = ''
        while True:
            if self.taskList:
                #self.printTaskList()

                listOfTasks = []
                for t in self.taskList:
                    listOfTasks.append({
                        "taskName": t["task_name"],
                        "taskId": int(t["task_id"])
                    })

                # Step 1: Pull the first task
                task = self.taskList.popleft()
                #self.printNextTask(task)

                # Step 2: Execute the task
                result = executeTask(
                    self.vectorStore, self.executionChain, objective, task["task_name"]
                )
                thisTaskId = int(task["task_id"])
                #self.printTaskResult(result)

                # Step 3: Store the result in Pinecone
                result_id = f"result_{task['task_id']}"
                taskAndResult.append({
                    "taskName": task["task_name"],
                    "taskId": int(task["task_id"]),
                    "result": result,
                    "taskList": listOfTasks
                })
                # Required for Pinecone, in case it's not there for some reason, ignore
                try:
                    self.vectorStore.add_texts(
                        texts=[result],
                        metadatas=[{"task": task["task_name"]}],
                        ids=[result_id],
                        index_name=VsIndexName, 
                        namespace=taskNamespace
                    )
                except:
                    pass

                # Step 4: Create new tasks and reprioritize task list
                newTasks = getNextTask(
                    self.taskCreationChain,
                    result,
                    task["task_name"],
                    [t["task_name"] for t in self.taskList],
                    objective,
                )
                for newTask in newTasks:
                    self.taskIdCounter += 1
                    newTask.update({"task_id": self.taskIdCounter})
                    self.addTask(newTask)
                self.taskList = deque(
                    priortizeTasks(
                        self.taskPriortizationChain,
                        thisTaskId,
                        list(self.taskList),
                        objective,
                    )
                )
            numIters += 1
            if self.maxIterations is not None and numIters == self.maxIterations:
                finalAnswer = result
                print(
                    "\033[91m\033[1m" + "\n*****TASK ENDING*****\n" + "\033[0m\033[0m"
                )
                break
        return [{
                "answer": finalAnswer,
                "thoughtProcess": taskAndResult,
            }]

    @classmethod
    def fromLlm(
        cls, llm: BaseLLM, vectorStore: VectorStore, agiPrompt, agiTools, verbose: bool = False, **kwargs
    ) -> "BabyAGI":
        """Initialize the BabyAGI Controller."""
        taskCreationChain = TaskCreationChain.fromLlm(llm, verbose=verbose)
        taskPriortizationChain = TaskPrioritizationChain.fromLlm(
            llm, verbose=verbose
        )
        llmChain = LLMChain(llm=llm, prompt=agiPrompt)
        toolNames = [tool.name for tool in agiTools]
        agent = ZeroShotAgent(llm_chain=llmChain, allowed_tools=toolNames)
        agentExecutor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=agiTools, verbose=True
        )
        return cls(
            taskCreationChain=taskCreationChain,
            taskPriortizationChain=taskPriortizationChain,
            executionChain=agentExecutor,
            vectorStore=vectorStore,
            **kwargs,
        )

def addTool(vectorDb, indexType, llm, overrideChain, indexName, returnDirect):
    if indexType == "pinecone":
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever())
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool
    elif indexType == "redis":
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever())
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool

def TaskAgentQaAnswer(question, overrides):
    logging.info("Calling TaskAgentQaAnswer Open AI")
    answer = ''

    try:
        topK = overrides.get("top") or 3
        overrideChain = overrides.get("chainType") or 'stuff'
        temperature = overrides.get("temperature") or 0.3
        tokenLength = overrides.get('tokenLength') or 500
        indexes = json.loads(json.dumps(overrides.get('indexes')))
        indexType = overrides.get('indexType')
        embeddingModelType = overrides.get('embeddingModelType') or 'azureopenai'
        logging.info("Search for Top " + str(topK) + " and chainType is " + str(overrideChain))

        if (embeddingModelType == 'azureopenai'):
            openai.api_type = "azure"
            openai.api_key = OpenAiKey
            openai.api_version = OpenAiVersion
            openai.api_base = f"https://{OpenAiService}.openai.azure.com"

            llm = AzureChatOpenAI(
                openai_api_base="https://{OpenAiService}.openai.azure.com",
                openai_api_version=OpenAiVersion,
                deployment_name=OpenAiChat,
                temperature=0,
                openai_api_key=OpenAiKey,
                openai_api_type="azure",
                max_tokens=1000)

            embeddings = OpenAIEmbeddings(model=OpenAiEmbedding, chunk_size=1, openai_api_key=OpenAiKey)
            logging.info("Azure Open AI LLM Setup done")
        elif embeddingModelType == "openai":
            openai.api_type = "open_ai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_version = '2020-11-07' 
            openai.api_key = OpenAiApiKey
            llm = ChatOpenAI(temperature=temperature,
                    openai_api_key=OpenAiApiKey,
                    max_tokens=1000)
            embeddings = OpenAIEmbeddings(openai_api_key=OpenAiApiKey)
            logging.info("Open AI LLM Setup done")

        if indexType == "pinecone":
            vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexes[0]['indexNs'])
        elif indexType == "redis":
            redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
            vectorDb = Redis.from_existing_index(index_name=indexes[0]['indexNs'], embedding=embeddings, redis_url=redisUrl)

        tools = []
        for index in indexes:
            indexNs = index['indexNs']
            indexName = index['indexName']
            returnDirect = bool(index['returnDirect'])
            tool = addTool(vectorDb, indexType, llm, overrideChain, indexName, returnDirect)
            tools.append(tool)

        logging.info("Vector Database Setup done")

        prefix = """Perform one task based on the following objective: : {objective}. 
        Take into account these previously completed context: {context}."""
        suffix = """Question: {task}
        {agent_scratchpad}"""
        prompt = ZeroShotAgent.create_prompt(
            tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["objective", "task", "context", "agent_scratchpad"],
        )

        maxIterations: Optional[int] = topK

        babyAgi = BabyAGI.fromLlm(
            llm=llm, vectorStore=vectorDb, verbose=False, maxIterations=maxIterations,
            agiPrompt=prompt, agiTools=tools
        )

        agiAnswer = babyAgi._call({"objective": question})
        try:
            finalAnswer = agiAnswer[0]['answer']
        except:
            finalAnswer = "I don't know"
        
        try:
            action = agiAnswer[0]['thoughtProcess']
        except:
            action = ''
        sources = ''
        
        followupQaPromptTemplate = """Generate three very brief follow-up questions from the answer {answer} that the user would likely ask next.
        Use double angle brackets to reference the questions, e.g. <Is there a more details on that?>.
        Try not to repeat questions that have already been asked.
        Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'"""

        finalPrompt = followupQaPromptTemplate.format(answer=finalAnswer)
        try:
            if (embeddingModelType == 'azureopenai'):
                openai.api_type = "azure"
                openai.api_key = OpenAiKey
                openai.api_version = OpenAiVersion
                openai.api_base = f"https://{OpenAiService}.openai.azure.com"

                completion = openai.Completion.create(
                    engine=OpenAiDavinci,
                    prompt=finalPrompt,
                    temperature=temperature,
                    max_tokens=tokenLength,
                    n=1)
                logging.info("Azure Open AI LLM Setup done")
            elif embeddingModelType == "openai":
                openai.api_type = "open_ai"
                openai.api_base = "https://api.openai.com/v1"
                openai.api_version = '2020-11-07' 
                openai.api_key = OpenAiApiKey
                completion = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=finalPrompt,
                    temperature=temperature,
                    max_tokens=tokenLength,
                    n=1)
                logging.info("OpenAI LLM Setup done")

            nextQuestions = completion.choices[0].text
        except Exception as e:
            logging.error(e)
            nextQuestions =  ''
    
        if ((finalAnswer.find("I don't know") >= 0) or (finalAnswer.find("I'm not sure") >= 0)):
            sources = ''
            nextQuestions = ''

        return {"data_points": [], "answer": finalAnswer, "thoughts": action, "sources": sources, "nextQuestions":nextQuestions, "error": ""}

    except Exception as e:
        logging.info("Error in TaskAgentQaAnswer Open AI : " + str(e))
        return {"data_points": [], "answer": 'Exception occurred :' + str(e), "thoughts": '', "sources": '', "nextQuestions":'', "error": str(e)}

    #return answer

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info(f'{context.function_name} HTTP trigger function processed a request.')
    if hasattr(context, 'retry_context'):
        logging.info(f'Current retry count: {context.retry_context.retry_count}')

        if context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.info(
                f"Max retries of {context.retry_context.max_retry_count} for "
                f"function {context.function_name} has been reached")

    try:
        body = json.dumps(req.get_json())
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    if body:
        pinecone.init(
            api_key=PineconeKey,  # find at app.pinecone.io
            environment=PineconeEnv  # next to api key in console
        )
        result = ComposeResponse(body)
        return func.HttpResponse(result, mimetype="application/json")
    else:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

def ComposeResponse(jsonData):
    values = json.loads(jsonData)['values']

    logging.info("Calling Compose Response")
    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        outputRecord = TransformValue(value)
        if outputRecord != None:
            results["values"].append(outputRecord)
    return json.dumps(results, ensure_ascii=False)

def TransformValue(record):
    logging.info("Calling Transform Value")
    try:
        recordId = record['recordId']
    except AssertionError  as error:
        return None

    # Validate the inputs
    try:
        assert ('data' in record), "'data' field is required."
        data = record['data']
        assert ('text' in data), "'text' field is required in 'data' object."

    except KeyError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "KeyError:" + error.args[0] }   ]
            })
    except AssertionError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "AssertionError:" + error.args[0] }   ]
            })
    except SystemError as error:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "SystemError:" + error.args[0] }   ]
            })

    try:
        # Getting the items from the values/data/text
        value = data['text']
        approach = data['approach']
        overrides = data['overrides']
        question = data['question']

        answer = TaskAgentQaAnswer(question, overrides)
        return ({
            "recordId": recordId,
            "data": answer
            })

    except:
        return (
            {
            "recordId": recordId,
            "errors": [ { "message": "Could not complete operation for record." }   ]
            })

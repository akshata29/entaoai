from langchain.chains import RetrievalQA
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.vectorstores import Pinecone
import pinecone

def addTool(indexType, embeddings, llm, overrideChain, indexNs, indexName, VsIndexName, returnDirect, topK):
    if indexType == "pinecone":
        vectorDb = Pinecone.from_existing_index(index_name=VsIndexName, embedding=embeddings, namespace=indexNs)
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever(search_kwargs={"k": topK}))
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool
    elif indexType == "redis":
        #redisUrl = "redis://default:" + RedisPassword + "@" + RedisAddress + ":" + RedisPort
        #vectorDb = Redis.from_existing_index(index_name=indexNs, embedding=embeddings, redis_url=redisUrl)
        index = RetrievalQA.from_chain_type(llm=llm, chain_type=overrideChain, retriever=vectorDb.as_retriever(search_kwargs={"k": topK}))
        tool = Tool(
                name = indexName,
                func=index.run,
                description="useful for when you need to answer questions about " + indexName + ". Input should be a fully formed question.",
                return_direct=returnDirect
            )
        return tool
        
def searchPinecone(indexes, conn, embeddings, llm, overrideChain, question):
    """
    The input is an exact entity name. The action will search this entity name on Wikipedia and returns the first
    count sentences if it exists. If not, it will return some related entities to search next.
    """

    pinecone.init(
                api_key=conn.PineconeKey,  # find at app.pinecone.io
                environment=conn.PineconeEnv  # next to api key in console
        )
    
    tools = []
    for index in indexes:
        indexNs = index['indexNs']
        indexName = index['indexName']
        returnDirect = bool(index['returnDirect'])
        tool = addTool("pinecone", embeddings, llm, overrideChain, indexNs, indexName, conn.VsIndexName, returnDirect, 3)
        tools.append(tool)

    print(tools)
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
                    verbose=False, return_intermediate_steps=True)
    answer = agent({"input":question})
    print(answer)
    return answer['output']

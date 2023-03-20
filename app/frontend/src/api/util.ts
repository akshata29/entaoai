import { OpenAI } from 'langchain/llms'
import { LLMChain, ChatVectorDBQAChain, loadQAChain } from 'langchain/chains'
import { PromptTemplate } from 'langchain/prompts'
import { VectorStore } from 'langchain/vectorstores'

export const makeChain = (vectorStore : VectorStore, qaPrompt: PromptTemplate, IsCached: boolean, onTokenStream : boolean) => {
  const template = `Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

  Chat History:
  {chat_history}
  Follow Up Input: {question}
  Standalone question:`

  const prompt = new PromptTemplate({ template, inputVariables: ['question', 'chat_history'] })

  const questionGenerator = new LLMChain({
    llm: new OpenAI({ temperature: 0, cache: IsCached }),
    prompt: prompt
  })

  
  const docChain = loadQAChain(
    new OpenAI({
      temperature: 0,
      streaming: Boolean(onTokenStream),
      // callbackManager: {
      //   handleNewToken: onTokenStream
      // },
      cache: IsCached
    }),
    //qaPrompt,
    { type: 'map_reduce' }
  )

  return new ChatVectorDBQAChain({
    vectorstore: vectorStore,
    combineDocumentsChain: docChain,
    questionGeneratorChain: questionGenerator
  })
}

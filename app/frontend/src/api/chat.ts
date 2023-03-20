import { PineconeStore } from "langchain/vectorstores";
import { OpenAIEmbeddings } from 'langchain/embeddings'
import { makeChain } from './util'
import { PineconeClient } from "@pinecone-database/pinecone";
import { Configuration, OpenAIApi } from "azure-openai"; 
import { OpenAI } from 'langchain/llms'
import { LLMChain, ChatVectorDBQAChain, loadQAChain } from 'langchain/chains'
import { PromptTemplate } from 'langchain/prompts'
import { VectorStore } from 'langchain/vectorstores'

export default async function handler(req: { body: any; }, res: {
    writeHead: (arg0: number, arg1: {
      'Content-Type': string;
      // Important to set no-transform to avoid compression, which will delay
      // writing response chunks to the client.
      // See https://github.com/vercel/next.js/issues/9965
      'Cache-Control': string; Connection: string;
    }) => void; write: (arg0: string) => void; end: () => void;
  }) {
  const body = req.body

  const qaGeneratortemplate =
    'You are an AI assistant for the all questions on' +
    body.indexName +
    '.  I am still improving my Knowledge base. The documentation is located from PDF. You have a deep understanding of the ' +
    body.indexName +
    ". You are given the following extracted parts of a long document and a question. Provide an answer with a hyperlink to the PDF or with a code block directly from the PDF. You should only use hyperlinks that are explicitly listed as a source in the context. Do NOT make up a hyperlink that is not listed. If you don't know the answer, just say 'Hmm, I'm not sure.' Don't try to make up an answer. If the question is not about " +
    body.indexName +
    ', politely inform them that you are tuned to only answer questions about ' +
    body.indexName +
    '. \r\n========= \r\n{context} \r\n Question: {question} \r\n========= Answer in Markdown:'
  //const promptTemplate = new PromptTemplate({ qaGeneratortemplate, inputVariables: ['question', 'context'] })

  const pineconeClient = new PineconeClient();
  await pineconeClient.init({
    environment: process.env.VITE_PINECONE_ENV || '',
    apiKey: process.env.VITE_PINECONE_KEY || '',
  });

  const openAiApi = new OpenAIApi(
    new Configuration({
       apiKey: process.env.VITE_OPENAI_KEY,
       // add azure info into configuration
       azure: {
          apiKey: process.env.VITE_OPENAI_KEY,
          endpoint: process.env.VITE_OPENAI_ENDPOINT,
          deploymentName: process.env.VIET_OPENAI_DEPLOYMENT
       }
    }),
  );

  
  const vectorStore = await PineconeStore.fromExistingIndex(new OpenAIEmbeddings(), {pineconeIndex:pineconeClient.Index(body.indexName),namespace:body.indexNs})

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',

    // Important to set no-transform to avoid compression, which will delay
    // writing response chunks to the client.
    // See https://github.com/vercel/next.js/issues/9965
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive'
  })

  const sendData = (data: string) => {
    res.write(`data: ${data}\n\n`)
  }

  sendData(JSON.stringify({ data: '' }))

  try {
    // const chain = makeChain(vectorStore, promptTemplate, false, token => {
    //   sendData(JSON.stringify({ data: token }))
    // })
    const model = new OpenAI({});
    const chain = ChatVectorDBQAChain.fromLLM(model, vectorStore);

    await chain.call({
      question: body.question,
      chat_history: body.history
    })
  } catch (err) {
    console.error(err)
  } finally {
    sendData('[DONE]')
    res.end()
  }
}

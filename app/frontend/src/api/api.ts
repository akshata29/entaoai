import { AskRequest, AskResponse, ChatRequest, ChatResponse } from "./models";
import { PineconeStore } from "langchain/vectorstores";
import { OpenAIEmbeddings } from 'langchain/embeddings'
import { PineconeClient } from "@pinecone-database/pinecone";
import { ChatVectorDBQAChain } from 'langchain/chains'
import { OpenAI } from 'langchain/llms'

// export const qaUrl = `${import.meta.env.VITE_QA_URL}`
// export const chatUrl = `${import.meta.env.VITE_CHAT_URL}`
export const qaUrl = `${process.env.VITE_QA_URL}`
export const chatUrl = `${process.env.VITE_CHAT_URL}`
export const chat3Url = `${process.env.VITE_CHAT3_URL}`

export async function askApi(options: AskRequest, indexNs: string, indexType: string, chainType : string): Promise<AskResponse> {
    const url = qaUrl + "&chainType=" + chainType
    + "&question=" + options.question + "&indexType=" + indexType + "&indexNs=" + indexNs;
    // const url = "http://localhost:7071/api/QuestionAnswering?chainType=" + chainType
    // + "&question=" + options.question + "&indexType=" + indexType + "&indexNs=" + indexNs;
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify( {
            values: [
              {
                recordId: 0,
                data: {
                  text: ''
                }
              }
            ]
          })
        // body: JSON.stringify({
        //     question: options.question,
        //     approach: options.approach,
        //     overrides: {
        //         semantic_ranker: options.overrides?.semanticRanker,
        //         semantic_captions: options.overrides?.semanticCaptions,
        //         top: options.overrides?.top,
        //         temperature: options.overrides?.temperature,
        //         prompt_template: options.overrides?.promptTemplate,
        //         prompt_template_prefix: options.overrides?.promptTemplatePrefix,
        //         prompt_template_suffix: options.overrides?.promptTemplateSuffix,
        //         exclude_category: options.overrides?.excludeCategory
        //     }
        // })
    });

    const parsedResponse: ChatResponse = await response.json();
    if (response.status > 299 || !response.ok) {
        throw Error("Unknown error");
    }
    return parsedResponse.values[0].data

}

export async function chatGptApi(options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
    const response = await fetch(chatUrl + "&indexNs=" + indexNs + "&indexType=" + indexType , {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
          values: [
            {
              recordId: 0,
              data: {
                history: options.history,
                approach: 'rrr',
                overrides: {
                  semantic_ranker: true,
                  semantic_captions: false,
                  top: 3,
                  suggest_followup_questions: false
                }
              }
            }
          ]
        })
        // body: JSON.stringify({
        //     history: options.history,
        //     approach: options.approach,
        //     overrides: {
        //         semantic_ranker: options.overrides?.semanticRanker,
        //         semantic_captions: options.overrides?.semanticCaptions,
        //         top: options.overrides?.top,
        //         temperature: options.overrides?.temperature,
        //         prompt_template: options.overrides?.promptTemplate,
        //         prompt_template_prefix: options.overrides?.promptTemplatePrefix,
        //         prompt_template_suffix: options.overrides?.promptTemplateSuffix,
        //         exclude_category: options.overrides?.excludeCategory,
        //         suggest_followup_questions: options.overrides?.suggestFollowupQuestions
        //     }
        // })
    });

    const parsedResponse: ChatResponse = await response.json();
    if (response.status > 299 || !response.ok) {
        throw Error(parsedResponse.values[0].data.error || "Unknown error");
    }
    return parsedResponse.values[0].data;
}

export async function chatGpt3Api(question: string, options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
  const response = await fetch(chat3Url + "&indexNs=" + indexNs + "&question=" + question + "&indexType=" + indexType , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        values: [
          {
            recordId: 0,
            data: {
              history: options.history,
              approach: 'rrr',
              overrides: {
                semantic_ranker: true,
                semantic_captions: false,
                top: 3,
                suggest_followup_questions: false
              }
            }
          }
        ]
      })
  });

  const parsedResponse: ChatResponse = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error(parsedResponse.values[0].data.error || "Unknown error");
  }
  return parsedResponse.values[0].data;
}

export async function chatJsApi(question: string, history: never[], indexNs: string, indexType:string): Promise<AskResponse> {
  
  console.log(question)
  console.log(history)
  console.log(indexNs)

  const response = {
    answer: "Success",
    thoughts: "No Thoughts",
    data_points: [],
    error : ""
  }
  return response
  
  const pineconeClient = new PineconeClient();
  await pineconeClient.init({
    environment: process.env.VITE_PINECONE_ENV || 'us-east-1-aws',
    apiKey: process.env.VITE_PINECONE_KEY || '9e8a4f2b-7dd2-43be-bf19-a0183cad3a7c',
  });
  const pineconeIndex = pineconeClient.Index(process.env.VITE_PINECONE_INDEX || 'oaiembed') 
  
  const vectorStore = await PineconeStore.fromExistingIndex(new OpenAIEmbeddings({openAIApiKey:process.env.VITE_OPENAI_KEY}), 
    {pineconeIndex,namespace:indexNs})

  const model = new OpenAI({openAIApiKey:process.env.VITE_OPENAI_KEY});
  const chain = ChatVectorDBQAChain.fromLLM(model, vectorStore);

  const answer = await chain.call({
      question: question,
      chat_history: history
  })

  console.log(answer)

  const chatHistory = question + answer["text"];
  const followUpRes = await chain.call({
    question: question,
    chat_history: chatHistory,
  });

  console.log(followUpRes)

  return followUpRes["text"]
}

export function getCitationFilePath(citation: string): string {
    return `/content/${citation}`;
}

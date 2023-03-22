import { AskRequest, AskResponse, ChatRequest, ChatResponse } from "./models";
import { PineconeStore } from "langchain/vectorstores";
import { OpenAIEmbeddings } from 'langchain/embeddings'
import { PineconeClient } from "@pinecone-database/pinecone";
import { ChatVectorDBQAChain } from 'langchain/chains'
import { OpenAI } from 'langchain/llms'

export async function askApi(options: AskRequest, indexNs: string, indexType: string, chainType : string): Promise<AskResponse> {
    const response = await fetch('/ask', {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            question: options.question,
            chainType: chainType,
            indexType:indexType,
            indexNs: indexNs,
            postBody: {
              values: [
                {
                  recordId: 0,
                  data: {
                    text: ''
                  }
                }
              ]
            }
        })
    });

    const parsedResponse: ChatResponse = await response.json();
    if (response.status > 299 || !response.ok) {
        throw Error("Unknown error");
    }
    return parsedResponse.values[0].data

}

export async function chatGptApi(options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
    const response = await fetch('/chat' , {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
          indexType:indexType,
          indexNs: indexNs,
          postBody: {
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
          }
        })
    });

    const parsedResponse: ChatResponse = await response.json();
    if (response.status > 299 || !response.ok) {
        throw Error(parsedResponse.values[0].data.error || "Unknown error");
    }
    return parsedResponse.values[0].data;
}
export async function chatGpt3Api(question: string, options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
  const response = await fetch('/chat3', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType:indexType,
        indexNs: indexNs,
        question:question,
        postBody: {
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
        }
      })
  });

  const parsedResponse: ChatResponse = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error(parsedResponse.values[0].data.error || "Unknown error");
  }
  return parsedResponse.values[0].data;
}

export async function refreshIndex() : Promise<any> {
  
  const response = await fetch('/refreshIndex', {
    method: "GET",
    headers: {
        "Content-Type": "application/json"
    },
  });

  const result = await response.json();
  if (response.status > 299 || !response.ok) {
    return "Error";
  }
  return result;
}

export async function uploadFile(fileName:string, fileContent:any, contentType:string) : Promise<string> {
  
  const response = await fetch('/uploadFile', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      fileName:fileName,
      fileContent: fileContent,
      contentType:contentType
    })
  });

  const result = await response.json();
  if (response.status > 299 || !response.ok) {
    return "Error";
  }
  return "Success";
}

export async function uploadBinaryFile(formData:any) : Promise<string> {
  const response = await fetch('/uploadBinaryFile', {
    method: "POST",
    body: formData
  });

  const result = await response.json();
  if (response.status > 299 || !response.ok) {
    return "Error";
  }
  return "Success";
}

export async function processDoc(indexType: string, loadType : string, multiple: string, indexName : string, files: any) : Promise<string> {
  const response = await fetch('/processDoc', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      indexType:indexType,
      multiple: multiple,
      loadType:loadType,
      indexName:indexName,
      postBody: {
        values: [
          {
            recordId: 0,
            data: {
              text: files
            }
          }
        ]
      }
    })
  });

  if (response.status > 299 || !response.ok) {
    return "Error";
  }
  return "Success";
}

export async function chatJsApi(question: string, history: never[], indexNs: string, indexType:string): Promise<AskResponse> { 
  const response = {
    answer: "Success",
    thoughts: "No Thoughts",
    data_points: [],
    error : ""
  }
  return response
  
  // const pineconeClient = new PineconeClient();
  // await pineconeClient.init({
  //   environment: process.env.VITE_PINECONE_ENV || '',
  //   apiKey: process.env.VITE_PINECONE_KEY || '',
  // });
  // const pineconeIndex = pineconeClient.Index(process.env.VITE_PINECONE_INDEX || 'oaiembed') 
  
  // const vectorStore = await PineconeStore.fromExistingIndex(new OpenAIEmbeddings({openAIApiKey:process.env.VITE_OPENAI_KEY}), 
  //   {pineconeIndex,namespace:indexNs})

  // const model = new OpenAI({openAIApiKey:process.env.VITE_OPENAI_KEY});
  // const chain = ChatVectorDBQAChain.fromLLM(model, vectorStore);

  // const answer = await chain.call({
  //     question: question,
  //     chat_history: history
  // })

  // const chatHistory = question + answer["text"];
  // const followUpRes = await chain.call({
  //   question: question,
  //   chat_history: chatHistory,
  // });


  // return followUpRes["text"]
}

export function getCitationFilePath(citation: string): string {
    return `/content/${citation}`;
}

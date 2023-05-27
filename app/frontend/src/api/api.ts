import { AskRequest, AskResponse, ChatRequest, ChatResponse, SpeechTokenResponse, SqlResponse} from "./models";
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
                    text: '',
                    approach: options.approach,
                    overrides: {
                        semantic_ranker: options.overrides?.semanticRanker,
                        semantic_captions: options.overrides?.semanticCaptions,
                        top: options.overrides?.top,
                        temperature: options.overrides?.temperature,
                        prompt_template: options.overrides?.promptTemplate,
                        prompt_template_prefix: options.overrides?.promptTemplatePrefix,
                        prompt_template_suffix: options.overrides?.promptTemplateSuffix,
                        exclude_category: options.overrides?.excludeCategory,
                        chainType: options.overrides?.chainType,
                        tokenLength: options.overrides?.tokenLength,
                        embeddingModelType: options.overrides?.embeddingModelType,
                    }
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

export async function promptGuru(task: string, modelName:string, embeddingModelType: string): Promise<AskResponse> {
  const response = await fetch('/promptGuru', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
          task: task,
          modelName:modelName,
          embeddingModelType:embeddingModelType,
          postBody: {
            values: [
              {
                recordId: 0,
                data: {
                  text: '',
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

export async function askAgentApi(options: AskRequest): Promise<AskResponse> {
  const response = await fetch('/askAgent', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
          postBody: {
            values: [
              {
                recordId: 0,
                data: {
                  text: '',
                  question: options.question,
                  approach: options.approach,
                  overrides: {
                      indexType: options.overrides?.indexType,
                      indexes: options.overrides?.indexes,
                      semantic_ranker: options.overrides?.semanticRanker,
                      semantic_captions: options.overrides?.semanticCaptions,
                      top: options.overrides?.top,
                      temperature: options.overrides?.temperature,
                      prompt_template: options.overrides?.promptTemplate,
                      prompt_template_prefix: options.overrides?.promptTemplatePrefix,
                      prompt_template_suffix: options.overrides?.promptTemplateSuffix,
                      exclude_category: options.overrides?.excludeCategory,
                      chainType: options.overrides?.chainType,
                      tokenLength: options.overrides?.tokenLength,
                      embeddingModelType: options.overrides?.embeddingModelType,
                  }
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
export async function smartAgent(options: AskRequest): Promise<AskResponse> {
  const response = await fetch('/smartAgent', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
          postBody: {
            values: [
              {
                recordId: 0,
                data: {
                  text: '',
                  question: options.question,
                  approach: options.approach,
                  overrides: {
                      top: options.overrides?.top,
                      temperature: options.overrides?.temperature,
                      chainType: options.overrides?.chainType,
                      tokenLength: options.overrides?.tokenLength,
                      embeddingModelType: options.overrides?.embeddingModelType,
                  }
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

export async function askTaskAgentApi(options: AskRequest): Promise<AskResponse> {
  const response = await fetch('/askTaskAgent', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
          postBody: {
            values: [
              {
                recordId: 0,
                data: {
                  text: '',
                  question: options.question,
                  approach: options.approach,
                  overrides: {
                      indexType: options.overrides?.indexType,
                      indexes: options.overrides?.indexes,
                      semantic_ranker: options.overrides?.semanticRanker,
                      semantic_captions: options.overrides?.semanticCaptions,
                      top: options.overrides?.top,
                      temperature: options.overrides?.temperature,
                      prompt_template: options.overrides?.promptTemplate,
                      prompt_template_prefix: options.overrides?.promptTemplatePrefix,
                      prompt_template_suffix: options.overrides?.promptTemplateSuffix,
                      exclude_category: options.overrides?.excludeCategory,
                      chainType: options.overrides?.chainType,
                      tokenLength: options.overrides?.tokenLength,
                      embeddingModelType: options.overrides?.embeddingModelType,
                  }
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
                    semantic_ranker: options.overrides?.semanticRanker,
                    semantic_captions: options.overrides?.semanticCaptions,
                    top: options.overrides?.top,
                    temperature: options.overrides?.temperature,
                    prompt_template: options.overrides?.promptTemplate,
                    prompt_template_prefix: options.overrides?.promptTemplatePrefix,
                    prompt_template_suffix: options.overrides?.promptTemplateSuffix,
                    suggest_followup_questions: options.overrides?.suggestFollowupQuestions,
                    embeddingModelType: options.overrides?.embeddingModelType,
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
                  semantic_ranker: options.overrides?.semanticRanker,
                  semantic_captions: options.overrides?.semanticCaptions,
                  top: options.overrides?.top,
                  temperature: options.overrides?.temperature,
                  prompt_template: options.overrides?.promptTemplate,
                  prompt_template_prefix: options.overrides?.promptTemplatePrefix,
                  prompt_template_suffix: options.overrides?.promptTemplateSuffix,
                  suggest_followup_questions: options.overrides?.suggestFollowupQuestions,
                  embeddingModelType: options.overrides?.embeddingModelType,
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
export async function uploadBinaryFile(formData:any, indexName:string) : Promise<string> {
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

export async function uploadSummaryBinaryFile(formData:any) : Promise<string> {
  const response = await fetch('/uploadSummaryBinaryFile', {
    method: "POST",
    body: formData
  });

  const result = await response.json();
  if (response.status > 299 || !response.ok) {
    return "Error";
  }
  return "Success";
}


export async function processDoc(indexType: string, loadType : string, multiple: string, indexName : string, files: any,
  blobConnectionString : string, blobContainer : string, blobPrefix : string, blobName : string,
  s3Bucket : string, s3Key : string, s3AccessKey : string, s3SecretKey : string, s3Prefix : string,
  existingIndex : string, existingIndexNs: string, embeddingModelType: string,
  textSplitter:string) : Promise<string> {
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
      existingIndex:existingIndex,
      existingIndexNs:existingIndexNs,
      embeddingModelType:embeddingModelType,
      textSplitter:textSplitter,
      postBody: {
        values: [
          {
            recordId: 0,
            data: {
              text: files,
              blobConnectionString: blobConnectionString,
              blobContainer : blobContainer,
              blobPrefix : blobPrefix,
              blobName : blobName,
              s3Bucket: s3Bucket,
              s3Key : s3Key,
              s3AccessKey : s3AccessKey,
              s3SecretKey : s3SecretKey,
              s3Prefix : s3Prefix
            }
          }
        ]
      }
    })
  });

  const parsedResponse: ChatResponse = await response.json();
  if (response.status > 299 || !response.ok) {
      return "Error";
  } else {
    if (parsedResponse.values[0].data.error) {
      return parsedResponse.values[0].data.error;
    }
    return 'Success';
  }
  // if (response.status > 299 || !response.ok) {
  //   return "Error";
  // }
  
  // return "Success";
}

export async function processSummary(loadType : string, multiple: string, files: any,
  embeddingModelType: string, chainType:string) : Promise<AskResponse> {
  const response = await fetch('/processSummary', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      multiple: multiple,
      loadType:loadType,
      embeddingModelType:embeddingModelType,
      chainType:chainType,
      postBody: {
        values: [
          {
            recordId: 0,
            data: {
              text: files,
            }
          }
        ]
      }
    })
  });
  const parsedResponse: ChatResponse = await response.json();
  return parsedResponse.values[0].data;
  // if (response.status > 299 || !response.ok) {
  //     return "Error";
  // } else {
  //   if (parsedResponse.values[0].data.error) {
  //     return parsedResponse.values[0].data.error;
  //   }
  //   return parsedResponse.values[0].data.answer;
  // }
}

export async function convertCode(inputLanguage:string, outputLanguage:string, 
  inputCode:string, modelName:string, embeddingModelType: string) : Promise<string> {
  const response = await fetch('/convertCode', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      inputLanguage:inputLanguage,
      outputLanguage: outputLanguage,
      modelName:modelName,
      embeddingModelType:embeddingModelType,
      postBody: {
        values: [
          {
            recordId: 0,
            data: {
              text: inputCode
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
  return parsedResponse.values[0].data.answer
}

export async function indexManagement(indexType:string, indexName:string, blobName:string, indexNs:string,
  operation:string) : Promise<string> {
  const response = await fetch('/indexManagement', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      indexType:indexType,
      blobName:blobName,
      indexNs:indexNs,
      indexName:indexName,
      operation:operation,
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
      return "Error";
  } else {
    if (parsedResponse.values[0].data.error) {
      return parsedResponse.values[0].data.error;
    }
    return 'Success';
  }
  // if (response.status > 299 || !response.ok) {
  //   return "Error";
  // }
  
  // return "Success";
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

export async function secSearch(indexType: string,  indexName: string, question:string, top: string, 
  embeddingModelType:string): Promise<any> {
  const response = await fetch('/secSearch' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType:indexType,
        indexName: indexName,
        question:question,
        top:top,
        embeddingModelType:embeddingModelType,
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

  const result = await response.json();
  if (response.status > 299 || !response.ok) {
    return "Error";
  }
  return result;
}

export async function sqlChat(question:string, top: number, embeddingModelType: string): Promise<SqlResponse> {
  const response = await fetch('/sqlChat' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question:question,
        top:top,
        embeddingModelType:embeddingModelType,
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

export async function sqlChain(question:string, top: number, embeddingModelType:string): Promise<SqlResponse> {
    const response = await fetch('/sqlChain' , {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question:question,
          top:top,
          embeddingModelType:embeddingModelType,
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

export async function verifyPassword(passType:string, password: string): Promise<string> {
  const response = await fetch('/verifyPassword' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        passType:passType,
        password:password,
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
      return "Error";
  } else {
    if (parsedResponse.values[0].data.error) {
      return parsedResponse.values[0].data.error;
    }
    return 'Success';
  }
}

export async function getSpeechToken(): Promise<SpeechTokenResponse> {
  const response = await fetch('/speechToken' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
  });

  const parsedResponse: SpeechTokenResponse = await response.json();
  if (response.status > 299 || !response.ok) {
    throw Error("Unknown error");
  }
  return parsedResponse
}

export async function summarizer(options: AskRequest, requestText: string, promptType:string, promptName: string, docType: string, 
  chainType:string, embeddingModelType:string): Promise<string> {
  const response = await fetch('/summarizer' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        docType: docType,
        chainType: chainType,
        promptType: promptType,
        promptName: promptName,
        postBody: {
          values: [
            {
              recordId: 0,
              data: {
                text: requestText,
                overrides: {
                  temperature: options.overrides?.temperature,
                  tokenLength: options.overrides?.tokenLength,
                  embeddingModelType : embeddingModelType,
                }
              }
            }
          ]
        }
    })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
    throw Error("Unknown error");
  }
  return parsedResponse.values[0].data.text
}

export async function summaryAndQa(indexType: string, indexNs:string, embeddingModelType: string, requestType: string, 
  chainType:string): Promise<string> {
  const response = await fetch('/summaryAndQa' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType: indexType,
        indexNs: indexNs,
        embeddingModelType: embeddingModelType,
        requestType: requestType,
        chainType: chainType,
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

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
    throw Error("Unknown error");
  }
  if (requestType === 'summary') {
    return parsedResponse.values[0].summary
  }
  else if (requestType === 'qa') {
    return parsedResponse.values[0].qa
  }
  else
    return ''
}

export async function textAnalytics(documentText: string): Promise<string> {
  const response = await fetch('/textAnalytics' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        documentText:documentText
      })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
    throw Error("Unknown error");
  }
  return parsedResponse.TextAnalytics
}

export async function getSpeechApi(text: string): Promise<string|null> {
  return await fetch("/speech", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
          text: text
      })
  }).then((response) => { 
      if(response.status == 200){
          return response.blob();
      } else {
          console.error("Unable to get speech synthesis.");
          return null;
      }
  }).then((blob) => blob ? URL.createObjectURL(blob) : null);
}

export function getCitationFilePath(citation: string): string {
    return `/content/${citation}`;
}

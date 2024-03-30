import { AskRequest, AskResponse, ChatRequest, ChatResponse, SpeechTokenResponse, SqlResponse,
  EvalResponse, UserInfo} from "./models";
import { Any } from "@react-spring/web";

export async function getUserInfo(): Promise<UserInfo[]> {
  const response = await fetch('/.auth/me');
  if (!response.ok) {
      console.log("No identity provider found. Access to chat will be blocked.")
      return [];
  }

  const payload = await response.json();
  return payload;
}
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
                        promptTemplate: options.overrides?.promptTemplate,
                        exclude_category: options.overrides?.excludeCategory,
                        chainType: options.overrides?.chainType,
                        tokenLength: options.overrides?.tokenLength,
                        embeddingModelType: options.overrides?.embeddingModelType,
                        deploymentType: options.overrides?.deploymentType,
                        searchType: options.overrides?.searchType,
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
export async function chat(options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
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
                    top: options.overrides?.top,
                    temperature: options.overrides?.temperature,
                    promptTemplate: options.overrides?.promptTemplate,
                    suggest_followup_questions: options.overrides?.suggestFollowupQuestions,
                    embeddingModelType: options.overrides?.embeddingModelType,
                    firstSession:options.overrides?.firstSession,
                    session:options.overrides?.session,
                    sessionId:options.overrides?.sessionId,
                    deploymentType: options.overrides?.deploymentType,
                    chainType: options.overrides?.chainType,
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
export async function chatStream(options: ChatRequest, indexNs: string, indexType:string): Promise<Response> {
    return await fetch('/chatStream' , {
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
                  top: options.overrides?.top,
                  temperature: options.overrides?.temperature,
                  promptTemplate: options.overrides?.promptTemplate,
                  suggest_followup_questions: options.overrides?.suggestFollowupQuestions,
                  embeddingModelType: options.overrides?.embeddingModelType,
                  firstSession:options.overrides?.firstSession,
                  session:options.overrides?.session,
                  sessionId:options.overrides?.sessionId,
                  deploymentType: options.overrides?.deploymentType,
                  chainType: options.overrides?.chainType,
                }
              }
            }
          ]
        }
      })
  });
}
export async function chatGpt(options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
  const response = await fetch('/chatGpt' , {
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
                  temperature: options.overrides?.temperature,
                  tokenLength: options.overrides?.tokenLength,
                  promptTemplate: options.overrides?.promptTemplate,
                  embeddingModelType: options.overrides?.embeddingModelType,
                  firstSession:options.overrides?.firstSession,
                  session:options.overrides?.session,
                  sessionId:options.overrides?.sessionId,
                  deploymentType: options.overrides?.deploymentType,
                  functionCall: options.overrides?.functionCall,
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
export async function getAllSessions(indexType:string, feature:string, type:string): Promise<Any> {
  const response = await fetch('/getAllSessions' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType:indexType,
        feature:feature,
        type:type,
      })
  });

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function getAllIndexSessions(indexNs: string, indexType:string, feature:string, type:string): Promise<Any> {
  const response = await fetch('/getAllIndexSessions' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType:indexType,
        indexNs: indexNs,
        feature:feature,
        type:type,
      })
  });

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function getIndexSession(indexNs: string, indexType:string, sessionName:string): Promise<Any> {
  const response = await fetch('/getIndexSession' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType:indexType,
        indexNs: indexNs,
        sessionName:sessionName
      })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function deleteIndexSession(indexNs: string, indexType:string, sessionName:string): Promise<String> {
  const response = await fetch('/deleteIndexSession' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        indexType:indexType,
        indexNs: indexNs,
        sessionName:sessionName
      })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function getDocumentList(): Promise<Any> {
  const response = await fetch('/getDocumentList' , {
      method: "GET",
      headers: {
          "Content-Type": "application/json"
      },
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function renameIndexSession(oldSessionName: string, newSessionName:string): Promise<String> {
  const response = await fetch('/renameIndexSession' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        oldSessionName:oldSessionName,
        newSessionName: newSessionName
      })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function getIndexSessionDetail(sessionId: string): Promise<Any> {
  const response = await fetch('/getIndexSessionDetail' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        sessionId:sessionId,
      })
  });

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
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
export async function refreshQuestions(indexType:string, indexName: string) : Promise<any> {
  
  const response = await fetch('/refreshQuestions' , {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      indexType:indexType,
      indexName:indexName,
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
export async function refreshIndexQuestions(indexType:string) : Promise<any> {
  
  const response = await fetch('/refreshIndexQuestions' , {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      indexType:indexType,
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
export async function kbQuestionManagement(documentsToDelete:any) : Promise<any> {
  
  const response = await fetch('/kbQuestionManagement' , {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      documentsToDelete:documentsToDelete,
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
export async function processDoc(indexType: string, loadType : string, multiple: string, indexName : string, files: any,
  blobConnectionString : string, blobContainer : string, blobPrefix : string, blobName : string,
  s3Bucket : string, s3Key : string, s3AccessKey : string, s3SecretKey : string, s3Prefix : string,
  existingIndex : string, existingIndexNs: string, embeddingModelType: string,
  textSplitter:string, chunkSize:any, chunkOverlap:any, promptType:string, deploymentType:string) : Promise<string> {
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
      chunkSize:chunkSize,
      chunkOverlap:chunkOverlap,
      promptType:promptType,
      deploymentType:deploymentType,
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

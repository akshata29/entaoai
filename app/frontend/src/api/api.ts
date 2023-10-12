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
export async function getNews(symbol: string): Promise<Any> {
  const response = await fetch('/getNews', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        symbol: symbol,
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

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse
}
export async function getSocialSentiment(symbol: string): Promise<Any> {
  const response = await fetch('/getSocialSentiment', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        symbol: symbol,
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

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse
}
export async function getIncomeStatement(symbol: string): Promise<Any> {
  const response = await fetch('/getIncomeStatement', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        symbol: symbol,
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

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse
}
export async function getCashFlow(symbol: string): Promise<Any> {
  const response = await fetch('/getCashFlow', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        symbol: symbol,
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

  const parsedResponse: Any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse
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
export async function getPib(step: string, symbol: string, embeddingModelType: string): Promise<AskResponse> {
  const response = await fetch('/getPib', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        step: step,
        symbol: symbol,
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

export async function getPitchBook(profileDataSource: string, earningTranscriptDataSource:string, earningQuarters:string, symbol: string, embeddingModelType: string): Promise<AskResponse> {
  const response = await fetch('/getPitchBook', {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        profileDataSource: profileDataSource,
        earningTranscriptDataSource: earningTranscriptDataSource,
        earningQuarters: earningQuarters,
        symbol: symbol,
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
                      top: options.overrides?.top,
                      temperature: options.overrides?.temperature,
                      promptTemplate: options.overrides?.promptTemplate,
                      exclude_category: options.overrides?.excludeCategory,
                      chainType: options.overrides?.chainType,
                      tokenLength: options.overrides?.tokenLength,
                      embeddingModelType: options.overrides?.embeddingModelType,
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
export async function pibChatGptApi(options: ChatRequest, symbol: string, indexName: string): Promise<AskResponse> {
  const response = await fetch('/pibChat' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        symbol:symbol,
        indexName: indexName,
        postBody: {
          values: [
            {
              recordId: 0,
              data: {
                text: '',
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
export async function getProspectusList(): Promise<Any> {
  const response = await fetch('/getProspectusList' , {
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
export async function getAllDocumentRuns(documentId: string): Promise<Any> {
  const response = await fetch('/getAllDocumentRuns' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        documentId:documentId,
      })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function getEvaluationQaDataSet(documentId: string): Promise<Any> {
  const response = await fetch('/getEvaluationQaDataSet' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        documentId:documentId,
      })
  });

  const parsedResponse: any = await response.json();
  if (response.status > 299 || !response.ok) {
      throw Error("Unknown error");
  }
  return parsedResponse;
}
export async function getEvaluationResults(documentId: string, runId:string): Promise<Any> {
  const response = await fetch('/getEvaluationResults' , {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
        documentId:documentId,
        runId:runId
      })
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
export async function uploadEvaluatorFile(formData:any) : Promise<string> {
  const response = await fetch('/uploadEvaluatorFile', {
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
export async function runEvaluation(overlap: string[], chunkSize : string[], splitMethod: string[], totalQuestions : string, model: string,
  embeddingModelType : string, promptStyle : string, fileName : string, retrieverType : string) : Promise<string> {
  const response = await fetch('/runEvaluation', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      fileName:fileName,
      retrieverType: retrieverType,
      promptStyle:promptStyle,
      totalQuestions:totalQuestions,
      embeddingModelType:embeddingModelType,
      postBody: {
        values: [
          {
            recordId: 0,
            data: {
              splitMethods: splitMethod,
              chunkSizes: chunkSize,
              overlaps : overlap,
            }
          }
        ]
      }
    })
  });

  const parsedResponse: EvalResponse = await response.json();
  if (response.status > 299 || !response.ok) {
      return "Error";
  }
  return parsedResponse.values[0].data.statusUri
}
export async function processSummary(indexNs: string, indexType: string, existingSummary : string, options : AskRequest) : Promise<AskResponse> {
  const response = await fetch('/processSummary', {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
      indexNs:indexNs,
      indexType: indexType,
      existingSummary: existingSummary,
      postBody: {
        values: [
          {
            recordId: 0,
            data: {
              text: '',
              overrides: {
                  promptTemplate: options.overrides?.promptTemplate,
                  fileName: options.overrides?.fileName,
                  topics: options.overrides?.topics,
                  embeddingModelType: options.overrides?.embeddingModelType,
                  chainType: options.overrides?.chainType,
                  temperature: options.overrides?.temperature,
                  tokenLength: options.overrides?.tokenLength,
                  top: options.overrides?.top,
                  deploymentType: options.overrides?.deploymentType,
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

export async function sqlAsk(question:string, top: number, embeddingModelType: string): Promise<SqlResponse> {
  const response = await fetch('/sqlAsk' , {
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
export async function sqlVisual(question:string, top: number, embeddingModelType:string): Promise<SqlResponse> {
  const response = await fetch('/sqlVisual' , {
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
                  useInternet:options.overrides?.useInternet,
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

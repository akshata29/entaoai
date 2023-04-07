import { AskRequest, AskResponse, ChatRequest, ChatResponse } from "./models";
export async function chatGptApi(options: ChatRequest, indexNs: string, indexType:string): Promise<AskResponse> {
    const url = process.env.chatGptUrl
    
    const response = await fetch(url, {
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


export function getCitationFilePath(citation: string): string {
    return `/content/${citation}`;
}

import { atom } from 'jotai';

export const enum Approaches {
    RetrieveThenRead = "rtr",
    ReadRetrieveRead = "rrr",
    ReadDecomposeAsk = "rda"
}


export type ChatMessage = {
    id: string; // Guid
    type: string; // "Message"
    role: string; // "User" || "Assistant"
    sessionId: string ; // Guid (same as ChatSession.id)
    tokens: number; // Number of tokens in the message
    timestamp: string; // ISO 8601
    content: string;
};

export type ChatSession = {
    id: string; // Guid
    type: string; // "Session"
    sessionId: string ; // Guid
    feature: string; // "chat" || "ask" || "sql"
    tokenUsed: number; // Number of tokens in all the message
    name: string;
    timestamp: string; // ISO 8601
    indexType: string; // "pinecone" || "cogsearch" || "cogsearchvs"
    indexName: string; 
    indexId: string; // Guid
    llmModel: string; // "openai" || "azureopenai"
    chainType: string // "stuff" || "refine" || "mapreduce"
    embeddingModelType: string; // "azureopenai" || "openai"
    messages?: ChatMessage[];
};

export const chatSessionsAtom = atom<ChatSession[]>([]);

export type AskRequestOverrides = {
    semanticRanker?: boolean;
    semanticCaptions?: boolean;
    excludeCategory?: string;
    top?: number;
    temperature?: number;
    promptTemplate?: string;
    promptTemplatePrefix?: string;
    promptTemplateSuffix?: string;
    suggestFollowupQuestions?: boolean;
    chainType?: string;
    tokenLength?: number;
    indexType?: string;
    indexes?: any;
    autoSpeakAnswers?: boolean;
    embeddingModelType?: string;
    firstSession?: boolean;
    session?: string;
    sessionId?: string;
    functionCall?: boolean;
    useInternet?: boolean;
    deploymentType?: string;
    fileName?: string;
    topics?: string[]
};

export type AskRequest = {
    question: string;
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type AskResponse = {
    answer: string;
    thoughts: string | null;
    data_points: string[];
    error?: string;
    sources?: string;
    nextQuestions?: string;
};

export type EvalRunResponse = {
    statusUri: string;
    error?: string;
}

export type SqlResponse = {
    answer: string;
    thoughts: string | null;
    data_points: string[];
    error?: string;
    sources?: string;
    nextQuestions?: string;
    toolInput?: string;
    observation?: string;
};

export type SpeechTokenResponse = {
    Token: string;
    Region: string
};

export type ChatTurn = {
    user: string;
    bot?: string;
};

export type ChatRequest = {
    history: ChatTurn[];
    approach: Approaches;
    overrides?: AskRequestOverrides;
};

export type ChatRespValues = {
    recordId: number,
    data: AskResponse
};

export type ChatResponse = {
    values: ChatRespValues[];
};

export type EvalRespValues = {
    recordId: number,
    data: EvalRunResponse
};

export type EvalResponse = {
    values: EvalRespValues[];
};

export type UserInfo = {
    access_token: string;
    expires_on: string;
    id_token: string;
    provider_name: string;
    user_claims: any[];
    user_id: string;
};
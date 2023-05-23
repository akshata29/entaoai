import { atom } from 'jotai';

export const enum Approaches {
    RetrieveThenRead = "rtr",
    ReadRetrieveRead = "rrr",
    ReadDecomposeAsk = "rda"
}


export type ChatMessage = {
    id: string; // Guid
    type: string; // "message" | "bot" | "user"
    sessionId: string ; // Guid
    tokens: number; // Number of tokens in the message
    timestamp: string; // ISO 8601
    content: string;
    indexType: string; // "pinecone" || "cogsearch" || "cogsearchvs"
    indexName: string; 
    indexId: string; // Guid
    llmModel: string; // "openai" || "azureopenai"
    chainType: string // "stuff" || "refine" || "mapreduce"
};

export type ChatSession = {
    id: string; // Guid
    sessionId: string ; // Guid
    feature: string; // "chat" || "ask" || "sql" || "chat3"
    tokenUsed: number; // Number of tokens in the message
    name: string;
    timestamp: string; // ISO 8601
    messages: ChatMessage[];
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

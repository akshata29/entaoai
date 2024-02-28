import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import Markdown from '@pity/vite-plugin-react-markdown'
import EnvironmentPlugin from 'vite-plugin-environment'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react(), 
        EnvironmentPlugin('all'),
        Markdown({
        wrapperComponentName: 'ReactMarkdown',
       // wrapperComponentPath: './src/pages/help/help',
      })],
    build: {
        outDir: "../backend/static",
        emptyOutDir: true,
        sourcemap: true
    },
    server: {
        port:5172,
        proxy: {
            "/ask": "http://127.0.0.1:5002",
            "/askAgent": "http://127.0.0.1:5002",
            "/askTaskAgent": "http://127.0.0.1:5002",
            "/chat": "http://127.0.0.1:5002",
            "/chatStream": "http://127.0.0.1:5002",
            "/chatGpt": "http://127.0.0.1:5002",
            "/content": "http://127.0.0.1:5002",
            "/convertCode": "http://127.0.0.1:5002",
            "/deleteIndexSession": "http://127.0.0.1:5002",
            "/getAllDocumentRuns": "http://127.0.0.1:5002",
            "/getAllIndexSessions": "http://127.0.0.1:5002",
            "/getAllSessions": "http://127.0.0.1:5002",
            "/getCashFlow": "http://127.0.0.1:5002",
            "/getDocumentList": "http://127.0.0.1:5002",
            "/getEvaluationResults": "http://127.0.0.1:5002",
            "/getEvaluationQaDataSet": "http://127.0.0.1:5002",
            "/getIncomeStatement": "http://127.0.0.1:5002",
            "/getIndexSession": "http://127.0.0.1:5002",
            "/getIndexSessionDetail": "http://127.0.0.1:5002",
            "/getPitchBook": "http://127.0.0.1:5002",
            "/getProspectusList": "http://127.0.0.1:5002",
            "/getSocialSentiment": "http://127.0.0.1:5002",
            "/getNews": "http://127.0.0.1:5002",
            "/indexManagement": "http://127.0.0.1:5002",
            "/kbQuestionManagement": "http://127.0.0.1:5002",
            "/processDoc": "http://127.0.0.1:5002",
            "/promptGuru": "http://127.0.0.1:5002",
            "/processSummary": "http://127.0.0.1:5002",
            "/refreshIndex": "http://127.0.0.1:5002",
            "/refreshVideoIndex": "http://127.0.0.1:5002",
            "/refreshQuestions": "http://127.0.0.1:5002",
            "/refreshIndexQuestions": "http://127.0.0.1:5002",
            "/renameIndexSession": "http://127.0.0.1:5002",
            "/runEvaluation": "http://127.0.0.1:5002",
            "/smartAgent": "http://127.0.0.1:5002",
            "/sqlChat": "http://127.0.0.1:5002",
            "/sqlAsk": "http://127.0.0.1:5002",
            "/sqlChain": "http://127.0.0.1:5002",
            "/sqlVisual": "http://127.0.0.1:5002",
            "/speechToken": "http://127.0.0.1:5002",
            "/speech": "http://127.0.0.1:5002",
            "/summarizer": "http://127.0.0.1:5002",
            "/textAnalytics": "http://127.0.0.1:5002",
            "/uploadFile": "http://127.0.0.1:5002",
            "/uploadBinaryFile": "http://127.0.0.1:5002",
            "/uploadEvaluatorFile": "http://127.0.0.1:5002",
            "/uploadSummaryBinaryFile": "http://127.0.0.1:5002",
            "/verifyPassword": "http://127.0.0.1:5002"
        }
        // proxy: {
        //     "/ask": {
        //          target: 'http://127.0.0.1:5002',
        //          changeOrigin: true,
        //          secure: false,
        //      }
        // }
    }
});

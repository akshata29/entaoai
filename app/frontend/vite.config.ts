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
        proxy: {
            "/ask": "http://127.0.0.1:5000",
            "/askAgent": "http://127.0.0.1:5000",
            "/askTaskAgent": "http://127.0.0.1:5000",
            "/chat": "http://127.0.0.1:5000",
            "/chat3": "http://127.0.0.1:5000",
            "/content": "http://127.0.0.1:5000",
            "/convertCode": "http://127.0.0.1:5000",
            "/indexManagement": "http://127.0.0.1:5000",
            "/kbQuestionManagement": "http://127.0.0.1:5000",
            "/processDoc": "http://127.0.0.1:5000",
            "/promptGuru": "http://127.0.0.1:5000",
            "/processSummary": "http://127.0.0.1:5000",
            "/refreshIndex": "http://127.0.0.1:5000",
            "/refreshQuestions": "http://127.0.0.1:5000",
            "/refreshIndexQuestions": "http://127.0.0.1:5000",
            "/secSearch": "http://127.0.0.1:5000",
            "/smartAgent": "http://127.0.0.1:5000",
            "/sqlChat": "http://127.0.0.1:5000",
            "/sqlChain": "http://127.0.0.1:5000",
            "/speechToken": "http://127.0.0.1:5000",
            "/speech": "http://127.0.0.1:5000",
            "/summarizer": "http://127.0.0.1:5000",
            "/summaryAndQa": "http://127.0.0.1:5000",
            "/textAnalytics": "http://127.0.0.1:5000",
            "/uploadFile": "http://127.0.0.1:5000",
            "/uploadBinaryFile": "http://127.0.0.1:5000",
            "/uploadSummaryBinaryFile": "http://127.0.0.1:5000",
            "/verifyPassword": "http://127.0.0.1:5000"
        }
        // proxy: {
        //     "/ask": {
        //          target: 'http://127.0.0.1:5000',
        //          changeOrigin: true,
        //          secure: false,
        //      }
        // }
    }
});

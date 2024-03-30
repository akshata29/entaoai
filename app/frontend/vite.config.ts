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
            "/chat": "http://127.0.0.1:5002",
            "/chatStream": "http://127.0.0.1:5002",
            "/chatGpt": "http://127.0.0.1:5002",
            "/content": "http://127.0.0.1:5002",
            "/deleteIndexSession": "http://127.0.0.1:5002",
            "/getAllIndexSessions": "http://127.0.0.1:5002",
            "/getAllSessions": "http://127.0.0.1:5002",
            "/getDocumentList": "http://127.0.0.1:5002",
            "/getIndexSession": "http://127.0.0.1:5002",
            "/getIndexSessionDetail": "http://127.0.0.1:5002",
            "/indexManagement": "http://127.0.0.1:5002",
            "/kbQuestionManagement": "http://127.0.0.1:5002",
            "/processDoc": "http://127.0.0.1:5002",
            "/refreshIndex": "http://127.0.0.1:5002",
            "/refreshQuestions": "http://127.0.0.1:5002",
            "/refreshIndexQuestions": "http://127.0.0.1:5002",
            "/renameIndexSession": "http://127.0.0.1:5002",
            "/uploadFile": "http://127.0.0.1:5002",
            "/uploadBinaryFile": "http://127.0.0.1:5002",
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

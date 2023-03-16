import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        outDir: "../backend/static",
        emptyOutDir: true,
        sourcemap: true
    }
    // server: {
        // port: 3001,
        // proxy: {
        //     "/ask": "http://localhost:5000",
        //     "/chat": "http://localhost:5000"
        // }
    // }
});

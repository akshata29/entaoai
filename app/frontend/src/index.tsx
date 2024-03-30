import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, Routes, Route } from "react-router-dom";
import { initializeIcons } from "@fluentui/react";

import "./index.css";

import Layout from "./pages/layout/Layout";
import NoPage from "./pages/NoPage";
import ChatGpt from "./pages/chatgpt/ChatGpt";
import OneShot from "./pages/oneshot/OneShot";
import Upload from "./pages/upload/Upload";
import Help from "./pages/help/Help";
import Admin from "./pages/admin/Admin";

initializeIcons();

export default function App() {
    return (
        <HashRouter>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route path="upload" element={<Upload />} />
                    <Route path="qa" element={<OneShot />} />
                    <Route path="admin" element={<Admin />} />
                    <Route index element={<ChatGpt />} />
                    <Route path="help" index element={<Help />} />
                    <Route path="*" element={<NoPage />} />
                </Route>
            </Routes>
        </HashRouter>
    );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);

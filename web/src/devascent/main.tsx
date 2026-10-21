import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import "reactflow/dist/style.css";
import "./theme.css";
import Onboard from "./routes/Onboard";
import Roadmap from "./routes/Roadmap";
import Studio from "./routes/Studio";
import Interview from "./routes/Interview";

ReactDOM.createRoot(document.getElementById("devascent-root")!).render(
  <React.StrictMode>
    <HashRouter>
      <Routes>
        <Route path="/" element={<Onboard />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="/learn/:nodeId" element={<Studio />} />
        <Route path="/interview/:nodeId" element={<Interview />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  </React.StrictMode>,
);

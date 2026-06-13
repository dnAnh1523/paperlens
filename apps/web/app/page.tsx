"use client";

import { useState } from "react";

import { ChatWorkspace } from "./components/ChatWorkspace";
import { DocumentLibrary } from "./components/DocumentLibrary";
import { PaperLensDocument } from "../lib/api";

type ScopedChatRequest = {
  requestKey: number;
  documentId: string;
  title: string;
  originalFilename: string;
};

export default function HomePage() {
  const [scopedChatRequest, setScopedChatRequest] = useState<ScopedChatRequest | null>(null);

  function handleChatWithDocument(document: PaperLensDocument) {
    setScopedChatRequest((currentRequest) => ({
      requestKey: (currentRequest?.requestKey ?? 0) + 1,
      documentId: document.id,
      title: document.title,
      originalFilename: document.original_filename,
    }));
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Applied CS Thesis + Production Project</p>
        <h1>PaperLens</h1>
        <p className="subtitle">
          A local-native multimodal RAG assistant for scientific and technical papers.
        </p>
        <div className="cardGrid">
          <div className="card">
            <h2>Evidence types</h2>
            <p>Text, tables, figures, charts, equations, captions, and page layout.</p>
          </div>
          <div className="card">
            <h2>Local dev stack</h2>
            <p>FastAPI, Next.js, SQLite, local file storage, and zero-budget local retrieval.</p>
          </div>
          <div className="card">
            <h2>Research target</h2>
            <p>Compare text-only and evidence-type-aware multimodal RAG variants.</p>
          </div>
        </div>
      </section>

      <ChatWorkspace scopedChatRequest={scopedChatRequest} />
      <DocumentLibrary onChatWithDocument={handleChatWithDocument} />
    </main>
  );
}

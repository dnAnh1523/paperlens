import { ChatWorkspace } from "./components/ChatWorkspace";
import { DocumentLibrary } from "./components/DocumentLibrary";

export default function HomePage() {
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
            <p>FastAPI, Next.js, SQLite, local file storage, and Qdrant Client local mode.</p>
          </div>
          <div className="card">
            <h2>Research target</h2>
            <p>Compare text-only and evidence-type-aware multimodal RAG variants.</p>
          </div>
        </div>
      </section>

      <ChatWorkspace />
      <DocumentLibrary />
    </main>
  );
}

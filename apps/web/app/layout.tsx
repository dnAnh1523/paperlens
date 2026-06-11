import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PaperLens",
  description: "Multimodal RAG assistant for scientific and technical papers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

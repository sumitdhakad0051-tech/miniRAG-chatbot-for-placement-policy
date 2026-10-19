import "dotenv/config";
import fs from "fs";
import faiss from "faiss-node";
import { GoogleGenAI } from "@google/genai";

const { IndexFlatIP } = faiss;
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const CHAT_MODEL = process.env.GEMINI_MODEL || "gemini-3.8-flash";
const EMBED_MODEL = "gemini-embedding-001";
const TOP_K = 4;

const chunks = JSON.parse(fs.readFileSync("store/chunks.json", "utf-8"));
const index = IndexFlatIP.read("store/faiss.index");

const SYSTEM = `You are an assistant that answers questions about the MNIT Jaipur placement policy.
Answer ONLY using the context provided. If the answer is not in the context, say you could not find it in the documents.
Mention the section number(s) you used. Be concise and clear.`;

function normalize(v) {
  const norm = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
  return v.map((x) => x / norm);
}

async function withRetry(fn, tries = 5) {
  for (let i = 1; i <= tries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (![429, 503].includes(err.status) || i === tries) throw err;
      const wait = i * 4000;
      console.log(`API busy/limit (${err.status}), retry ${i} in ${wait / 1000}s...`);
      await new Promise((r) => setTimeout(r, wait));
    }
  }
}

export async function retrieve(question, k = TOP_K) {
  const res = await withRetry(() =>
    ai.models.embedContent({
      model: EMBED_MODEL,
      contents: question,
      config: { taskType: "RETRIEVAL_QUERY" },
    })
  );
  const { labels, distances } = index.search(normalize(res.embeddings[0].values), k);
  return labels.map((id, i) => ({ ...chunks[id], score: distances[i] }));
}

export async function ask(question) {
  const hits = await retrieve(question);
  const context = hits
    .map((h, i) => `[${i + 1}] (${h.section}, page ${h.page})\n${h.text}`)
    .join("\n\n");

  const res = await withRetry(() =>
    ai.models.generateContent({
      model: CHAT_MODEL,
      contents: `Context:\n${context}\n\nQuestion: ${question}`,
      config: { systemInstruction: SYSTEM, temperature: 0.2 },
    })
  );

  return {
    answer: res.text,
    sources: hits.map((h) => ({
      source: h.source,
      section: h.section,
      page: h.page,
      score: h.score,
    })),
  };
}
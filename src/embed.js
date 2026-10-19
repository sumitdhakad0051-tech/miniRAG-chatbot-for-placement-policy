import "dotenv/config";
import fs from "fs";
import faiss from "faiss-node";
import { GoogleGenAI } from "@google/genai";

const { IndexFlatIP } = faiss;
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const BATCH = 20;

const chunks = JSON.parse(fs.readFileSync("store/chunks.json", "utf-8"));

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
      const wait = i * 5000;
      console.log(`API busy/limit (${err.status}), retry ${i} in ${wait / 1000}s...`);
      await new Promise((r) => setTimeout(r, wait));
    }
  }
}

const vectors = [];
for (let i = 0; i < chunks.length; i += BATCH) {
  const batch = chunks.slice(i, i + BATCH);
  const res = await withRetry(() =>
    ai.models.embedContent({
      model: "gemini-embedding-001",
      contents: batch.map((c) => c.text),
      config: { taskType: "RETRIEVAL_DOCUMENT" },
    })
  );
  res.embeddings.forEach((e) => vectors.push(normalize(e.values)));
  console.log(`Embedded ${vectors.length}/${chunks.length}`);
  await new Promise((r) => setTimeout(r, 1000));
}

const index = new IndexFlatIP(vectors[0].length);
for (const v of vectors) index.add(v);
index.write("store/faiss.index");
console.log(`FAISS index saved: ${index.ntotal()} vectors, dimension ${vectors[0].length}`);
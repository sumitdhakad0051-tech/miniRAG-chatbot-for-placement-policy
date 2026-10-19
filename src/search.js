import "dotenv/config";
import fs from "fs";
import faiss from "faiss-node";
import { GoogleGenAI } from "@google/genai";

const { IndexFlatIP } = faiss;
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const chunks = JSON.parse(fs.readFileSync("store/chunks.json", "utf-8"));
const index = IndexFlatIP.read("store/faiss.index");

function normalize(v) {
  const norm = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
  return v.map((x) => x / norm);
}

const question = process.argv.slice(2).join(" ") || "What is the 1.5X rule?";

const res = await ai.models.embedContent({
  model: "gemini-embedding-001",
  contents: question,
  config: { taskType: "RETRIEVAL_QUERY" },
});

const { labels, distances } = index.search(normalize(res.embeddings[0].values), 3);

console.log(`Question: ${question}\n`);
labels.forEach((id, i) => {
  const c = chunks[id];
  console.log(`#${i + 1} score=${distances[i].toFixed(3)} [${c.section}, page ${c.page}]`);
  console.log(c.text + "\n");
});
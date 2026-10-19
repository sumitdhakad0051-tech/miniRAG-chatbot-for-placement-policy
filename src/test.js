import "dotenv/config";
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const emb = await ai.models.embedContent({
  model: "gemini-embedding-001",
  contents: "hello world",
});
console.log("Embedding size:", emb.embeddings[0].values.length);

const res = await ai.models.generateContent({
  model: "gemini-3.8-flash",
  contents: "Say hi in one line",
});
console.log(res.text);
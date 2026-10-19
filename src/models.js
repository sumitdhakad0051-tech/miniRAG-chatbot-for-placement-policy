import "dotenv/config";
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
const pager = await ai.models.list();
for await (const m of pager) {
  if (m.name.includes("gemini") && !m.name.includes("embedding")) console.log(m.name);
}
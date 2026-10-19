import "dotenv/config";
import express from "express";
import { ask } from "./rag.js";

const app = express();
app.use(express.json());
app.use(express.static("public"));

app.post("/api/ask", async (req, res) => {
  const question = (req.body.question || "").trim();
  if (!question) return res.status(400).json({ error: "Question is required" });
  try {
    res.json(await ask(question));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Could not get an answer right now. Please try again." });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
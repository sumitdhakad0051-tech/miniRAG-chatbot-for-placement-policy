import "dotenv/config";
import express from "express";

const app = express();
app.use(express.json());
app.use(express.static("public"));

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

app.post("/api/ask", async (req, res) => {
  const question = (req.body.question || "").trim();
  if (!question) return res.status(400).json({ error: "Question is required" });

  try {
    const r = await fetch(`${BACKEND_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await r.json();
    if (!r.ok) return res.status(r.status).json({ error: data.detail || "Backend error" });
    res.json(data);
  } catch (err) {
    console.error(err);
    res.status(502).json({ error: "Backend is not reachable. Is the Python server running?" });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Frontend running on http://localhost:${PORT}`));
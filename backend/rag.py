import json
import os
import time
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBED_MODEL = "gemini-embedding-001"
TOP_K = 4

chunks = json.loads((ROOT / "store" / "chunks.json").read_text(encoding="utf-8"))
index = faiss.read_index(str(ROOT / "store" / "faiss.index"))

SYSTEM = """You are an assistant that answers questions about the MNIT Jaipur placement policy and related placement documents.
Answer ONLY using the context provided. If the answer is not in the context, say you could not find it in the documents.
Mention the document and section number(s) you used. Be concise and clear."""


def with_retry(fn, tries=5):
    """429 (rate limit) aur 503 (server busy) par thodi der ruk kar dobara try karta hai."""
    for i in range(1, tries + 1):
        try:
            return fn()
        except Exception as err:
            code = getattr(err, "code", None)
            if code not in (429, 503) or i == tries:
                raise
            wait = i * 4
            print(f"API busy/limit ({code}), retry {i} in {wait}s...")
            time.sleep(wait)


def retrieve(question: str, k: int = TOP_K):
    res = with_retry(
        lambda: client.models.embed_content(
            model=EMBED_MODEL,
            contents=question,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
    )
    query = np.array([res.embeddings[0].values], dtype="float32")
    faiss.normalize_L2(query)
    scores, ids = index.search(query, k)
    return [
        {**chunks[int(idx)], "score": float(score)}
        for score, idx in zip(scores[0], ids[0])
        if idx != -1
    ]


def ask(question: str):
    hits = retrieve(question)
    context = "\n\n".join(
        f"[{i + 1}] ({h['source']}, {h['section']}, page {h['page']})\n{h['text']}"
        for i, h in enumerate(hits)
    )
    res = with_retry(
        lambda: client.models.generate_content(
            model=CHAT_MODEL,
            contents=f"Context:\n{context}\n\nQuestion: {question}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.2),
        )
    )
    return {
        "answer": res.text,
        "sources": [
            {"source": h["source"], "section": h["section"], "page": h["page"], "score": h["score"]}
            for h in hits
        ],
    }
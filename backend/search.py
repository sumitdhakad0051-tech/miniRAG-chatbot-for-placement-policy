import json
import os
import sys
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

chunks = json.loads(Path("store/chunks.json").read_text(encoding="utf-8"))
index = faiss.read_index("store/faiss.index")

question = " ".join(sys.argv[1:]) or "What is the 1.5X rule?"

res = client.models.embed_content(
    model="gemini-embedding-001",
    contents=question,
    config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
)
query = np.array([res.embeddings[0].values], dtype="float32")
faiss.normalize_L2(query)

scores, ids = index.search(query, 3)

print(f"Question: {question}\n")
for rank, (score, idx) in enumerate(zip(scores[0], ids[0]), start=1):
    c = chunks[idx]
    print(f"#{rank} score={score:.3f} [{c['section']}, page {c['page']}]")
    print(c["text"] + "\n")
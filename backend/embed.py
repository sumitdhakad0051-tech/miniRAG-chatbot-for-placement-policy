import json
import os
import time
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

EMBED_MODEL = "gemini-embedding-001"
BATCH = 20
CHUNKS_FILE = Path("store/chunks.json")
INDEX_FILE = Path("store/faiss.index")


def with_retry(fn, tries=5):
    """429 (rate limit) aur 503 (server busy) par thodi der ruk kar dobara try karta hai."""
    for i in range(1, tries + 1):
        try:
            return fn()
        except Exception as err:
            code = getattr(err, "code", None)
            if code not in (429, 503) or i == tries:
                raise
            wait = i * 5
            print(f"API busy/limit ({code}), retry {i} in {wait}s...")
            time.sleep(wait)


def main():
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    vectors = []

    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        res = with_retry(
            lambda: client.models.embed_content(
                model=EMBED_MODEL,
                contents=[c["text"] for c in batch],
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
        )
        vectors.extend(e.values for e in res.embeddings)
        print(f"Embedded {len(vectors)}/{len(chunks)}")
        time.sleep(1)

    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)  # length 1 karo, taaki inner product = cosine similarity

    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, str(INDEX_FILE))
    print(f"FAISS index saved: {index.ntotal} vectors, dimension {matrix.shape[1]}")


if __name__ == "__main__":
    main()
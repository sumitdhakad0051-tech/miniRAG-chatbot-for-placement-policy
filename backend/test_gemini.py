import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

emb = client.models.embed_content(model="gemini-embedding-001", contents="hello world")
print("Embedding size:", len(emb.embeddings[0].values))

res = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    contents="Say hi in one line",
)
print(res.text)
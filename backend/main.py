from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rag import ask

app = FastAPI(title="Mini RAG backend")


class Question(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask_endpoint(body: Question):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    try:
        return ask(question)
    except Exception as err:
        print("RAG error:", err)
        raise HTTPException(status_code=502, detail="Could not get an answer right now. Please try again.")
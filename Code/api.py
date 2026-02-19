from fastapi import FastAPI
from pydantic import BaseModel
from Code.agent import ask_agent
import os
import json

app = FastAPI()

CHAT_DIR = "chat_history"
os.makedirs(CHAT_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    question: str
    session_id: str


def chat_file(session_id):
    return os.path.join(CHAT_DIR, f"{session_id}.json")


def load_chat(session_id):
    path = chat_file(session_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_chat(session_id, messages):
    path = chat_file(session_id)
    with open(path, "w") as f:
        json.dump(messages, f, indent=2)


@app.get("/")
def root():
    return {"message": "Invoice AI API running"}


@app.post("/chat")
def chat(request: QueryRequest):

    history = load_chat(request.session_id)

    # save user message
    history.append({
        "role": "user",
        "content": request.question
    })

    answer = ask_agent(
        request.question,
        request.session_id
    )

    # save assistant response
    history.append({
        "role": "assistant",
        "content": answer
    })

    save_chat(request.session_id, history)

    return {"answer": answer}


@app.get("/history/{session_id}")
def get_history(session_id):
    return load_chat(session_id)

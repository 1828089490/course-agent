import os
import secrets

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]
OPENAI_MODEL = os.environ["OPENAI_MODEL"]
ACCESS_CODE = os.environ["ACCESS_CODE"]

client = OpenAI()
app = FastAPI()


class AskRequest(BaseModel):
    question: str


@app.get("/")
def hello():
    return {"message": "你好"}


@app.post("/ask")
def ask(req: AskRequest, x_access_code: str | None = Header(default=None)):
    if x_access_code is None or not secrets.compare_digest(x_access_code, ACCESS_CODE):
        raise HTTPException(status_code=401, detail="访问口令错误")

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=req.question,
    )
    return {"question": req.question, "answer": response.output_text}
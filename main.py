import os

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

app = FastAPI()


class CourseCreate(BaseModel):
    name: str
    teacher: str | None = None


@app.get("/")
def hello():
    return {"message": "你好"}


@app.get("/courses/{course_name}")
def get_course(course_name):
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT id, name, teacher FROM courses WHERE name = %s",
            (course_name,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="课程不存在")

    return {"id": row[0], "name": row[1], "teacher": row[2]}


@app.post("/courses", status_code=201)
def create_course(course: CourseCreate):
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(
                "INSERT INTO courses (name, teacher) VALUES (%s, %s) RETURNING id",
                (course.name, course.teacher),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="课程已存在")

    return {"id": row[0], "name": course.name, "teacher": course.teacher}
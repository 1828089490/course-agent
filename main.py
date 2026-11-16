from fastapi import FastAPI, HTTPException
import psycopg

DATABASE_URL = "postgresql://course:course_dev_pw@localhost:5432/course_agent"
app=FastAPI()
@app.get("/")
def hello():
    return {"message": "你好"}

@app.get("/courses/{course_name}")
def c(course_name):
    with psycopg.connect(DATABASE_URL) as conn:
        row=conn.execute(
            "SELECT id, name, teacher FROM courses WHERE name = %s",
            (course_name,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404,detail="课程不存在")
    return {"id": row[0], "name": row[1], "teacher": row[2]}
   
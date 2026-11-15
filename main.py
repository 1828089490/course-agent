from fastapi import FastAPI
app=FastAPI()
@app.get("/")
def hello():
    return {"message": "你好"}

@app.get("/courses/{x}")
def c(x):
    return {"course": x, "message": "正在查询这门课的资料"}

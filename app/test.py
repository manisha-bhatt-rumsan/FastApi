from fastapi import FastAPI
from quiz.routes import quiz_routes


app = FastAPI()

@app.get("/")
def test():
    return {"message":"server is running"}

app.include_router(quiz_routes)
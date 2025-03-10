from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router

app = FastAPI(
    title="HeavyMetal Backend",
    description="Backend for HeavyMetal Music Streaming Service",
    port=8080,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/ping")
async def ping():
    return {"message": "pong", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.post("/ping")
async def pingPost(data: dict):
    print(data)
    # get any data
    return {
        "message": "pong",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data,
    }

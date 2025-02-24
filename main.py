from fastapi import FastAPI
from datetime import datetime
from routes import router

app = FastAPI(
    title="HeavyMetal Backend",
    description="Backend for HeavyMetal Music Streaming Service",
    port=8080,
    tags=["General Purpose APIs", "Auth", "Users", "Public"],
)

@app.get('/ping')
async def ping():
    return {
            "message": "pong",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

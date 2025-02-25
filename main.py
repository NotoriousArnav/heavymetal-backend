from fastapi import FastAPI
from datetime import datetime
from routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HeavyMetal Backend",
    description="Backend for HeavyMetal Music Streaming Service",
    port=8080,
    tags=["General Purpose APIs", "Auth", "Users", "Public"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get('/ping')
async def ping():
    return {
            "message": "pong",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

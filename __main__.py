import os

import uvicorn
from dotenv import load_dotenv

import db

load_dotenv()

if __name__ == "__main__":
    db.init_db()
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8080)),
        # reload
        reload=True,
    )

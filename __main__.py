from dotenv import load_dotenv
import uvicorn
import db
import os

load_dotenv()

if __name__ == "__main__":
    db.init_db()
    uvicorn.run(
            "main:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8080)),
            # reload
            reload=True
    )

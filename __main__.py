from main import app
from dotenv import load_dotenv
import uvicorn
import db
import os

load_dotenv()

if __name__ == "__main__":
    db.init_db()
    uvicorn.run(
            app,
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8080)),
    )

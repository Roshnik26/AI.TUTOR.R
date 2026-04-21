"""
Main application file for FastAPI app.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.health_router import router as health_router
from app.api.routes import router as api_router 
from app.database.sql_db import engine, Base
import app.models.tutor_models

# Initialize SQLite database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "AI Tutor",
    version="2.0.0",
)

# include routers
app.include_router(health_router, tags=["health"])
app.include_router(api_router, prefix="/api", tags=["api"])

# Mount static files for the frontend
import os
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    if os.path.exists("app/static/index.html"):
        return FileResponse("app/static/index.html")
    return {"message": "Frontend not found"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.config import get_settings
from src.core.database import engine, Base
from src.api import routes # Import the new router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized.")
    yield

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Register the router
app.include_router(routes.router) 

@app.get("/health")
async def health_check():
    return {"status": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
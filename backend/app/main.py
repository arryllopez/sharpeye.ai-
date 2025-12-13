from fastapi import FastAPI
from app.api.nba_routes import router as nba_router

app = FastAPI(title="SharpEye Backend", version="0.1.0")

app.include_router(nba_router)

@app.get("/health")
def health():
    return {"status": "ok"}

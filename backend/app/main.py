from fastapi import FastAPI
from app.routers import health, props

app = FastAPI(title="SharpEye.ai Backend")

app.include_router(health.router, tags=["health"])
app.include_router(props.router, prefix="/props", tags=["props"])
# props - simulate() will have route 127... /props/simulate 
# due to this line --> @router.post("/simulate")

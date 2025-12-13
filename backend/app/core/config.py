from pydantic import BaseModel
import os
from dotenv import load_dotenv

# 🔑 THIS loads .env when the app starts
load_dotenv()

class Settings(BaseModel):
    environment: str = os.getenv("ENV", "dev")

    theodds_base_url: str = os.getenv(
        "THEODDS_BASE_URL",
        "https://api.the-odds-api.com"
    )

    theodds_api_key: str = os.getenv("THEODDS_API_KEY", "")

settings = Settings()

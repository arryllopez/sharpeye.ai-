from pydantic import BaseModel
import os
from dotenv import load_dotenv

#load the .env file, hidden variables into environment variables
load_dotenv()

class Settings(BaseModel):
    environment: str = os.getenv("ENV", "dev")

    theodds_base_url: str = os.getenv(
        "THEODDS_BASE_URL",
        "https://api.the-odds-api.com"
    )

    theodds_api_key: str = os.getenv("THEODDS_API_KEY", "")

    database_url: str = os.getenv("DATABASE_URL", "") #loading database url from environment variables

settings = Settings()

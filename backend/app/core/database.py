#setting up the connection to Railway's postgresql database

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings


def get_async_database_url(url: str) -> str:
    #convert a PostgreSQL URL to use asyncpg driver
    #handling both "postgres://" and "postgresql://" prefixes
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

database_url = get_async_database_url(settings.database_url)#async drivers are better for handling multiple concurrent requests
#synchronous drivers handle concurrent requests by assigning a thread to each request, so for example, 100 concurrent requests (queries) woudl take 100 thread
# async drivers use a single thread to manage multiple requests, switching between them as needed, which is more efficient and scalable 

# Create async engine
engine = create_async_engine(
    database_url,
    echo=False,  # lets set to false for now and then true later for sql debugging
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, #initialize the session  with the async engine aboe
    class_=AsyncSession, #specify the session class to use, async 
    #prevent attributes from expiring after commit
    #this is useful because game logs are read-only historical data
    #so we can keep data in session memory without re-querying the data during th esession
    #memory is still freed when session closes (end of each http request)
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

# dependency for getting DB session

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() #ensure the session is closed after use4
            #returns connection to pool and frees session memory
            #this happens automatically per-request, so memory doesn't accumulate
            #this addresses the issue of caching memory getting full over time with too many saved data from the db

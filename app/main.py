from fastapi import FastAPI
from app.router import router
from app.database import init_db
from app.storage import get_minio_client, ensure_bucket_exists


app = FastAPI(
    title="Animal Picture Microservice",
    description="Fetches and stores cat, dog, and bear images",
    version="1.0.0"
)

# Include router at module level
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and MinIO bucket on application startup."""
    init_db()
    ensure_bucket_exists(get_minio_client())


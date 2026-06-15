from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy.orm import Session
from minio import Minio
from app.database import get_db
from app.storage import get_minio_client
from app.schemas import FetchRequest, FetchResponse, FetchedImage
from app import service


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


def get_minio():
    """Dependency function that provides a MinIO client instance."""
    return get_minio_client()


@router.post("/animals/fetch", response_model=FetchResponse)
async def fetch_animals(
    request: FetchRequest,
    db: Session = Depends(get_db),
    minio_client: Minio = Depends(get_minio),
):
    """Fetch animal images from the internet and store them in MinIO and database."""
    # Fetch and save images
    saved_records = await service.fetch_and_save(
        animal_type=request.animal_type,
        count=request.count,
        db=db,
        minio_client=minio_client
    )
    
    # Build response
    fetched_images = [
        FetchedImage(
            id=record.id,
            animal_type=record.animal_type,
            image_url=record.image_url,
            minio_key=record.minio_key,
            fetched_at=record.fetched_at
        )
        for record in saved_records
    ]
    
    return FetchResponse(
        saved=fetched_images,
        count=len(fetched_images)
    )


@router.get("/animals/last/{animal_type}")
async def get_last(
    animal_type: str,
    db: Session = Depends(get_db),
    minio_client: Minio = Depends(get_minio)
):
    """Get the most recently fetched image for a given animal type."""
    result = service.get_last_image(animal_type, db, minio_client)
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No images found for this animal type"
        )
    
    image_bytes, record = result
    
    return Response(
        content=image_bytes,
        media_type="image/jpeg"
    )


@router.get("/animals/history/{animal_type}")
async def get_history(
    animal_type: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get the history of fetched images for a given animal type."""
    records = service.get_history(animal_type, db, limit)
    
    if not records:
        return []
    
    return [
        {
            "id": record.id,
            "animal_type": record.animal_type,
            "image_url": record.image_url,
            "minio_key": record.minio_key,
            "fetched_at": record.fetched_at.isoformat()
        }
        for record in records
    ]


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main UI page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}



import asyncio
import uuid
from sqlalchemy.orm import Session
from minio import Minio
from app.models import AnimalPicture
from app.animal_clients import fetch_animal
from app import storage


async def fetch_and_save(
    animal_type: str,
    count: int,
    db: Session,
    minio_client: Minio
):
    """
    Fetch multiple animal images in parallel and save them to MinIO and database.
    
    Args:
        animal_type: Type of animal ("cat", "dog", or "bear")
        count: Number of images to fetch
        db: SQLAlchemy database session
        minio_client: MinIO client instance
        
    Returns:
        list[AnimalPicture]: List of saved database records
    """
    # Fetch all images in parallel
    tasks = [fetch_animal(animal_type) for _ in range(count)]
    results = await asyncio.gather(*tasks)
    
    saved_records = []
    
    # Process each fetched image
    for image_bytes, url in results:
        # Generate unique object key
        key = f"{animal_type}/{uuid.uuid4()}.jpg"
        
        # Upload to MinIO
        storage.put_image(minio_client, key, image_bytes)
        
        # Create database record
        record = AnimalPicture(
            animal_type=animal_type,
            image_url=url,
            minio_key=key
        )
        
        # Add to session and tracking list
        db.add(record)
        saved_records.append(record)
    
    # Commit all records at once
    db.commit()
    
    # Refresh records to get auto-generated IDs
    for record in saved_records:
        db.refresh(record)
    
    return saved_records


def get_last_image(
    animal_type: str,
    db: Session,
    minio_client: Minio
):
    """
    Get the most recently fetched image for a given animal type.
    
    Args:
        animal_type: Type of animal ("cat", "dog", or "bear")
        db: SQLAlchemy database session
        minio_client: MinIO client instance
        
    Returns:
        tuple: (image_bytes, record) or None if no images found
    """
    # Query for most recent record
    record = db.query(AnimalPicture)\
        .filter(AnimalPicture.animal_type == animal_type)\
        .order_by(AnimalPicture.fetched_at.desc())\
        .first()
    
    if record is None:
        return None
    
    # Retrieve image from MinIO
    image_bytes = storage.get_image(minio_client, record.minio_key)
    
    return (image_bytes, record)


def get_history(
    animal_type: str,
    db: Session,
    limit: int = 10
):
    """
    Get the history of fetched images for a given animal type.
    
    Args:
        animal_type: Type of animal ("cat", "dog", or "bear")
        db: SQLAlchemy database session
        limit: Maximum number of records to return (default: 10)
        
    Returns:
        list[AnimalPicture]: List of database records, most recent first
    """
    records = db.query(AnimalPicture)\
        .filter(AnimalPicture.animal_type == animal_type)\
        .order_by(AnimalPicture.fetched_at.desc())\
        .limit(limit)\
        .all()
    
    return records


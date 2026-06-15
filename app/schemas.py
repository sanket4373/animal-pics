from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal



class FetchRequest(BaseModel):
    """Request schema for fetching animal images."""
    animal_type: Literal["dog", "bear"]
    count: int = Field(ge=1, le=20)


class FetchedImage(BaseModel):
    """Schema for a single fetched and stored animal image."""
    id: int
    animal_type: str
    image_url: str
    minio_key: str
    fetched_at: datetime
    

class FetchResponse(BaseModel):
    """Response schema containing fetched images."""
    saved: list[FetchedImage]
    count: int



    

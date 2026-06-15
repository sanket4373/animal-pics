from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class AnimalPicture(Base):
    __tablename__ = 'animal_pictures'
    id = Column(Integer, primary_key=True, index=True)
    animal_type = Column(String,nullable=False,index=True)
    image_url= Column(String,nullable=False)
    minio_key = Column(String, nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)    


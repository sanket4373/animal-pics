from minio import Minio
import io
from app.config import settings

#minio client instance
def get_minio_client():
     """Create and return a MinIO client instance."""
     return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

def ensure_bucket_exists(minio_client):
    """Check if bucket exists and create it if it doesn't."""
    if not minio_client.bucket_exists(settings.minio_bucket):
        minio_client.make_bucket(settings.minio_bucket)



def put_image(minio_client, object_key, data):
    """
    Upload image bytes to MinIO.
    
    Args:
        minio_client: MinIO client instance
        object_key: Storage key like "cat/abc123.jpg"
        data: Raw image bytes
    """
    # Wrap bytes in BytesIO for MinIO SDK
    data_stream = io.BytesIO(data)
    
    minio_client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_key,
        data=data_stream,
        length=len(data),
        content_type="image/jpeg",
    )


def get_image(minio_client, object_key):
    """
    Retrieve image bytes from MinIO.
    
    Args:
        minio_client: MinIO client instance
        object_key: Storage key like "cat/abc123.jpg"
        
    Returns:
        bytes: Raw image data
    """
    response = minio_client.get_object(
        bucket_name=settings.minio_bucket,
        object_name=object_key,
    )
    
    # Read the data
    data = response.read()
    
    # Clean up the connection
    response.close()
    response.release_conn()
    
    return data
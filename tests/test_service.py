import pytest
import asyncio
import respx
import httpx
from app import service
from app.models import AnimalPicture


@pytest.mark.asyncio
@respx.mock
async def test_fetch_and_save_stores_correct_count(db_session, mock_minio):
    """Test that fetch_and_save stores the correct number of images."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image_bytes")
    )
    
    # Call the service function
    records = await service.fetch_and_save("dog", 3, db_session, None)
    
    # Assert the function returned 3 records
    assert len(records) == 3
    
    # Verify all records have the correct animal type
    for record in records:
        assert record.animal_type == "dog"
        assert record.id is not None  # ID should be populated after commit
        assert record.minio_key.startswith("dog/")
        assert record.image_url == "https://place.dog/400/400"
    
    # Query the database directly to verify persistence
    count = db_session.query(AnimalPicture)\
        .filter(AnimalPicture.animal_type == "dog")\
        .count()
    assert count == 3


@pytest.mark.asyncio
@respx.mock
async def test_fetch_and_save_stores_in_minio(db_session, mock_minio):
    """Test that fetch_and_save stores images in MinIO."""
    # Mock the external API call
    respx.get("https://placebear.com/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_bear_image_bytes")
    )
    
    # Call the service function
    records = await service.fetch_and_save("bear", 2, db_session, None)
    
    # Verify images were stored in mock MinIO
    assert len(mock_minio) == 2  # mock_minio is the in-memory store dict
    
    # Verify the keys match what's in the database
    for record in records:
        assert record.minio_key in mock_minio
        assert mock_minio[record.minio_key] == b"fake_bear_image_bytes"


def test_get_last_image_returns_none_when_empty(db_session, mock_minio):
    """Test that get_last_image returns None when no images exist."""
    result = service.get_last_image("bear", db_session, None)
    
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_get_last_image_returns_correct_image(db_session, mock_minio):
    """Test that get_last_image returns the most recent image."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image")
    )
    
    # Store some images
    records = await service.fetch_and_save("dog", 3, db_session, None)
    
    # Get the last image
    result = service.get_last_image("dog", db_session, None)
    
    # Should return a tuple of (image_bytes, record)
    assert result is not None
    image_bytes, record = result
    
    # Verify it's the last record
    assert record.id == records[-1].id
    assert image_bytes == b"fake_dog_image"


@pytest.mark.asyncio
@respx.mock
async def test_get_last_image_filters_by_animal_type(db_session, mock_minio):
    """Test that get_last_image only returns images of the requested type."""
    # Mock both APIs
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image")
    )
    respx.get("https://placebear.com/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_bear_image")
    )
    
    # Store dog images
    await service.fetch_and_save("dog", 2, db_session, None)
    
    # Store bear images
    bear_records = await service.fetch_and_save("bear", 1, db_session, None)
    
    # Get last bear image
    result = service.get_last_image("bear", db_session, None)
    
    assert result is not None
    image_bytes, record = result
    
    # Should be the bear, not the dog
    assert record.animal_type == "bear"
    assert record.id == bear_records[0].id
    assert image_bytes == b"fake_bear_image"


def test_get_history_returns_empty_list(db_session):
    """Test that get_history returns empty list when no images exist."""
    records = service.get_history("dog", db_session, limit=10)
    
    assert records == []


@pytest.mark.asyncio
@respx.mock
async def test_get_history_returns_correct_count(db_session, mock_minio):
    """Test that get_history returns the correct number of records."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image")
    )
    
    # Store 5 images
    await service.fetch_and_save("dog", 5, db_session, None)
    
    # Get history
    records = service.get_history("dog", db_session, limit=10)
    
    assert len(records) == 5
    
    # Verify all are dogs
    for record in records:
        assert record.animal_type == "dog"


@pytest.mark.asyncio
@respx.mock
async def test_get_history_respects_limit(db_session, mock_minio):
    """Test that get_history respects the limit parameter."""
    # Mock the external API call
    respx.get("https://placebear.com/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_bear_image")
    )
    
    # Store 10 images
    await service.fetch_and_save("bear", 10, db_session, None)
    
    # Get history with limit of 3
    records = service.get_history("bear", db_session, limit=3)
    
    assert len(records) == 3


@pytest.mark.asyncio
@respx.mock
async def test_get_history_returns_most_recent_first(db_session, mock_minio):
    """Test that get_history returns records in descending order by date."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image")
    )
    
    # Store images in batches to ensure different timestamps
    first_batch = await service.fetch_and_save("dog", 2, db_session, None)
    
    # Small delay to ensure different timestamps
    await asyncio.sleep(0.01)
    
    second_batch = await service.fetch_and_save("dog", 2, db_session, None)
    
    # Get history
    records = service.get_history("dog", db_session, limit=10)
    
    # Most recent should be first
    assert records[0].id == second_batch[-1].id
    assert records[-1].id == first_batch[0].id
    
    # Verify descending order
    for i in range(len(records) - 1):
        assert records[i].fetched_at >= records[i + 1].fetched_at


@pytest.mark.asyncio
@respx.mock
async def test_get_history_filters_by_animal_type(db_session, mock_minio):
    """Test that get_history only returns images of the requested type."""
    # Mock both APIs
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image")
    )
    respx.get("https://placebear.com/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_bear_image")
    )
    
    # Store both types
    await service.fetch_and_save("dog", 3, db_session, None)
    await service.fetch_and_save("bear", 2, db_session, None)
    
    # Get dog history
    dog_records = service.get_history("dog", db_session, limit=10)
    
    # Should only have dogs
    assert len(dog_records) == 3
    for record in dog_records:
        assert record.animal_type == "dog"
    
    # Get bear history
    bear_records = service.get_history("bear", db_session, limit=10)
    
    # Should only have bears
    assert len(bear_records) == 2
    for record in bear_records:
        assert record.animal_type == "bear"

# Made with Bob

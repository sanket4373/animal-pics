import pytest
import respx
import httpx
from app.schemas import FetchResponse, FetchedImage


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@respx.mock
def test_fetch_animals_success(client, mock_minio):
    """Test successfully fetching and storing animal images."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image_bytes")
    )
    
    # Make the request
    response = client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 1}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["saved"]) == 1
    
    # Validate response structure
    saved_image = data["saved"][0]
    assert "id" in saved_image
    assert saved_image["animal_type"] == "dog"
    assert "image_url" in saved_image
    assert "minio_key" in saved_image
    assert "fetched_at" in saved_image


@respx.mock
def test_fetch_multiple_animals(client, mock_minio):
    """Test fetching multiple animal images at once."""
    # Mock the external API call
    respx.get("https://placebear.com/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_bear_image_bytes")
    )
    
    # Make the request for 3 images
    response = client.post(
        "/animals/fetch",
        json={"animal_type": "bear", "count": 3}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["saved"]) == 3


def test_fetch_invalid_animal_type(client):
    """Test that invalid animal types are rejected by validation."""
    response = client.post(
        "/animals/fetch",
        json={"animal_type": "fish", "count": 1}
    )
    
    # FastAPI validation error
    assert response.status_code == 422


def test_fetch_invalid_count_too_low(client):
    """Test that count below minimum is rejected."""
    response = client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 0}
    )
    
    assert response.status_code == 422


def test_fetch_invalid_count_too_high(client):
    """Test that count above maximum is rejected."""
    response = client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 21}
    )
    
    assert response.status_code == 422


def test_get_last_image_not_found(client, mock_minio):
    """Test getting last image when none exist."""
    response = client.get("/animals/last/bear")
    
    assert response.status_code == 404


@respx.mock
def test_get_last_image_success(client, mock_minio):
    """Test successfully retrieving the last stored image."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image_bytes")
    )
    
    # First, fetch and store an image
    fetch_response = client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 1}
    )
    assert fetch_response.status_code == 200
    
    # Now retrieve the last image
    response = client.get("/animals/last/dog")
    
    # Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"fake_dog_image_bytes"


@respx.mock
def test_get_last_image_returns_most_recent(client, mock_minio):
    """Test that get_last returns the most recently fetched image."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"first_dog_image")
    )
    
    # Fetch first image
    client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 1}
    )
    
    # Mock a different response for the second fetch
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"second_dog_image")
    )
    
    # Fetch second image
    client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 1}
    )
    
    # Get last image - should be the second one
    response = client.get("/animals/last/dog")
    
    assert response.status_code == 200
    assert response.content == b"second_dog_image"


def test_get_history_empty(client):
    """Test getting history when no images exist."""
    response = client.get("/animals/history/dog")
    
    assert response.status_code == 200
    assert response.json() == []


@respx.mock
def test_get_history_with_data(client, mock_minio):
    """Test getting history of fetched images."""
    # Mock the external API call
    respx.get("https://placebear.com/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_bear_image")
    )
    
    # Fetch some images
    client.post(
        "/animals/fetch",
        json={"animal_type": "bear", "count": 3}
    )
    
    # Get history
    response = client.get("/animals/history/bear")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    # Verify structure of history items
    for item in data:
        assert "id" in item
        assert item["animal_type"] == "bear"
        assert "image_url" in item
        assert "minio_key" in item
        assert "fetched_at" in item


@respx.mock
def test_get_history_with_limit(client, mock_minio):
    """Test that history respects the limit parameter."""
    # Mock the external API call
    respx.get("https://place.dog/400/400").mock(
        return_value=httpx.Response(200, content=b"fake_dog_image")
    )
    
    # Fetch 10 images
    client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 10}
    )
    
    # Get history with limit of 5
    response = client.get("/animals/history/dog?limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_root_endpoint_returns_html(client):
    """Test that the root endpoint returns HTML."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Animal Picture Fetcher" in response.content

# Made with Bob

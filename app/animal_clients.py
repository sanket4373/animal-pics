import httpx
import uuid


# Base URLs for animal image APIs
#CAT_BASE_URL = "https://placekitten.com"
DOG_BASE_URL = "https://place.dog"
BEAR_BASE_URL = "https://placebear.com"

# link not working
# async def fetch_cat():
#     """
#     Fetch a random cat image from placekitten.com.
    
#     Returns:
#         tuple: (image_bytes, image_url)
#     """
#     url = f"{CAT_BASE_URL}/400/400"
    
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#         response.raise_for_status()
#         return (response.content, url)


async def fetch_dog():
    """
    Fetch a random dog image from place.dog.
    
    Returns:
        tuple: (image_bytes, image_url)
    """
    url = f"{DOG_BASE_URL}/400/400"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return (response.content, url)


async def fetch_bear():
    """
    Fetch a random bear image from placebear.com.
    
    Returns:
        tuple: (image_bytes, image_url)
    """
    url = f"{BEAR_BASE_URL}/400/400"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return (response.content, url)


async def fetch_animal(animal_type: str):
    """
    Fetch an animal image based on the specified type.
    
    Args:
        animal_type: Type of animal ("dog", or "bear")
        
    Returns:
        tuple: (image_bytes, image_url)
        
    Raises:
        ValueError: If animal_type is not supported
    """
    if animal_type == "dog":
        return await fetch_dog()
    elif animal_type == "bear":
        return await fetch_bear()
    else:
        raise ValueError(f"Unknown animal type: {animal_type}")

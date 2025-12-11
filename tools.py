"""
Tools for external API calls (Perplexity Search API, Google Places API)
"""
from typing import List, Dict, Any, Optional
from perplexity import Perplexity
import googlemaps
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings
from utils import print_error
import time


# Initialize Perplexity client for Search API
perplexity_client = Perplexity(api_key=settings.PERPLEXITY_API_KEY)

# Initialize Google Maps client
gmaps_client = None
if settings.GOOGLE_PLACES_API_KEY:
    gmaps_client = googlemaps.Client(key=settings.GOOGLE_PLACES_API_KEY)


@retry(
    stop=stop_after_attempt(settings.MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def perplexity_search_tool(query: str) -> List[Dict[str, Any]]:
    """
    Search using Perplexity Search API (NOT chat completion)
    
    Args:
        query: Search query string
        
    Returns:
        List of search results with title, url, snippet, etc.
    """
    try:
        # Using Perplexity Search API
        search_response = perplexity_client.search.create(
            query=query,
            max_results=settings.PERPLEXITY_MAX_RESULTS,
            max_tokens_per_page=settings.PERPLEXITY_MAX_TOKENS_PER_PAGE
        )
        
        results = []
        for result in search_response.results:
            results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "date": getattr(result, 'date', None),
                "last_updated": getattr(result, 'last_updated', None)
            })
        
        return results
        
    except Exception as e:
        print_error(f"Perplexity Search API error: {str(e)}", "perplexity_search_tool")
        return []


def perplexity_multi_query_search(queries: List[str]) -> List[Dict[str, Any]]:
    """
    Perform multiple searches using Perplexity Search API
    
    Args:
        queries: List of search query strings
        
    Returns:
        Combined list of search results
    """
    try:
        # Multi-query search as shown in Perplexity documentation
        search_response = perplexity_client.search.create(
            query=queries,  # Pass list of queries
            max_results=settings.PERPLEXITY_MAX_RESULTS
        )
        
        results = []
        for result in search_response.results:
            results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "date": getattr(result, 'date', None),
                "last_updated": getattr(result, 'last_updated', None)
            })
        
        return results
        
    except Exception as e:
        print_error(f"Perplexity Multi-Query Search error: {str(e)}", "perplexity_multi_query_search")
        # Fallback to individual queries
        all_results = []
        for query in queries:
            results = perplexity_search_tool(query)
            all_results.extend(results)
            time.sleep(0.5)  # Rate limiting
        return all_results


@retry(
    stop=stop_after_attempt(settings.MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def google_places_search_tool(
    hotel_name: str,
    location: str
) -> Optional[Dict[str, Any]]:
    """
    Search for hotel using Google Places API to get images and contact
    
    Args:
        hotel_name: Name of the hotel
        location: City/location
        
    Returns:
        Dict with photos and phone number or None
    """
    if not gmaps_client:
        return None
    
    try:
        # Search for the place
        query = f"{hotel_name} {location}"
        places_result = gmaps_client.places(query=query)
        
        if not places_result.get('results'):
            return None
        
        # Get the first result
        place = places_result['results'][0]
        place_id = place.get('place_id')
        
        if not place_id:
            return None
        
        # Get place details
        place_details = gmaps_client.place(
            place_id=place_id,
            fields=['photo', 'formatted_phone_number', 'website', 'rating']
        )
        
        result = place_details.get('result', {})
        
        # Extract photo URLs
        photos = []
        if 'photos' in result:
            for photo in result['photos'][:5]:  # Get up to 5 photos
                photo_reference = photo.get('photo_reference')
                if photo_reference:
                    # Construct photo URL
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_reference}&key={settings.GOOGLE_PLACES_API_KEY}"
                    photos.append(photo_url)
        
        return {
            "place_id": place_id,
            "photos": photos,
            "phone": result.get('formatted_phone_number'),
            "website": result.get('website'),
            "rating": result.get('rating')
        }
        
    except Exception as e:
        print_error(f"Google Places API error: {str(e)}", "google_places_search_tool")
        return None


def deep_search_hotel_details(hotel_url: str) -> Dict[str, Any]:
    """
    Perform a deep search on a specific hotel URL to extract detailed information
    Uses Perplexity Search API to analyze the hotel's website
    
    Args:
        hotel_url: URL of the hotel's website or booking page
        
    Returns:
        Dict with extracted hotel details
    """
    try:
        # Search for specific information about this hotel
        query = f"site:{hotel_url} room types prices amenities contact phone booking"
        
        results = perplexity_search_tool(query)
        
        if not results:
            return {}
        
        # Return the most relevant result
        return {
            "detailed_info": results[0].get('snippet', ''),
            "source": results[0].get('url', hotel_url)
        }
        
    except Exception as e:
        print_error(f"Deep search error: {str(e)}", "deep_search_hotel_details")
        return {}


def validate_hotel_images(image_urls: List[str], hotel_name: str) -> List[str]:
    """
    Validate that image URLs are relevant to the hotel
    This is a simple validation - in production, you might use image recognition
    
    Args:
        image_urls: List of image URLs from Google Places
        hotel_name: Name of the hotel to validate against
        
    Returns:
        List of validated image URLs
    """
    # For now, return all URLs since Google Places should return relevant images
    # In production, you could use OpenAI Vision API or similar to validate
    return [url for url in image_urls if url and url != "Not available"]


def extract_contact_from_snippet(snippet: str) -> Optional[str]:
    """
    Extract phone number from text snippet
    
    Args:
        snippet: Text snippet that might contain a phone number
        
    Returns:
        Extracted phone number or None
    """
    import re
    
    # Indian phone number patterns
    patterns = [
        r'\+91[\s-]?\d{10}',  # +91 with 10 digits
        r'0\d{2,4}[\s-]?\d{6,8}',  # Landline with STD code
        r'\d{10}',  # 10 digit mobile
    ]
    
    for pattern in patterns:
        match = re.search(pattern, snippet)
        if match:
            return match.group(0)
    
    return None

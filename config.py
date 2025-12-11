"""
Configuration management for Hotel Search Agent
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    OPENAI_API_KEY: str
    PERPLEXITY_API_KEY: str
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    
    # Model Configuration
    OPENAI_MODEL: str = "gpt-5-mini"  # Using GPT-5-mini
    # Note: GPT-5-mini only supports default temperature (1.0), so we don't set it
    OPENAI_MAX_TOKENS: int = 4000
    
    # Perplexity Configuration
    PERPLEXITY_MAX_RESULTS: int = 10
    PERPLEXITY_MAX_TOKENS_PER_PAGE: int = 2048
    
    # Application Settings
    APP_NAME: str = "Hotel Search Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    
    # GST Tax Slabs for India (INR per night)
    GST_SLAB_1: dict = {"min": 0, "max": 1000, "rate": 0.0}  # No GST below 1000
    GST_SLAB_2: dict = {"min": 1000, "max": 2500, "rate": 0.12}
    GST_SLAB_3: dict = {"min": 2500, "max": 7500, "rate": 0.12}
    GST_SLAB_4: dict = {"min": 7500, "max": float('inf'), "rate": 0.18}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# CoT Few-Shot Examples for the agents
COT_EXAMPLES = {
    "input_parser": """
    Example Chain of Thought for Input Parser:
    
    User Input: "I need hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed"
    
    Reasoning:
    1. "Okay, I received user input requesting hotel search"
    2. "Let me extract the location: 'Jaipur'"
    3. "Check-in date mentioned: December 16, 2025 -> Converting to YYYY-MM-DD: 2025-12-16"
    4. "Check-out date: December 20, 2025 -> 2025-12-20"
    5. "Number of guests: 2"
    6. "Budget mentioned: 20000 INR"
    7. "Room preference: queen bed"
    8. "All required fields extracted successfully"
    9. "Converting to Pydantic SearchParams structure"
    10. "Validation successful, passing to perplexity_hotel_search_agent"
    """,
    
    "perplexity_search": """
    Example Chain of Thought for Perplexity Search:
    
    Reasoning:
    1. "Received SearchParams for Jaipur hotels"
    2. "Constructing comprehensive search query for Perplexity Search API"
    3. "Query: 'hotels in Jaipur India check-in 2025-12-16 check-out 2025-12-20 budget 20000 INR room types amenities contact booking'"
    4. "Calling Perplexity Search API with max_results=10"
    5. "Received 8 search results from Perplexity"
    6. "Extracting hotel names, prices, amenities from snippets"
    7. "Found booking links in results"
    8. "Some fields missing: images, contact, detailed pricing"
    9. "Flagging for enrichment: needs_image_enrichment=True, needs_contact_enrichment=True"
    """,
    
    "tax_calculator": """
    Example Chain of Thought for Tax Calculator:
    
    Hotel: Vesta International, Room Price: 800 INR per night, 4 nights
    
    Reasoning:
    1. "Received room price: 800 INR per night"
    2. "Duration: 4 nights (Dec 16-20)"
    3. "Base cost: 800 × 4 = 3200 INR"
    4. "Checking GST slab: 800 INR falls in 0-1000 range"
    5. "Wait, this is wrong. Below 1000 has 0% GST? Let me verify..."
    6. "Actually, 1000-2500 range has 12% GST"
    7. "Since 800 < 1000, it's actually 0% GST (exempted)"
    8. "But hotels typically add service charges: ~10%"
    9. "Service charge: 3200 × 0.10 = 320 INR"
    10. "Total cost: 3200 + 0 (GST) + 320 (service) = 3520 INR"
    """,
    
    "validation": """
    Example Chain of Thought for Validation:
    
    Reasoning:
    1. "Checking hotel data completeness"
    2. "Hotel 1: Missing images, contact number"
    3. "Hotel 2: Has booking link, missing images"
    4. "8 out of 10 hotels missing image URLs"
    5. "6 hotels missing contact information"
    6. "All hotels have pricing and amenities"
    7. "Need to invoke google_places_api_agent for enrichment"
    8. "Preparing hotel names for Google Places search"
    """
}

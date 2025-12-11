"""
Pydantic schemas for Hotel Search Agent
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SearchParams(BaseModel):
    """User input parameters for hotel search"""
    location: str = Field(..., description="City or location for hotel search")
    check_in: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    guests: int = Field(..., ge=1, description="Number of guests")
    budget: str = Field(..., description="Total budget (e.g., '20000 INR')")
    room_type: str = Field(..., description="Preferred room type (e.g., 'single', 'double', 'queen')")


class RoomDetails(BaseModel):
    """Details of a room type"""
    type: str = Field(default="Not available")
    price: str = Field(default="Not available")


class HotelDetails(BaseModel):
    """Complete hotel information"""
    name: str
    images: List[str] = Field(default_factory=lambda: ["Not available"])
    amenities: List[str] = Field(default_factory=lambda: ["Not available"])
    room_price: str = Field(default="Not available")
    other_rooms: List[RoomDetails] = Field(default_factory=list)
    government_taxes: str = Field(default="Not available")
    other_charges: str = Field(default="Not available")
    total_cost: str = Field(default="Not available")
    source: str = Field(default="Not available")
    booking_link: str = Field(default="Not available")
    contact: str = Field(default="Not available")


class HotelSearchResponse(BaseModel):
    """Complete search response with all hotels"""
    search_params: SearchParams
    hotels: List[HotelDetails]
    version: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AgentState(BaseModel):
    """State maintained throughout the agent workflow"""
    # User inputs
    user_input: str = ""
    search_params: Optional[SearchParams] = None
    
    # Agent reasoning
    cot_reasoning: List[str] = Field(default_factory=list)
    
    # Search results
    perplexity_results: Optional[dict] = None
    hotel_data: Optional[HotelSearchResponse] = None
    
    # Enrichment data
    images_data: Optional[dict] = None
    contact_data: Optional[dict] = None
    
    # Validation flags
    needs_image_enrichment: bool = False
    needs_contact_enrichment: bool = False
    
    # Final output
    final_response: Optional[HotelSearchResponse] = None
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class PerplexitySearchResult(BaseModel):
    """Structured result from Perplexity Search API"""
    title: str
    url: str
    snippet: str
    date: Optional[str] = None
    last_updated: Optional[str] = None


class GooglePlacesResult(BaseModel):
    """Result from Google Places API"""
    place_id: str
    name: str
    photos: List[str] = Field(default_factory=list)
    formatted_phone_number: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None

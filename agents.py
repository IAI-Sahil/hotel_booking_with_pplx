"""
Agent nodes for the Hotel Search workflow using LangGraph
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
from datetime import datetime

from schemas import (
    AgentState, SearchParams, HotelDetails, 
    HotelSearchResponse, RoomDetails
)
from config import settings, COT_EXAMPLES
from utils import (
    print_cot_reasoning, print_agent_action, print_tool_call,
    print_tool_result, extract_price_from_text, calculate_gst,
    calculate_total_cost, calculate_nights, format_amenities,
    print_error
)
from tools import (
    perplexity_search_tool, google_places_search_tool
)


# Initialize OpenAI LLM with GPT-5-mini
# Note: gpt-5-mini only supports temperature=1.0 (the default)
# We MUST set it explicitly to 1.0, not 0.7 or any other value
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=1.0,  # REQUIRED: GPT-5-mini only supports 1.0
    model_kwargs={
        "max_completion_tokens": settings.OPENAI_MAX_TOKENS
    }
)


def input_parser_agent(state: AgentState) -> Dict[str, Any]:
    """
    Parse user input and extract search parameters with CoT reasoning
    """
    print_agent_action("Input Parser Agent", "Starting to parse user input")
    
    # CoT Reasoning
    cot_steps = [
        "Received user input for hotel search",
        "Analyzing input to extract: location, check-in, check-out, guests, budget, room_type",
        "Using GPT-5-mini to intelligently parse natural language input",
        "Converting extracted data to Pydantic SearchParams structure"
    ]
    
    system_prompt = f"""You are an expert at parsing hotel search queries.
Extract the following information from the user input:
- location: City or place name
- check_in: Check-in date in YYYY-MM-DD format
- check_out: Check-out date in YYYY-MM-DD format  
- guests: Number of guests (integer)
- budget: Budget amount with currency (e.g., "20000 INR")
- room_type: Type of room preferred

{COT_EXAMPLES['input_parser']}

Return ONLY a valid JSON object with these exact fields. No additional text.
"""
    
    try:
        print_cot_reasoning("Step 1", "\n".join(cot_steps), "Input Parser Agent")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.user_input)
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        params_dict = json.loads(content)
        search_params = SearchParams(**params_dict)
        
        reasoning = f"✅ Successfully parsed input:\n"
        reasoning += f"  Location: {search_params.location}\n"
        reasoning += f"  Check-in: {search_params.check_in}\n"
        reasoning += f"  Check-out: {search_params.check_out}\n"
        reasoning += f"  Guests: {search_params.guests}\n"
        reasoning += f"  Budget: {search_params.budget}\n"
        reasoning += f"  Room Type: {search_params.room_type}\n"
        reasoning += "Now passing to perplexity_hotel_search_agent"
        
        print_cot_reasoning("Step 2", reasoning, "Input Parser Agent")
        
        return {
            "search_params": search_params,
            "cot_reasoning": state.cot_reasoning + [reasoning]
        }
        
    except Exception as e:
        print_error(str(e), "Input Parser Agent")
        return {
            "errors": state.errors + [f"Input parsing failed: {str(e)}"]
        }


def perplexity_hotel_search_agent(state: AgentState) -> Dict[str, Any]:
    """
    Search for hotels using Perplexity Search API with CoT reasoning
    """
    print_agent_action("Perplexity Search Agent", "Searching for hotels")
    
    params = state.search_params
    
    # Check if search_params is None (upstream failure)
    if params is None:
        error_msg = "Search parameters are missing. Input parsing may have failed."
        print_error(error_msg, "Perplexity Search Agent")
        return {
            "errors": state.errors + [error_msg]
        }
    
    # CoT Reasoning
    reasoning_steps = [
        f"Received SearchParams: {params.location}, {params.check_in} to {params.check_out}",
        f"Budget: {params.budget}, Guests: {params.guests}, Room: {params.room_type}",
        "Constructing comprehensive search queries for Perplexity Search API",
        "Need to find: hotel names, prices, amenities, booking links, images, contact"
    ]
    
    print_cot_reasoning("Step 1", "\n".join(reasoning_steps), "Perplexity Search Agent")
    
    try:
        # Construct search queries
        queries = [
            f"best hotels in {params.location} India {params.room_type} room price around {params.budget} booking contact",
            f"{params.location} hotels amenities facilities {params.check_in} to {params.check_out}",
            f"affordable hotels {params.location} {params.budget} phone number website booking"
        ]
        
        print_tool_call("perplexity_search_tool", {"queries": queries})
        
        # Use Perplexity Search API
        all_results = []
        for query in queries:
            results = perplexity_search_tool(query)
            all_results.extend(results)
        
        # IMPORTANT: Limit results to prevent prompt overflow
        # Too many results can cause LLM to return empty response
        max_results = 15  # Reduced from 30 to prevent token overflow
        if len(all_results) > max_results:
            all_results = all_results[:max_results]
            print_cot_reasoning(
                "Data Limiting", 
                f"Limiting to {max_results} results to prevent prompt overflow",
                "Perplexity Search Agent"
            )
        
        print_tool_result("Perplexity Search", f"Found {len(all_results)} results")
        
        # Use LLM to structure the results with retry mechanism
        structure_prompt = f"""You MUST extract hotel information from these search results and return ONLY a JSON array.

Search Results:
{json.dumps(all_results, indent=2)}

Extract for each hotel:
- name (string)
- amenities (array of strings)
- room_price (string with price per night, e.g., "5000 INR" or "Not available")
- source (string URL)
- booking_link (string URL or "Not available")

CRITICAL INSTRUCTIONS:
1. Return ONLY a JSON array, nothing else
2. Start your response with [ and end with ]
3. Do NOT include any explanatory text
4. Do NOT wrap the JSON in markdown code blocks
5. Use double quotes for strings
6. If you find fewer than 3 hotels, that's okay, just return what you found

Example format:
[
  {{"name": "Hotel ABC", "amenities": ["WiFi", "Pool"], "room_price": "3000 INR per night", "source": "https://example.com", "booking_link": "https://booking.com"}},
  {{"name": "Hotel XYZ", "amenities": ["AC", "Restaurant"], "room_price": "Not available", "source": "https://example2.com", "booking_link": "Not available"}}
]
"""
        
        messages = [
            SystemMessage(content="You are a hotel data extraction expert. You MUST return ONLY valid JSON arrays, no other text."),
            HumanMessage(content=structure_prompt)
        ]
        
        # Retry mechanism for LLM calls
        max_retries = 3
        hotels_data = None
        
        for attempt in range(max_retries):
            try:
                response = llm.invoke(messages)
                content = response.content.strip()
                
                # Check if response is empty
                if not content:
                    error_msg = f"LLM returned empty response (Attempt {attempt + 1}/{max_retries})"
                    print_error(error_msg, "Perplexity Search Agent")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        raise ValueError("LLM returned empty response after all retries")
                
                # Debug: Print first 200 characters of LLM response
                print_cot_reasoning("LLM Response", f"First 200 chars: {content[:200]}", "Perplexity Search Agent")
                
                # Try to extract JSON from various formats
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Additional cleanup - remove leading/trailing non-JSON characters
                content = content.strip()
                if content.startswith("```"):
                    content = content[3:].strip()
                if content.endswith("```"):
                    content = content[:-3].strip()
                    
                # Try to find JSON array if text contains extra content
                if not content.startswith("["):
                    # Look for [ to start of array
                    start_idx = content.find("[")
                    if start_idx != -1:
                        content = content[start_idx:]
                
                if not content.startswith("["):
                    error_msg = f"LLM did not return a JSON array. Response: '{content[:500]}...'"
                    print_error(error_msg, "Perplexity Search Agent")
                    if attempt < max_retries - 1:
                        print_cot_reasoning("Retry", f"Retrying... (Attempt {attempt + 2}/{max_retries})", "Perplexity Search Agent")
                        import time
                        time.sleep(1)
                        continue
                    else:
                        raise ValueError(error_msg)
                
                # Try to parse JSON
                try:
                    hotels_data = json.loads(content)
                    break  # Success! Exit retry loop
                except json.JSONDecodeError as e:
                    error_msg = f"JSON parsing failed at position {e.pos}. Content: '{content[:500]}...'"
                    print_error(error_msg, "Perplexity Search Agent")
                    if attempt < max_retries - 1:
                        print_cot_reasoning("Retry", f"Retrying... (Attempt {attempt + 2}/{max_retries})", "Perplexity Search Agent")
                        import time
                        time.sleep(1)
                        continue
                    else:
                        raise ValueError(error_msg)
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    print_error(f"Attempt {attempt + 1} failed: {str(e)}", "Perplexity Search Agent")
                    import time
                    time.sleep(1)
                    continue
                else:
                    raise
        
        # If we still don't have hotels_data, create a fallback
        if hotels_data is None or not hotels_data:
            print_error("Failed to extract hotels from LLM. Using fallback extraction.", "Perplexity Search Agent")
            # Simple fallback: create basic hotel entries from search results
            hotels_data = []
            for i, result in enumerate(all_results[:5], 1):  # Only take first 5
                hotels_data.append({
                    "name": result.get("title", f"Hotel {i}"),
                    "amenities": ["Not available"],
                    "room_price": "Not available",
                    "source": result.get("url", "Not available"),
                    "booking_link": "Not available"
                })
        
        # Convert to HotelDetails objects
        hotels = []
        for hotel_data in hotels_data[:10]:  # Limit to top 10
            hotel = HotelDetails(
                name=hotel_data.get("name", "Unknown Hotel"),
                amenities=hotel_data.get("amenities", ["Not available"]),
                room_price=hotel_data.get("room_price", "Not available"),
                source=hotel_data.get("source", "Not available"),
                booking_link=hotel_data.get("booking_link", "Not available"),
                images=["Not available"],
                contact="Not available",
                other_rooms=[],
                government_taxes="Not available",
                other_charges="Not available",
                total_cost="Not available"
            )
            hotels.append(hotel)
        
        reasoning = f"✅ Extracted {len(hotels)} hotels from Perplexity results\n"
        reasoning += "❗ Missing: images, contact, taxes, total_cost\n"
        reasoning += "Next: Calculate taxes and costs"
        
        print_cot_reasoning("Step 2", reasoning, "Perplexity Search Agent")
        
        return {
            "perplexity_results": {"hotels": hotels_data},
            "hotel_data": HotelSearchResponse(
                search_params=params,
                hotels=hotels
            ),
            "cot_reasoning": state.cot_reasoning + [reasoning],
            "needs_image_enrichment": True,
            "needs_contact_enrichment": True
        }
        
    except Exception as e:
        print_error(str(e), "Perplexity Search Agent")
        return {
            "errors": state.errors + [f"Perplexity search failed: {str(e)}"]
        }


def calculate_total_cost_agent(state: AgentState) -> Dict[str, Any]:
    """
    Calculate government taxes and total costs for each hotel with CoT reasoning
    """
    print_agent_action("Cost Calculator Agent", "Calculating taxes and total costs")
    
    params = state.search_params
    
    # Check if search_params is None (upstream failure)
    if params is None:
        error_msg = "Search parameters are missing. Cannot calculate costs."
        print_error(error_msg, "Cost Calculator Agent")
        return {
            "errors": state.errors + [error_msg]
        }
    
    # Check if hotel_data exists (perplexity search failure)
    if state.hotel_data is None:
        error_msg = "Hotel data is missing. Perplexity search may have failed."
        print_error(error_msg, "Cost Calculator Agent")
        return {
            "errors": state.errors + [error_msg]
        }
    
    num_nights = calculate_nights(params.check_in, params.check_out)
    
    reasoning_steps = [
        f"Calculating costs for {num_nights} nights ({params.check_in} to {params.check_out})",
        "For each hotel, will extract price per night",
        "Apply GST based on Indian hotel tax slabs",
        "Add typical service charges (~10%)",
        "Calculate final total cost"
    ]
    
    print_cot_reasoning("Step 1", "\n".join(reasoning_steps), "Cost Calculator Agent")
    
    try:
        hotels = state.hotel_data.hotels
        updated_hotels = []
        
        for i, hotel in enumerate(hotels, 1):
            # Extract price per night
            price_per_night = extract_price_from_text(hotel.room_price)
            
            if price_per_night > 0:
                # Calculate GST
                gst_rate, gst_slab = calculate_gst(price_per_night)
                
                # Calculate total cost
                cost_breakdown = calculate_total_cost(
                    price_per_night,
                    num_nights,
                    gst_rate
                )
                
                hotel_reasoning = f"\nHotel {i}: {hotel.name}\n"
                hotel_reasoning += f"  Price/night: ₹{price_per_night:,.2f}\n"
                hotel_reasoning += f"  GST Slab: {gst_slab}\n"
                hotel_reasoning += f"  GST Amount: {cost_breakdown['gst_amount']}\n"
                hotel_reasoning += f"  Service Charge: {cost_breakdown['service_charge']}\n"
                hotel_reasoning += f"  Total Cost: {cost_breakdown['total_cost']}"
                
                print_cot_reasoning(f"Hotel {i} Calculation", hotel_reasoning, "Cost Calculator")
                
                # Update hotel
                hotel.government_taxes = cost_breakdown['gst_amount']
                hotel.other_charges = cost_breakdown['service_charge']
                hotel.total_cost = cost_breakdown['total_cost']
            else:
                hotel.government_taxes = "Unable to calculate"
                hotel.other_charges = "Unable to calculate"
                hotel.total_cost = "Contact hotel for pricing"
            
            updated_hotels.append(hotel)
        
        final_reasoning = f"✅ Calculated costs for {len(updated_hotels)} hotels\n"
        final_reasoning += "Next: Check if we need image/contact enrichment from Google Places"
        
        print_cot_reasoning("Final", final_reasoning, "Cost Calculator Agent")
        
        state.hotel_data.hotels = updated_hotels
        
        return {
            "hotel_data": state.hotel_data,
            "cot_reasoning": state.cot_reasoning + [final_reasoning]
        }
        
    except Exception as e:
        print_error(str(e), "Cost Calculator Agent")
        return {
            "errors": state.errors + [f"Cost calculation failed: {str(e)}"]
        }


def google_places_enrichment_agent(state: AgentState) -> Dict[str, Any]:
    """
    Enrich hotel data with images and contact from Google Places API (fallback)
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        print_agent_action("Google Places Agent", "Skipped (No API key)")
        return {}
    
    print_agent_action("Google Places Agent", "Enriching with images and contact")
    
    reasoning = "Checking which hotels need image/contact enrichment from Google Places API"
    print_cot_reasoning("Step 1", reasoning, "Google Places Agent")
    
    try:
        hotels = state.hotel_data.hotels
        updated_hotels = []
        
        for i, hotel in enumerate(hotels, 1):
            needs_enrichment = (
                hotel.images == ["Not available"] or 
                hotel.contact == "Not available"
            )
            
            if needs_enrichment:
                print_tool_call("google_places_search_tool", {"hotel_name": hotel.name})
                
                place_data = google_places_search_tool(
                    hotel.name,
                    state.search_params.location
                )
                
                if place_data:
                    if hotel.images == ["Not available"] and place_data.get("photos"):
                        hotel.images = place_data["photos"]
                        
                    if hotel.contact == "Not available" and place_data.get("phone"):
                        hotel.contact = place_data["phone"]
                    
                    print_tool_result(
                        "Google Places",
                        f"Enriched {hotel.name}: {len(place_data.get('photos', []))} images, contact: {place_data.get('phone', 'N/A')}"
                    )
            
            updated_hotels.append(hotel)
        
        state.hotel_data.hotels = updated_hotels
        
        final_reasoning = f"✅ Enrichment complete for {len(updated_hotels)} hotels\n"
        final_reasoning += "Ready to generate final response"
        
        print_cot_reasoning("Final", final_reasoning, "Google Places Agent")
        
        return {
            "hotel_data": state.hotel_data,
            "cot_reasoning": state.cot_reasoning + [final_reasoning]
        }
        
    except Exception as e:
        print_error(str(e), "Google Places Agent")
        # Non-critical error, continue
        return {
            "cot_reasoning": state.cot_reasoning + [f"Google Places enrichment failed (non-critical): {str(e)}"]
        }


def final_json_response_agent(state: AgentState) -> Dict[str, Any]:
    """
    Generate final structured JSON response
    """
    print_agent_action("Final Response Agent", "Generating final JSON response")
    
    reasoning = "Validating all hotel data fields are complete\n"
    reasoning += "Formatting amenities, prices, and contact information\n"
    reasoning += "Preparing final HotelSearchResponse"
    
    print_cot_reasoning("Final Validation", reasoning, "Final Response Agent")
    
    try:
        # Format amenities for all hotels
        for hotel in state.hotel_data.hotels:
            hotel.amenities = format_amenities(hotel.amenities)
        
        state.hotel_data.timestamp = datetime.now().isoformat()
        
        final_reasoning = f"✅ Final response ready with {len(state.hotel_data.hotels)} hotels\n"
        final_reasoning += "All required fields populated or marked as 'Not available'"
        
        print_cot_reasoning("Complete", final_reasoning, "Final Response Agent")
        
        return {
            "final_response": state.hotel_data,
            "cot_reasoning": state.cot_reasoning + [final_reasoning]
        }
        
    except Exception as e:
        print_error(str(e), "Final Response Agent")
        return {
            "errors": state.errors + [f"Final response generation failed: {str(e)}"]
        }

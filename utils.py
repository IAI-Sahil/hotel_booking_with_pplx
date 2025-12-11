"""
Utility functions for Hotel Search Agent
"""
from typing import Dict, Any, List
from datetime import datetime
import re
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
import json

console = Console()


def print_cot_reasoning(step: str, reasoning: str, agent_name: str = "Agent"):
    """
    Pretty print Chain of Thought reasoning
    
    Args:
        step: Current step number or name
        reasoning: The reasoning text
        agent_name: Name of the agent
    """
    console.print(f"\n[bold cyan]{'=' * 80}[/bold cyan]")
    console.print(f"[bold yellow]🤔 {agent_name} - {step}[/bold yellow]")
    console.print(f"[bold cyan]{'=' * 80}[/bold cyan]")
    console.print(Panel(reasoning, border_style="cyan", expand=False))


def print_agent_action(agent_name: str, action: str):
    """Print agent action"""
    console.print(f"\n[bold green]🤖 {agent_name}:[/bold green] {action}")


def print_tool_call(tool_name: str, params: Dict[str, Any]):
    """Print tool call with parameters"""
    console.print(f"\n[bold magenta]🔧 Tool Call: {tool_name}[/bold magenta]")
    console.print(Panel(
        Syntax(json.dumps(params, indent=2), "json", theme="monokai"),
        border_style="magenta"
    ))


def print_tool_result(tool_name: str, result_summary: str):
    """Print tool result summary"""
    console.print(f"[bold blue]✅ {tool_name} Result:[/bold blue] {result_summary}")


def print_state_transition(from_node: str, to_node: str):
    """Print state transition in the graph"""
    console.print(f"\n[dim]📍 Transition: {from_node} → {to_node}[/dim]")


def print_final_response(response: Dict[str, Any]):
    """Pretty print final response"""
    console.print(f"\n[bold green]{'=' * 80}[/bold green]")
    console.print(f"[bold green]🎉 FINAL RESPONSE[/bold green]")
    console.print(f"[bold green]{'=' * 80}[/bold green]")
    
    # Create a tree structure
    tree = Tree("🏨 Hotel Search Results")
    
    search_params = response.get("search_params", {})
    params_node = tree.add("📋 Search Parameters")
    params_node.add(f"Location: {search_params.get('location')}")
    params_node.add(f"Check-in: {search_params.get('check_in')}")
    params_node.add(f"Check-out: {search_params.get('check_out')}")
    params_node.add(f"Guests: {search_params.get('guests')}")
    params_node.add(f"Budget: {search_params.get('budget')}")
    
    hotels = response.get("hotels", [])
    hotels_node = tree.add(f"🏨 Found {len(hotels)} Hotels")
    
    for i, hotel in enumerate(hotels, 1):
        hotel_node = hotels_node.add(f"Hotel {i}: {hotel.get('name')}")
        hotel_node.add(f"💰 Price: {hotel.get('room_price')}")
        hotel_node.add(f"💳 Total Cost: {hotel.get('total_cost')}")
        hotel_node.add(f"📞 Contact: {hotel.get('contact')}")
        hotel_node.add(f"🔗 Booking: {hotel.get('booking_link')}")
        
        amenities = hotel.get('amenities', [])
        if amenities and amenities[0] != "Not available":
            amenities_str = ", ".join(amenities[:3])
            hotel_node.add(f"✨ Amenities: {amenities_str}...")
    
    console.print(tree)


def extract_price_from_text(text: str) -> float:
    """
    Extract numeric price from text
    
    Args:
        text: Text containing price information
        
    Returns:
        float: Extracted price or 0.0 if not found
    """
    # Look for patterns like "1500 INR", "₹2000", "$100"
    patterns = [
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'INR\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*INR',
        r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return 0.0


def calculate_gst(price_per_night: float) -> tuple[float, str]:
    """
    Calculate GST based on Indian hotel room tariff slabs
    
    Args:
        price_per_night: Room price per night in INR
        
    Returns:
        tuple: (GST rate as decimal, GST slab description)
    """
    if price_per_night < 1000:
        return 0.0, "Below ₹1000 (0% GST)"
    elif 1000 <= price_per_night < 2500:
        return 0.12, "₹1000-2500 (12% GST)"
    elif 2500 <= price_per_night < 7500:
        return 0.12, "₹2500-7500 (12% GST)"
    else:
        return 0.18, "Above ₹7500 (18% GST)"


def calculate_total_cost(
    room_price_per_night: float,
    num_nights: int,
    gst_rate: float,
    service_charge_rate: float = 0.10
) -> Dict[str, Any]:
    """
    Calculate total cost with breakdown
    
    Args:
        room_price_per_night: Price per night
        num_nights: Number of nights
        gst_rate: GST rate (e.g., 0.12 for 12%)
        service_charge_rate: Service charge rate (default 10%)
        
    Returns:
        dict: Cost breakdown
    """
    base_cost = room_price_per_night * num_nights
    gst_amount = base_cost * gst_rate
    service_charge = base_cost * service_charge_rate
    total = base_cost + gst_amount + service_charge
    
    return {
        "base_cost": f"₹{base_cost:,.2f}",
        "gst_amount": f"₹{gst_amount:,.2f} ({gst_rate*100}%)",
        "service_charge": f"₹{service_charge:,.2f} ({service_charge_rate*100}%)",
        "total_cost": f"₹{total:,.2f}",
        "per_night": f"₹{room_price_per_night:,.2f}",
        "num_nights": num_nights
    }


def calculate_nights(check_in: str, check_out: str) -> int:
    """
    Calculate number of nights between check-in and check-out
    
    Args:
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        
    Returns:
        int: Number of nights
    """
    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        delta = check_out_date - check_in_date
        return max(1, delta.days)
    except Exception:
        return 1


def validate_image_urls(urls: List[str], hotel_name: str) -> List[str]:
    """
    Validate image URLs (basic validation)
    
    Args:
        urls: List of image URLs
        hotel_name: Hotel name for context validation
        
    Returns:
        List[str]: Validated URLs
    """
    valid_urls = []
    
    for url in urls:
        if url == "Not available":
            continue
            
        # Basic URL validation
        if url.startswith(('http://', 'https://')):
            # Check if it looks like an image URL
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', 'photo', 'image']):
                valid_urls.append(url)
    
    return valid_urls if valid_urls else ["Not available"]


def format_amenities(amenities: List[str]) -> List[str]:
    """
    Format and clean amenities list
    
    Args:
        amenities: Raw amenities list
        
    Returns:
        List[str]: Formatted amenities
    """
    if not amenities or amenities[0] == "Not available":
        return ["Not available"]
    
    # Clean and deduplicate
    cleaned = []
    seen = set()
    
    for amenity in amenities:
        # Clean the amenity string
        cleaned_amenity = amenity.strip().title()
        
        # Avoid duplicates
        if cleaned_amenity.lower() not in seen and cleaned_amenity:
            seen.add(cleaned_amenity.lower())
            cleaned.append(cleaned_amenity)
    
    return cleaned if cleaned else ["Not available"]


def print_error(error_msg: str, context: str = ""):
    """Print error message"""
    console.print(f"\n[bold red]❌ ERROR{f' ({context})' if context else ''}:[/bold red] {error_msg}")

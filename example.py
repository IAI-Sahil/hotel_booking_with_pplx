"""
Example usage of the Hotel Search Agent
Demonstrates programmatic usage of the agentic workflow
"""
import json
from schemas import AgentState
from graph import create_hotel_search_graph
from utils import console


def example_1_basic_search():
    """
    Example 1: Basic hotel search in Jaipur
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 1: Basic Hotel Search[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    query = "Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed"
    
    # Create graph
    graph = create_hotel_search_graph()
    
    # Run workflow
    initial_state = AgentState(user_input=query)
    result = graph.invoke(initial_state)
    
    # Display results
    if result.get("final_response"):
        hotels = result["final_response"].hotels
        console.print(f"[green]✅ Found {len(hotels)} hotels[/green]\n")
        
        for i, hotel in enumerate(hotels[:3], 1):
            console.print(f"[bold]{i}. {hotel.name}[/bold]")
            console.print(f"   Price: {hotel.room_price}")
            console.print(f"   Total: {hotel.total_cost}")
            console.print(f"   Contact: {hotel.contact}\n")


def example_2_luxury_search():
    """
    Example 2: Luxury hotel search
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 2: Luxury Hotel Search[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    query = "I need luxury hotels in Mumbai for New Year's Eve, December 31, 2025 to January 2, 2026, for 2 guests, budget 50000 INR, suite with sea view"
    
    graph = create_hotel_search_graph()
    initial_state = AgentState(user_input=query)
    result = graph.invoke(initial_state)
    
    if result.get("final_response"):
        console.print("[green]✅ Search completed successfully[/green]")
        console.print(f"Total reasoning steps: {len(result.get('cot_reasoning', []))}")


def example_3_budget_search():
    """
    Example 3: Budget hotel search
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 3: Budget Hotel Search[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    query = "Find budget hotels in Goa for a week from January 10 to 17, 2026, 4 guests, total budget 30000 INR, need 2 double rooms"
    
    graph = create_hotel_search_graph()
    initial_state = AgentState(user_input=query)
    result = graph.invoke(initial_state)
    
    if result.get("final_response"):
        # Save to file
        with open("hotel_search_result.json", "w") as f:
            json.dump(result["final_response"].model_dump(), f, indent=2)
        console.print("[green]✅ Results saved to hotel_search_result.json[/green]")


def example_4_custom_state():
    """
    Example 4: Using custom state with pre-filled data
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 4: Custom State[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    from schemas import SearchParams
    
    # Pre-fill search parameters
    search_params = SearchParams(
        location="Bangalore",
        check_in="2026-02-14",
        check_out="2026-02-16",
        guests=2,
        budget="15000 INR",
        room_type="romantic suite"
    )
    
    # Create state with pre-filled params
    initial_state = AgentState(
        user_input="Valentine's Day hotel in Bangalore",
        search_params=search_params
    )
    
    graph = create_hotel_search_graph()
    result = graph.invoke(initial_state)
    
    if result.get("final_response"):
        console.print("[green]✅ Search with custom parameters completed[/green]")


def example_5_error_handling():
    """
    Example 5: Error handling
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 5: Error Handling[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    # Invalid query (missing required information)
    query = "Find me hotels"
    
    graph = create_hotel_search_graph()
    initial_state = AgentState(user_input=query)
    
    try:
        result = graph.invoke(initial_state)
        
        if result.get("errors"):
            console.print("[red]❌ Errors encountered:[/red]")
            for error in result["errors"]:
                console.print(f"   • {error}")
        else:
            console.print("[yellow]⚠️  Incomplete query handled gracefully[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Exception: {str(e)}[/red]")


def example_6_reasoning_inspection():
    """
    Example 6: Inspecting Chain of Thought reasoning
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 6: CoT Reasoning Inspection[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    query = "Budget hotels in Delhi for 3 nights, January 20-23, 2026, 1 guest, 10000 INR budget"
    
    graph = create_hotel_search_graph()
    initial_state = AgentState(user_input=query)
    result = graph.invoke(initial_state)
    
    # Inspect reasoning steps
    if result.get("cot_reasoning"):
        console.print(f"\n[bold]Chain of Thought Steps: {len(result['cot_reasoning'])}[/bold]\n")
        
        for i, reasoning in enumerate(result["cot_reasoning"], 1):
            console.print(f"[yellow]Step {i}:[/yellow]")
            console.print(f"{reasoning}\n")


def example_7_compare_multiple_cities():
    """
    Example 7: Compare hotels in multiple cities
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]Example 7: Multi-City Comparison[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    cities = ["Jaipur", "Udaipur", "Jodhpur"]
    all_results = {}
    
    graph = create_hotel_search_graph()
    
    for city in cities:
        query = f"Hotels in {city} from March 1 to March 3, 2026, 2 guests, 15000 INR budget"
        
        console.print(f"\n[cyan]Searching {city}...[/cyan]")
        initial_state = AgentState(user_input=query)
        result = graph.invoke(initial_state)
        
        if result.get("final_response"):
            all_results[city] = len(result["final_response"].hotels)
    
    # Compare results
    console.print("\n[bold]Comparison:[/bold]")
    for city, count in all_results.items():
        console.print(f"  {city}: {count} hotels found")


def main():
    """Run all examples"""
    console.print("\n[bold green]🏨 Hotel Search Agent - Example Usage[/bold green]\n")
    
    examples = [
        ("Basic Search", example_1_basic_search),
        ("Luxury Search", example_2_luxury_search),
        ("Budget Search", example_3_budget_search),
        ("Custom State", example_4_custom_state),
        ("Error Handling", example_5_error_handling),
        ("CoT Reasoning", example_6_reasoning_inspection),
        ("Multi-City", example_7_compare_multiple_cities),
    ]
    
    console.print("[bold]Available Examples:[/bold]")
    for i, (name, _) in enumerate(examples, 1):
        console.print(f"  {i}. {name}")
    
    console.print("\n[dim]You can run specific examples by calling them directly[/dim]")
    console.print("[dim]Example: python example_usage.py[/dim]\n")
    
    # Run a few examples
    try:
        example_1_basic_search()
        # example_2_luxury_search()
        # example_6_reasoning_inspection()
    except KeyboardInterrupt:
        console.print("\n[yellow]Examples interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error running examples: {str(e)}[/red]")


if __name__ == "__main__":
    main()

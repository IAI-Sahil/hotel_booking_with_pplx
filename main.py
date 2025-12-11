"""
Main entry point for Hotel Search Agent
Run the agentic workflow with terminal output
"""
import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from schemas import AgentState
from graph import create_hotel_search_graph, print_workflow_diagram
from config import settings
from utils import print_final_response, console


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║              🏨 HOTEL SEARCH AGENT - Agentic AI v1.0                 ║
    ║                                                                       ║
    ║  Powered by: GPT-5-mini + Perplexity Search API + LangGraph          ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_config_info():
    """Print configuration information"""
    config_info = f"""
    [bold]Configuration:[/bold]
    • LLM Model: {settings.OPENAI_MODEL}
    • Temperature: Default (1.0) - GPT-5-mini only
    • Perplexity Search API: ✅ Enabled
    • Google Places API: {'✅ Enabled' if settings.GOOGLE_PLACES_API_KEY else '❌ Disabled (Fallback unavailable)'}
    • Max Retries: {settings.MAX_RETRIES}
    """
    console.print(Panel(config_info, border_style="green", title="Settings"))


def get_user_input() -> str:
    """Get user input with a nice prompt"""
    console.print("\n[bold yellow]📝 Enter your hotel search query:[/bold yellow]")
    console.print("[dim]Example: Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed[/dim]\n")
    
    query = Prompt.ask("[cyan]Your query")
    return query


def run_hotel_search(query: str):
    """
    Run the hotel search workflow
    
    Args:
        query: Natural language hotel search query
    """
    try:
        console.print("\n" + "="*80)
        console.print("[bold magenta]🚀 INITIATING HOTEL SEARCH WORKFLOW[/bold magenta]")
        console.print("="*80 + "\n")
        
        # Create the graph
        console.print("[bold cyan]📊 Building LangGraph workflow...[/bold cyan]")
        hotel_search_graph = create_hotel_search_graph()
        console.print("[green]✅ Graph created successfully![/green]\n")
        
        # Initialize state
        console.print("[bold cyan]🎯 Initializing agent state...[/bold cyan]")
        initial_state = AgentState(user_input=query)
        console.print("[green]✅ State initialized![/green]\n")
        
        # Run the workflow
        console.print("[bold yellow]🤖 STARTING AGENTIC WORKFLOW WITH CoT REASONING[/bold yellow]\n")
        
        final_state = hotel_search_graph.invoke(initial_state)
        
        # Check for errors
        if final_state.get("errors"):
            console.print("\n[bold red]❌ WORKFLOW FAILED[/bold red]")
            for error in final_state["errors"]:
                console.print(f"  • [red]{error}[/red]")
            return
        
        # Get and display final response
        final_response = final_state.get("final_response")
        
        if final_response:
            console.print("\n" + "="*80)
            print_final_response(final_response.model_dump())
            console.print("="*80 + "\n")
            
            # Save JSON output to file
            import os
            from datetime import datetime
            
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            location = final_response.search_params.location.replace(" ", "_")
            filename = f"hotel_search_{location}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Save JSON to file
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(final_response.model_dump(), f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]💾 Results saved to:[/green] [cyan]{filepath}[/cyan]\n")
            
            # Print summary
            hotels_found = len(final_response.hotels)
            console.print(f"[bold green]✅ SUCCESS![/bold green] Found {hotels_found} hotels")
            console.print(f"[dim]Reasoning steps executed: {len(final_state.get('cot_reasoning', []))}[/dim]")
        else:
            console.print("\n[bold red]❌ Failed to generate final response[/bold red]")
            
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Search cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {str(e)}")
        import traceback
        if settings.DEBUG:
            console.print("\n[dim]" + traceback.format_exc() + "[/dim]")


def interactive_mode():
    """Run in interactive mode"""
    print_banner()
    print_config_info()
    print_workflow_diagram()
    
    console.print("\n[bold green]🎮 INTERACTIVE MODE[/bold green]")
    console.print("[dim]Type 'quit' or 'exit' to stop[/dim]\n")
    
    while True:
        try:
            query = get_user_input()
            
            if query.lower() in ['quit', 'exit', 'q']:
                console.print("\n[yellow]👋 Goodbye![/yellow]\n")
                break
            
            if not query.strip():
                console.print("[red]Please enter a valid query[/red]\n")
                continue
            
            # Run the search
            run_hotel_search(query)
            
            # Ask if user wants to search again
            console.print("\n")
            continue_search = Prompt.ask(
                "[cyan]Search again?[/cyan]",
                choices=["y", "n"],
                default="y"
            )
            
            if continue_search.lower() != 'y':
                console.print("\n[yellow]👋 Goodbye![/yellow]\n")
                break
                
        except KeyboardInterrupt:
            console.print("\n\n[yellow]👋 Goodbye![/yellow]\n")
            break


def single_search_mode(query: str):
    """Run a single search with the given query"""
    print_banner()
    print_config_info()
    run_hotel_search(query)


def main():
    """Main entry point"""
    import sys
    
    # Check if query is provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        single_search_mode(query)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

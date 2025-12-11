"""
LangGraph workflow orchestration for Hotel Search Agent
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from schemas import AgentState
from agents import (
    input_parser_agent,
    perplexity_hotel_search_agent,
    calculate_total_cost_agent,
    google_places_enrichment_agent,
    final_json_response_agent
)
from utils import print_state_transition, console


def should_enrich_data(state: AgentState) -> str:
    """
    Conditional edge to decide if we need Google Places enrichment
    """
    if state.errors:
        return "end"
    
    # Check if we have Google Places API key and need enrichment
    if state.needs_image_enrichment or state.needs_contact_enrichment:
        print_state_transition("calculate_costs", "google_places_enrichment")
        return "enrich"
    else:
        print_state_transition("calculate_costs", "format_response")
        return "final"


def should_continue_after_enrichment(state: AgentState) -> str:
    """
    Always continue to final response after enrichment
    """
    print_state_transition("google_places_enrichment", "format_response")
    return "final"


def has_errors(state: AgentState) -> str:
    """
    Check if there are any errors in the state
    """
    if state.errors:
        console.print(f"\n[bold red]❌ Workflow stopped due to errors:[/bold red]")
        for error in state.errors:
            console.print(f"  • {error}")
        return "end"
    return "continue"


def create_hotel_search_graph() -> CompiledGraph:
    """
    Create the LangGraph workflow for hotel search
    
    Workflow:
    1. input_parser_agent: Parse user input → SearchParams
    2. perplexity_hotel_search_agent: Search hotels using Perplexity Search API
    3. calculate_total_cost_agent: Calculate GST and total costs
    4. google_places_enrichment_agent (conditional): Enrich with images/contact
    5. final_json_response_agent: Generate final structured response
    """
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (agents)
    workflow.add_node("input_parser", input_parser_agent)
    workflow.add_node("perplexity_search", perplexity_hotel_search_agent)
    workflow.add_node("calculate_costs", calculate_total_cost_agent)
    workflow.add_node("google_places_enrichment", google_places_enrichment_agent)
    workflow.add_node("format_response", final_json_response_agent)
    
    # Set entry point
    workflow.set_entry_point("input_parser")
    
    # Add edges
    workflow.add_edge("input_parser", "perplexity_search")
    workflow.add_edge("perplexity_search", "calculate_costs")
    
    # Conditional edge: enrich with Google Places or go to final response
    workflow.add_conditional_edges(
        "calculate_costs",
        should_enrich_data,
        {
            "enrich": "google_places_enrichment",
            "final": "format_response",
            "end": END
        }
    )
    
    # After enrichment, always go to final response
    workflow.add_edge("google_places_enrichment", "format_response")
    
    # Final response ends the workflow
    workflow.add_edge("format_response", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


def visualize_graph(app: CompiledGraph, output_path: str = "hotel_search_graph.png"):
    """
    Visualize the graph structure
    
    Args:
        app: Compiled LangGraph
        output_path: Path to save the visualization
    """
    try:
        # This requires pygraphviz or similar
        from IPython.display import Image, display
        graph_image = app.get_graph().draw_png()
        
        with open(output_path, 'wb') as f:
            f.write(graph_image)
        
        console.print(f"[green]✅ Graph visualization saved to {output_path}[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not generate graph visualization: {e}[/yellow]")
        console.print("[dim]Install pygraphviz for graph visualization: pip install pygraphviz[/dim]")


def print_workflow_diagram():
    """
    Print a text-based workflow diagram
    """
    diagram = """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                    HOTEL SEARCH AGENT WORKFLOW                        ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    
                               [START]
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │   Input Parser Agent        │
                    │   • Parse user input        │
                    │   • Extract search params   │
                    │   • CoT reasoning           │
                    └──────────────┬──────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │ Perplexity Search Agent     │
                    │   • Search hotels via API   │
                    │   • Extract hotel data      │
                    │   • Structure results       │
                    └──────────────┬──────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │ Cost Calculator Agent       │
                    │   • Calculate GST           │
                    │   • Add service charges     │
                    │   • Compute total costs     │
                    └──────────────┬──────────────┘
                                  │
                        ┌─────────┴─────────┐
                        │  Need enrichment? │
                        └─────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                  Yes│                          │No
                    │                           │
                    ▼                           ▼
      ┌──────────────────────────┐    ┌────────────────────┐
      │ Google Places Agent      │    │                    │
      │   • Get hotel images     │    │   (Skip)           │
      │   • Get contact info     │    │                    │
      │   • Validate data        │    │                    │
      └──────────────┬───────────┘    └─────────┬──────────┘
                     │                           │
                     └───────────┬───────────────┘
                                 ▼
                    ┌─────────────────────────────┐
                    │ Final Response Agent        │
                    │   • Validate all fields     │
                    │   • Format amenities        │
                    │   • Generate JSON response  │
                    └──────────────┬──────────────┘
                                  │
                                  ▼
                               [END]
                    
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  Chain of Thought (CoT) reasoning is applied at each agent step      ║
    ║  All intermediate reasoning is logged to the terminal                 ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
    
    console.print(diagram, style="cyan")


if __name__ == "__main__":
    # Test the graph creation
    print_workflow_diagram()
    app = create_hotel_search_graph()
    console.print("\n[green]✅ Hotel Search Graph created successfully![/green]")

"""
FastAPI application for Hotel Search Agent
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from datetime import datetime

from schemas import AgentState, HotelSearchResponse
from graph import create_hotel_search_graph, print_workflow_diagram
from config import settings
from utils import console, print_final_response


# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic AI Hotel Search with CoT reasoning using GPT-5-mini and Perplexity Search API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the graph once at startup
hotel_search_graph = None


class SearchRequest(BaseModel):
    """Request model for hotel search"""
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed"
            }
        }


class SearchResponse(BaseModel):
    """Response model for hotel search"""
    success: bool
    data: Optional[HotelSearchResponse] = None
    error: Optional[str] = None
    reasoning_steps: list = []
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Initialize the graph on startup"""
    global hotel_search_graph
    
    console.print("\n[bold cyan]🚀 Starting Hotel Search Agent API[/bold cyan]")
    console.print(f"[dim]Model: {settings.OPENAI_MODEL}[/dim]")
    console.print(f"[dim]Perplexity Search API: Enabled[/dim]")
    console.print(f"[dim]Google Places API: {'Enabled' if settings.GOOGLE_PLACES_API_KEY else 'Disabled (Fallback unavailable)'}[/dim]\n")
    
    # Print workflow diagram
    print_workflow_diagram()
    
    # Create the graph
    hotel_search_graph = create_hotel_search_graph()
    console.print("[green]✅ LangGraph workflow initialized[/green]\n")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hotel Search Agent API",
        "version": settings.APP_VERSION,
        "model": settings.OPENAI_MODEL,
        "endpoints": {
            "search": "/api/search",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": settings.OPENAI_MODEL,
        "perplexity_api": "connected",
        "google_places_api": "connected" if settings.GOOGLE_PLACES_API_KEY else "not_configured"
    }


@app.post("/api/search", response_model=SearchResponse)
async def search_hotels(request: SearchRequest):
    """
    Search for hotels based on natural language query
    
    This endpoint orchestrates the entire agentic workflow:
    1. Parse user input with CoT reasoning
    2. Search hotels using Perplexity Search API
    3. Calculate costs and taxes
    4. Enrich with Google Places (if available)
    5. Return structured JSON response
    
    All reasoning steps are printed to the terminal for observability.
    """
    try:
        console.print("\n" + "="*80)
        console.print("[bold magenta]🔍 NEW SEARCH REQUEST[/bold magenta]")
        console.print("="*80)
        console.print(f"[bold]Query:[/bold] {request.query}\n")
        
        # Initialize state
        initial_state = AgentState(user_input=request.query)
        
        # Run the graph
        console.print("[bold cyan]🤖 Starting Agentic Workflow...[/bold cyan]\n")
        
        final_state = hotel_search_graph.invoke(initial_state)
        
        # Check for errors
        if final_state.get("errors"):
            error_msg = "; ".join(final_state["errors"])
            console.print(f"\n[bold red]❌ Search failed:[/bold red] {error_msg}")
            
            return SearchResponse(
                success=False,
                error=error_msg,
                reasoning_steps=final_state.get("cot_reasoning", []),
                timestamp=datetime.now().isoformat()
            )
        
        # Get final response
        final_response = final_state.get("final_response")
        
        if not final_response:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate hotel search response"
            )
        
        # Print final response to terminal
        print_final_response(final_response.model_dump())
        
        return SearchResponse(
            success=True,
            data=final_response,
            reasoning_steps=final_state.get("cot_reasoning", []),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error:[/bold red] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflow")
async def get_workflow_info():
    """Get information about the workflow"""
    return {
        "workflow": "Hotel Search Agent",
        "agents": [
            {
                "name": "Input Parser Agent",
                "description": "Parses natural language input and extracts search parameters",
                "outputs": "SearchParams"
            },
            {
                "name": "Perplexity Search Agent",
                "description": "Searches for hotels using Perplexity Search API",
                "api": "Perplexity Search API (not chat completion)",
                "outputs": "Hotel data with names, prices, amenities, booking links"
            },
            {
                "name": "Cost Calculator Agent",
                "description": "Calculates GST based on Indian tax slabs and total costs",
                "outputs": "Government taxes, service charges, total cost"
            },
            {
                "name": "Google Places Enrichment Agent",
                "description": "Enriches hotel data with images and contact (fallback)",
                "api": "Google Places API",
                "outputs": "Hotel images and contact numbers"
            },
            {
                "name": "Final Response Agent",
                "description": "Validates and formats final JSON response",
                "outputs": "Complete HotelSearchResponse"
            }
        ],
        "features": [
            "Chain of Thought (CoT) reasoning at each step",
            "Few-shot learning examples",
            "Pydantic schema validation",
            "Terminal observability",
            "Automatic GST calculation for India",
            "Multi-source data enrichment"
        ]
    }


if __name__ == "__main__":
    console.print(f"\n[bold green]Starting FastAPI server on {settings.API_HOST}:{settings.API_PORT}[/bold green]\n")
    
    uvicorn.run(
        "api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

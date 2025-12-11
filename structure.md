# 📁 Project Structure

Complete overview of the Hotel Search Agent architecture and file organization.

## Directory Structure

```
hotel-search-agent/
│
├── main.py                     # CLI entry point with interactive mode
├── api.py                      # FastAPI application
├── graph.py                    # LangGraph workflow definition
├── agents.py                   # All agent implementations
├── tools.py                    # External API integrations
├── schemas.py                  # Pydantic data models
├── config.py                   # Configuration and settings
├── utils.py                    # Utility functions and helpers
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your actual environment variables (gitignored)
├── .gitignore                 # Git ignore rules
│
├── README.md                  # Complete documentation
├── QUICKSTART.md             # Quick start guide
├── PROJECT_STRUCTURE.md      # This file
│
└── example_usage.py          # Usage examples and demonstrations
```

## Core Files

### 1. `main.py` - CLI Interface
**Purpose**: Command-line interface for interactive and single-query searches

**Key Functions**:
- `print_banner()` - Display application banner
- `print_config_info()` - Show configuration
- `get_user_input()` - Get user query
- `run_hotel_search()` - Execute search workflow
- `interactive_mode()` - Interactive query loop
- `single_search_mode()` - One-time search
- `main()` - Entry point

**Usage**:
```bash
python main.py  # Interactive mode
python main.py "search query"  # Single search
```

### 2. `api.py` - FastAPI Application
**Purpose**: RESTful API server for hotel search

**Endpoints**:
- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `POST /api/search` - Search hotels (main endpoint)
- `GET /api/workflow` - Get workflow information

**Models**:
- `SearchRequest` - Request body model
- `SearchResponse` - Response body model

**Usage**:
```bash
python api.py
# Or: uvicorn api:app --reload
```

### 3. `graph.py` - LangGraph Workflow
**Purpose**: Define and orchestrate the agent workflow using LangGraph

**Key Components**:
- `create_hotel_search_graph()` - Build the workflow graph
- `should_enrich_data()` - Conditional routing logic
- `visualize_graph()` - Generate graph visualization
- `print_workflow_diagram()` - ASCII workflow diagram

**Workflow**:
```
Input Parser → Perplexity Search → Cost Calculator → [Conditional] → Final Response
                                                         ↓
                                                 Google Places (optional)
```

### 4. `agents.py` - Agent Implementations
**Purpose**: Implement all agent nodes with CoT reasoning

**Agents**:

#### `input_parser_agent`
- **Input**: Raw user query
- **Process**: Parse with GPT-5-mini
- **Output**: `SearchParams` (Pydantic model)
- **CoT**: Shows extraction reasoning

#### `perplexity_hotel_search_agent`
- **Input**: `SearchParams`
- **Process**: Search via Perplexity Search API
- **Output**: List of `HotelDetails`
- **CoT**: Shows search strategy and results

#### `calculate_total_cost_agent`
- **Input**: Hotels with base prices
- **Process**: Calculate GST, service charges
- **Output**: Updated hotels with total costs
- **CoT**: Shows tax calculation for each hotel

#### `google_places_enrichment_agent`
- **Input**: Hotels needing enrichment
- **Process**: Fetch images and contact
- **Output**: Enriched hotel data
- **CoT**: Shows enrichment results

#### `final_json_response_agent`
- **Input**: Complete hotel data
- **Process**: Validate and format
- **Output**: `HotelSearchResponse`
- **CoT**: Shows final validation

### 5. `tools.py` - External APIs
**Purpose**: Interface with external services

**Tools**:

#### Perplexity Search API
```python
perplexity_search_tool(query: str) -> List[Dict]
```
- Uses Perplexity Search API (NOT chat completion)
- Returns search results with URLs, snippets
- Handles rate limiting and retries

#### Google Places API
```python
google_places_search_tool(hotel_name: str, location: str) -> Dict
```
- Fallback for images and contact
- Returns place photos and phone numbers
- Optional (system works without it)

### 6. `schemas.py` - Data Models
**Purpose**: Define all data structures using Pydantic

**Models**:

#### `SearchParams`
```python
location: str
check_in: str  # YYYY-MM-DD
check_out: str
guests: int
budget: str
room_type: str
```

#### `HotelDetails`
```python
name: str
images: List[str]
amenities: List[str]
room_price: str
other_rooms: List[RoomDetails]
government_taxes: str
other_charges: str
total_cost: str
source: str
booking_link: str
contact: str
```

#### `HotelSearchResponse`
```python
search_params: SearchParams
hotels: List[HotelDetails]
version: int
timestamp: str
```

#### `AgentState`
```python
user_input: str
search_params: Optional[SearchParams]
cot_reasoning: List[str]
perplexity_results: Optional[dict]
hotel_data: Optional[HotelSearchResponse]
# ... more fields
```

### 7. `config.py` - Configuration
**Purpose**: Manage settings and configuration

**Key Components**:
- `Settings` class - Pydantic settings model
- `COT_EXAMPLES` - Few-shot learning examples
- GST tax slab definitions
- API configuration

**Environment Variables**:
```python
OPENAI_API_KEY
PERPLEXITY_API_KEY
GOOGLE_PLACES_API_KEY
OPENAI_MODEL = "gpt-5-mini"
PERPLEXITY_MAX_RESULTS = 10
```

### 8. `utils.py` - Utilities
**Purpose**: Helper functions and display utilities

**Key Functions**:

#### Display Functions
- `print_cot_reasoning()` - Format CoT output
- `print_agent_action()` - Show agent actions
- `print_tool_call()` - Display tool invocations
- `print_final_response()` - Pretty print results

#### Calculation Functions
- `calculate_gst()` - GST based on tariff
- `calculate_total_cost()` - Full cost breakdown
- `calculate_nights()` - Date difference
- `extract_price_from_text()` - Parse prices

#### Validation Functions
- `validate_image_urls()` - Check image URLs
- `format_amenities()` - Clean amenity lists

## Data Flow

```
User Query
    ↓
[Input Parser Agent]
    ↓ SearchParams
[Perplexity Search Agent]
    ↓ Hotel data (basic)
[Cost Calculator Agent]
    ↓ Hotel data + costs
[Conditional: Need enrichment?]
    ↓ Yes                ↓ No
[Google Places Agent]    [Skip]
    ↓                    ↓
[Final Response Agent]
    ↓
Complete JSON Response
```

## State Management

The `AgentState` maintains:
1. **User Input**: Original query
2. **Parsed Params**: Structured search parameters
3. **Search Results**: Raw Perplexity data
4. **Hotel Data**: Structured hotel information
5. **Enrichment Data**: Images and contact
6. **Reasoning**: Chain-of-Thought steps
7. **Errors**: Any errors encountered

## Chain of Thought (CoT)

Each agent adds reasoning steps:

```python
state.cot_reasoning.append("Reasoning text here")
```

Example flow:
```
Step 1: "Parsed location: Jaipur"
Step 2: "Searching Perplexity with query: ..."
Step 3: "Found 8 hotels"
Step 4: "Calculating GST for Hotel 1..."
Step 5: "Total cost: ₹12,200"
Step 6: "Enriching with Google Places..."
Step 7: "Final validation complete"
```

## API Integration

### Perplexity Search API
```python
from perplexity import Perplexity

client = Perplexity(api_key=API_KEY)
search = client.search.create(
    query="hotels in Jaipur",
    max_results=10,
    max_tokens_per_page=2048
)
```

### Google Places API
```python
import googlemaps

client = googlemaps.Client(key=API_KEY)
places = client.places(query="Hotel Name Jaipur")
details = client.place(place_id=place_id)
```

### OpenAI GPT-5-mini
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0.7,
    max_tokens=4000
)
```

## Error Handling

Errors are tracked in `AgentState.errors`:
- Input parsing errors
- API failures
- Validation errors
- Network issues

All agents use try-except blocks and continue gracefully on non-critical errors.

## Extension Points

To add new features:

1. **New Agent**: Add to `agents.py` and wire in `graph.py`
2. **New Tool**: Add to `tools.py` and import in agents
3. **New Schema**: Add to `schemas.py`
4. **New Config**: Add to `config.py` and `.env.example`

## Testing

Run examples:
```bash
python example_usage.py
```

Test individual components:
```python
from graph import create_hotel_search_graph
from schemas import AgentState

graph = create_hotel_search_graph()
state = AgentState(user_input="test query")
result = graph.invoke(state)
```

## Performance Considerations

- **Caching**: Consider caching Perplexity results
- **Parallel Requests**: Agents run sequentially (LangGraph design)
- **Rate Limiting**: Implemented in tools with retry logic
- **Token Usage**: GPT-5-mini is efficient but track usage

## Security

- **API Keys**: Never commit `.env` file
- **Input Validation**: Pydantic handles validation
- **Error Messages**: Don't expose sensitive data
- **Rate Limiting**: Protect against abuse in production

---

This structure enables:
- ✅ Clear separation of concerns
- ✅ Easy testing and debugging
- ✅ Observable workflow execution
- ✅ Extensible architecture
- ✅ Production-ready code

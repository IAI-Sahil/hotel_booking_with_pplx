# 🏨 Hotel Search Agent - Agentic AI Architecture

An advanced agentic AI system for hotel search powered by **GPT-5-mini**, **Perplexity Search API**, and **LangGraph** with Chain-of-Thought (CoT) reasoning.

## 🌟 Features

- **🤖 Agentic Architecture**: Multi-agent system with specialized roles
- **🧠 Chain-of-Thought Reasoning**: CoT prompting with few-shot examples at each step
- **🔍 Perplexity Search API**: Real-time web search for hotel information (NOT chat completion)
- **📊 Structured Output**: Pydantic schema validation throughout
- **💰 Automatic Tax Calculation**: GST calculation based on Indian hotel tax slabs
- **📸 Image Enrichment**: Google Places API fallback for hotel images and contact
- **🖥️ Terminal Observability**: Real-time step-by-step reasoning printed to terminal
- **🚀 FastAPI Backend**: RESTful API with async support
- **🔄 LangGraph Orchestration**: State machine-based workflow management

## 🏗️ Architecture

```
User Input → Input Parser Agent → Perplexity Search Agent → Cost Calculator Agent 
                                                                      ↓
                                                          [Need Enrichment?]
                                                                      ↓
                                                    ┌─────────────────┴─────────────────┐
                                                    ↓                                   ↓
                                        Google Places Agent                        [Skip]
                                                    ↓                                   ↓
                                                    └─────────────────┬─────────────────┘
                                                                      ↓
                                                        Final Response Agent
                                                                      ↓
                                                              JSON Response
```

### Agents

1. **Input Parser Agent**: Parses natural language queries and extracts structured search parameters
2. **Perplexity Search Agent**: Uses Perplexity Search API to find hotels with pricing and amenities
3. **Cost Calculator Agent**: Calculates GST (based on Indian tax slabs) and total costs
4. **Google Places Enrichment Agent**: Fallback for images and contact information
5. **Final Response Agent**: Validates and formats the complete JSON response

## 📋 Requirements

- Python 3.10+
- OpenAI API key (for GPT-5-mini)
- Perplexity API key (for Search API)
- Google Places API key (optional, for image/contact fallback)

## 🚀 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd hotel-search-agent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required API keys:
- `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/)
- `PERPLEXITY_API_KEY`: Get from [Perplexity API](https://www.perplexity.ai/api)
- `GOOGLE_PLACES_API_KEY`: (Optional) Get from [Google Cloud Console](https://console.cloud.google.com/)

## 💻 Usage

### Command Line Interface

**Interactive Mode:**
```bash
pip install -r requirements.txt
```

**Single Query:**
```bash
python main.py "Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed"
```

### FastAPI Server

**Start the server:**
```bash
python api.py
```

Or using uvicorn:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**API Endpoints:**

- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `POST /api/search` - Search for hotels
- `GET /api/workflow` - Get workflow information

**Example API Request:**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed"
  }'
```

## 📊 Output Format

The system returns structured JSON with complete hotel information:

```json
{
  "search_params": {
    "location": "Jaipur",
    "check_in": "2025-12-16",
    "check_out": "2025-12-20",
    "guests": 2,
    "budget": "20000 INR",
    "room_type": "queen bed"
  },
  "hotels": [
    {
      "name": "Hotel Name",
      "images": ["url1", "url2"],
      "amenities": ["WiFi", "Pool", "Gym"],
      "room_price": "₹2,500 per night",
      "other_rooms": [
        {"type": "Deluxe", "price": "₹3,000"}
      ],
      "government_taxes": "₹1,200 (12%)",
      "other_charges": "₹1,000 (10%)",
      "total_cost": "₹12,200",
      "source": "https://...",
      "booking_link": "https://...",
      "contact": "+91-XXXXXXXXXX"
    }
  ]
}
```

## 🧠 Chain of Thought (CoT) Reasoning

The system employs CoT reasoning at each step. Example output:

```
🤖 Input Parser Agent: Starting to parse user input
════════════════════════════════════════════════════════════════════════════════
🤔 Input Parser Agent - Step 1
════════════════════════════════════════════════════════════════════════════════
┌────────────────────────────────────────────────────────────────────────────┐
│ Received user input for hotel search                                       │
│ Analyzing input to extract: location, check-in, check-out, guests, budget │
│ Using GPT-5-mini to intelligently parse natural language input            │
│ Converting extracted data to Pydantic SearchParams structure              │
└────────────────────────────────────────────────────────────────────────────┘
```

## 💳 GST Calculation (India)

The system automatically calculates GST based on Indian hotel tax slabs:

| Room Tariff (per night) | GST Rate |
|-------------------------|----------|
| Below ₹1,000           | 0%       |
| ₹1,000 - ₹2,500        | 12%      |
| ₹2,500 - ₹7,500        | 12%      |
| Above ₹7,500           | 18%      |

Additional charges:
- Service Charge: ~10% (standard)

## 🔧 Configuration

Edit `.env` file to customize:

```bash
# Model settings
OPENAI_MODEL=gpt-5-mini
OPENAI_TEMPERATURE=0.7

# Search settings
PERPLEXITY_MAX_RESULTS=10
PERPLEXITY_MAX_TOKENS_PER_PAGE=2048

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

## 📁 Project Structure

```
hotel-search-agent/
├── main.py                 # CLI entry point
├── api.py                  # FastAPI application
├── graph.py               # LangGraph workflow
├── agents.py              # Agent implementations
├── tools.py               # External API tools
├── schemas.py             # Pydantic models
├── config.py              # Configuration management
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🎯 Key Technologies

- **GPT-5-mini**: Latest OpenAI reasoning model
- **Perplexity Search API**: Real-time web search (not chat completion)
- **LangGraph**: State machine for agent orchestration
- **FastAPI**: Modern async web framework
- **Pydantic**: Data validation and settings management
- **Rich**: Beautiful terminal output

## 🐛 Troubleshooting

**Issue: API key errors**
- Ensure all required API keys are set in `.env`
- Verify keys are valid and have sufficient credits

**Issue: No results from Perplexity**
- Check your Perplexity API key and quota
- Verify internet connection
- Try simplifying the search query

**Issue: Missing images/contact**
- This is expected if Google Places API key is not configured
- The system will mark these fields as "Not available"
- Configure `GOOGLE_PLACES_API_KEY` to enable enrichment

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License

## 🔗 Resources

- [OpenAI GPT-5 Docs](https://platform.openai.com/docs/models/gpt-5-mini)
- [Perplexity Search API Guide](https://perplexity.mintlify.app/guides/search-guide)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ using Agentic AI, Chain-of-Thought Reasoning, and Modern Python**

# 🚀 Quick Start Guide

Get your Hotel Search Agent up and running in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Perplexity API key

## Step 1: Get API Keys

### OpenAI API Key (Required)
1. Visit https://platform.openai.com/
2. Sign up or log in
3. Go to API Keys section
4. Create new key
5. Copy the key (starts with `sk-...`)

### Perplexity API Key (Required)
1. Visit https://www.perplexity.ai/api
2. Sign up for API access
3. Get your API key from dashboard
4. Copy the key

### Google Places API Key (Optional)
1. Visit https://console.cloud.google.com/
2. Create a new project
3. Enable Places API
4. Create credentials (API key)
5. Copy the key

## Step 2: Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd hotel-search-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use any text editor
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-your-key-here
PERPLEXITY_API_KEY=pplx-your-key-here
GOOGLE_PLACES_API_KEY=your-key-here  # Optional
```

## Step 4: Run!

### Interactive CLI Mode
```bash
python main.py
```

Then enter your query when prompted:
```
Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed
```

### Direct Query
```bash
python main.py "Find hotels in Mumbai for January 15-17, 2026, 2 guests, budget 25000 INR"
```

### API Server
```bash
python api.py
```

Then visit http://localhost:8000/docs to see API documentation.

## Step 5: Test API

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find me hotels in Jaipur from December 16 to December 20, 2025 for 2 guests with budget 20000 INR, prefer queen bed"
  }'
```

## Expected Output

You'll see detailed Chain-of-Thought reasoning in the terminal:

```
════════════════════════════════════════════════════════════════════════════════
🤔 Input Parser Agent - Step 1
════════════════════════════════════════════════════════════════════════════════
┌────────────────────────────────────────────────────────────────────────────┐
│ Received user input for hotel search                                       │
│ Analyzing input to extract: location, check-in, check-out, guests, budget │
│ Using GPT-5-mini to intelligently parse natural language input            │
└────────────────────────────────────────────────────────────────────────────┘

🔧 Tool Call: perplexity_search_tool
{
  "query": "hotels in Jaipur India check-in 2025-12-16..."
}

✅ Perplexity Search Result: Found 10 results

... (more reasoning steps) ...

🎉 FINAL RESPONSE
════════════════════════════════════════════════════════════════════════════════
🏨 Hotel Search Results
├── 📋 Search Parameters
│   ├── Location: Jaipur
│   ├── Check-in: 2025-12-16
│   └── Budget: 20000 INR
└── 🏨 Found 8 Hotels
    ├── Hotel 1: Hotel Name
    │   ├── 💰 Price: ₹2,500 per night
    │   ├── 💳 Total Cost: ₹12,200
    │   └── 📞 Contact: +91-XXXXXXXXXX
    └── ...
```

## What's Happening?

The system performs these steps:

1. **Parse Input** - Uses GPT-5-mini to extract search parameters
2. **Search Hotels** - Uses Perplexity Search API to find hotels
3. **Calculate Costs** - Applies Indian GST rates and service charges
4. **Enrich Data** - (If enabled) Gets images and contact from Google Places
5. **Generate Response** - Returns structured JSON with all details

## Troubleshooting

### "API key not found"
- Check your `.env` file has the correct keys
- Make sure you're in the correct directory
- Verify the keys don't have extra spaces

### "No results found"
- Try a more specific query
- Check your internet connection
- Verify your Perplexity API has credits

### "Module not found"
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

### Google Places not working
- This is optional - the system will work without it
- Images and contact will show as "Not available"
- Add the API key to enable this feature

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [example_usage.py](example_usage.py) for programmatic usage
- Explore the API at http://localhost:8000/docs
- Customize settings in `.env`

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Enable DEBUG mode in `.env`
3. Review the troubleshooting section
4. Open an issue on GitHub

---

**Happy Hotel Searching! 🏨✨**

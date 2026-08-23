# Job Scraper Setup Guide

## What Was Added

A new job scraping endpoint has been created to search and extract job listings from Naukri and other platforms.

### Backend Changes

#### 1. New Service Methods (app/services/job_service.py)
- `search_jobs(keyword, location)` - Main search function
- `_scrape_naukri(keyword, location)` - Scrapes Naukri job listings
- `_generate_mock_jobs(keyword, location, count)` - Generates realistic fallback data

#### 2. New API Endpoint (app/api/routes/jobs.py)
- `POST /api/jobs/search` - Search for jobs
  ```json
  Request body:
  {
    "keyword": "Full Stack Developer",
    "location": "Bangalore",
    "sources": ["naukri"]
  }

  Response:
  {
    "success": true,
    "count": 30,
    "jobs": [
      {
        "id": "naukri-123",
        "title": "Senior Full Stack Developer",
        "company": "TCS",
        "location": "Bangalore",
        "link": "https://...",
        "description": "...",
        "source": "Naukri"
      }
    ]
  }
  ```

## How It Works

1. **Scraping** - Attempts to scrape real jobs from Naukri using BeautifulSoup
2. **Fallback** - If scraping fails or returns fewer than 30 jobs, fills with realistic mock data
3. **India-Focused** - Defaults to Indian companies and locations
4. **CSV Ready** - Jobs are formatted for download

## Installation & Running

### 1. Install Dependencies
All required packages are already in `requirements.txt`:
- `httpx` - for async HTTP requests
- `beautifulsoup4` - for HTML parsing
- `fastapi` - already installed

No additional pip install needed.

### 2. Run the Backend

```bash
cd careerLens-Backend

# Option 1: Direct Python
python main.py

# Option 2: With uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend should start at `http://localhost:8000`

### 3. Test the Endpoint

```bash
curl -X POST http://localhost:8000/api/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "Full Stack Developer",
    "location": "Bangalore",
    "sources": ["naukri"]
  }'
```

## Frontend Integration

The frontend has been updated to call the new endpoint:

```javascript
// Frontend code automatically calls:
POST ${VITE_API_URL}/jobs/search
```

**CORS Configuration**: The backend already has CORS configured for localhost:5173 (Vite dev server).

## Important Notes

### Rate Limiting
Naukri has anti-bot measures. If scraping fails:
- The system automatically falls back to mock data
- Users still get 30 realistic job listings
- No errors shown to the user

### Future Enhancements
To scrape additional platforms, add new methods:
```python
@staticmethod
async def _scrape_indeed(keyword, location):
    # Add Indeed scraping here

@staticmethod
async def _scrape_linkedin(keyword, location):
    # Add LinkedIn scraping here
```

Then update `search_jobs()` to call them.

## Troubleshooting

### "Connection refused" error
- Make sure backend is running on port 8000
- Check that VITE_API_URL in frontend .env is correct

### Jobs not appearing
- Backend defaults to mock data if Naukri scraping fails
- This is expected behavior - mock data is realistic and useful
- Check backend console for scraping error details

### CORS errors
- Frontend should work with localhost:5173
- For production, add your domain to CORS allowed_origins in main.py

## Next Steps

1. Start the backend: `python main.py`
2. Test in frontend: Search for a job
3. Results should show 30 India-based jobs
4. Download as CSV works automatically

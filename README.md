# Tunisia Price Tracker

A scalable price tracking platform that scrapes competitor websites in Tunisia and exposes data via REST API for price comparison.

## Features

- **Search-first API**: User provides product name → gets all competitor prices (fuzzy matched)
- **Config-driven scrapers**: Add new websites without writing code
- **Price history tracking**: TimescaleDB for efficient time-series storage
- **Admin dashboard**: React-based UI for managing websites and scrapers
- **Background jobs**: Celery workers for scheduled scraping

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL + TimescaleDB
- Redis
- Celery
- Playwright

### Frontend (Admin Dashboard)
- React 18 + TypeScript
- Vite
- TanStack Query
- Tailwind CSS + shadcn/ui

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for admin dashboard development)

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Seed initial data
docker-compose exec api python -m scripts.seed_data
```

The services will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Dashboard: http://localhost:3000

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Run migrations
alembic upgrade head

# Start the API
uvicorn src.main:app --reload
```

#### Admin Dashboard

```bash
cd admin

# Install dependencies
npm install

# Start dev server
npm run dev
```

## API Usage

### Core Search API

Search for products and get all competitor prices:

```bash
curl "http://localhost:8000/api/v1/search/prices?q=anua+peach+serum"
```

Response:
```json
{
  "query": "anua peach serum",
  "results": [
    {
      "product_name": "ANUA Peach 70 Niacinamide Serum 30ml",
      "website": "Freya.tn",
      "price": 45.900,
      "original_price": 52.000,
      "currency": "TND",
      "in_stock": true,
      "product_url": "https://freya.tn/...",
      "match_score": 0.92
    }
  ],
  "total_results": 5,
  "websites_searched": 3
}
```

### Authentication

Protected endpoints require an API key:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/scrapers/...
```

## Project Structure

```
tunisia-price-tracker/
├── backend/
│   ├── src/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── scrapers/        # Scraping infrastructure
│   ├── workers/             # Celery tasks
│   ├── alembic/             # Database migrations
│   └── tests/
├── admin/                   # React admin dashboard
│   └── src/
│       ├── api/             # API client
│       ├── components/      # UI components
│       └── pages/           # Page components
└── scripts/                 # Utility scripts
```

## Adding a New Website

1. Create the website via API or admin dashboard
2. Configure scraper selectors:
   ```json
   {
     "container": ".product-grid",
     "item": ".product-item",
     "name": ".product-title",
     "price": ".price",
     "url": "a.product-link::attr(href)"
   }
   ```
3. Trigger a test scrape
4. Verify products are being captured

## License

MIT

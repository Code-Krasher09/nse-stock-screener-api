# nse-stock-screener-api

[![Status](https://img.shields.io/badge/Status-%F0%9F%9A%A7%20In%20Active%20Development-yellow)](#)
[![CI Pipeline](https://github.com/Code-Krasher09/nse-stock-screener-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Code-Krasher09/nse-stock-screener-api/actions/workflows/ci.yml)

A real-time REST API for screening NSE equities using technical indicators (RSI, MACD, Bollinger Bands) built with FastAPI, PostgreSQL, and Redis.

## Tech Stack
- **Python** & **FastAPI**
- **PostgreSQL** & **SQLAlchemy** (with `asyncpg`)
- **Redis**
- **APScheduler**
- **yfinance**, **Pandas**, **NumPy**
- **Docker** & **GitHub Actions**

## Features
- **Multi-factor screening**: Screen stocks based on multiple technical indicators simultaneously.
- **Async data ingestion**: Fetch real-time and historical stock data efficiently.
- **Scheduled refresh**: Automatically update data at predefined intervals.
- **Redis caching**: Cache screener results and frequent API responses.
- **Technical indicator computation**: Real-time calculation of RSI, MACD, and Bollinger Bands.
- **Health monitoring**: Endpoints for checking API and database status.

## Project Structure
```text
nse-stock-screener-api/
├── api/             # API configuration and routing
│   └── routes/      # API endpoints (health, stocks, screen)
├── db/              # Database models and session management
├── ingestion/       # Data fetching and scheduling logic
├── indicators/      # Technical indicator computation modules
├── tests/           # Unit and integration tests
├── .env.example     # Example environment variables
├── .gitignore       # Git ignore file
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Setup Instructions

Make sure you have Docker and Docker Compose installed.

1. Clone the repository.
2. Create your `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Run the application:
   ```bash
   docker-compose up --build
   ```
4. The API will be available at `http://localhost:8000`.

## Running Tests

To run the test suite locally (requires PostgreSQL and Redis to be running):

```bash
# Install testing dependencies
pip install -r requirements.txt

# Run ruff linter
ruff check .

# Run pytest with coverage
pytest --cov=. --cov-report=term-missing
```
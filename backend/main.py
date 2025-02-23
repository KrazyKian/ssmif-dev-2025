import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import numpy as np
import pandas as pd
import dba as db  # All functions in db are assumed to be async

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Create APScheduler for periodic tasks using asyncio scheduler
scheduler = AsyncIOScheduler()

@app.get("/update_stock_data/")
async def trigger_stock_update():
    """Trigger stock data fetching and storage manually."""
    # Schedule the asynchronous update without blocking the response.
    asyncio.create_task(db.update_stock_data())
    return {"message": "Stock data update started in the background"}

@app.on_event("startup")
async def startup_event():
    """Run stock data ingestion on startup and schedule repeated execution at 4:15pm."""
    logger.info("🚀 Running stock data ingestion on startup...")
    await db.update_stock_data()  # Await the asynchronous update on startup

    # Schedule job to run every day at 4:15 PM (adjust hour/minute as needed)
    scheduler.add_job(db.update_stock_data, "cron", hour=16, minute=15, misfire_grace_time=10)
    
    # Start the scheduler if it isn't already running
    if not scheduler.running:
        scheduler.start()
        logger.info("📅 Scheduled stock update job: Runs at 4:15pm.")

@app.get("/portfolio_value")
async def get_portfolio_value():
    """Returns portfolio total value over time, adjusting for monthly trades."""
    holdings = pd.read_csv("holdings.csv")
    
    # Group trades by month to track holdings over time.
    grouped = holdings.groupby("Date")
    portfolio_values = {}

    async def task(trade_date, trade_data):
        tickers = trade_data["Symbol"].tolist()
        shares_dict = dict(zip(trade_data["Symbol"], trade_data["Shares"]))
        
        # Await the async database function to get prices for the trade date.
        result = await db.get_stock_prices_for_date(trade_date)
        logger.info(f"price_data for {trade_date}: {result}")

        # Calculate portfolio value for that month.
        total_value = np.sum(shares_dict.get(ticker, 0) * result.get(ticker, 0) for ticker in tickers)
        logger.info(f"total value for {trade_date}: {total_value}")
        portfolio_values[trade_date] = total_value

    # Create and gather tasks concurrently.
    tasks = [asyncio.create_task(task(trade_date, trade_data))
            for trade_date, trade_data in grouped]
    await asyncio.gather(*tasks)
    
    # Convert dictionary to a sorted time-series format.
    portfolio_series = [{"date": date, "value": value} for date, value in sorted(portfolio_values.items())]
    logger.info(f"hold values: {portfolio_series}")
    return portfolio_series

@app.get("/")
def root():
    return {"message": "Stock price update API is running!"}

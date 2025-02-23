import functools
import pandas as pd
import yfinance as yf
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client import Point, WriteOptions
from datetime import datetime, timedelta
import os
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment Variables for InfluxDB
INFLUXDB_URL = os.getenv("INFLUXB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "null")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "null")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "null")

# Initialize Async InfluxDB client
client = InfluxDBClientAsync(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()
write_api = client.write_api()

# CSV file location
holdings_file = "holdings.csv"

async def load_tickers():
    """Load stock tickers from the holdings CSV file, ensuring ^GSPC (S&P 500) is included."""
    df = pd.read_csv(holdings_file)
    tickers = df["Symbol"].unique().tolist()
    if "^GSPC" not in tickers:
        tickers.append("^GSPC")  # Ensure S&P 500 is included
    logger.info(f"Loaded {len(tickers)} tickers from {holdings_file}")
    return tickers

async def fetch_ticker_data(ticker, start_date):
    """Fetch stock data for a single ticker asynchronously."""
    try:
        # Run yfinance.download() in a thread to avoid blocking
        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(None, yf.download, ticker, start_date.strftime('%Y-%m-%d'))

        if df.empty:
            logger.warning(f"No data found for {ticker}.")
            return None
        
        # Add Ticker as a column for easier processing
        df["Ticker"] = ticker
        df = df[["Ticker", "Close", "Volume"]]  # Keep only relevant columns

        logger.info(f"✅ Downloaded {ticker} data with {len(df)} records.")
        return df

    except Exception as e:
        logger.error(f"❌ Error fetching {ticker} data: {e}")
        return None


async def get_latest_stock_date():
    """Query InfluxDB to find the most recent stock data date, ensuring it does not return a future date."""
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -10y)
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> last()
    '''
    result = await query_api.query(org=INFLUXDB_ORG, query=query)
    latest_date = None
    for table in result:
        for record in table.records:
            date = record.get_time().date()  # Only the date component
            logger.info(f"DATE SEEN IN DB = {date}")
            yesterday = datetime.utcnow().date()
            if date <= yesterday:
                latest_date = date.strftime('%Y-%m-%d')
    return latest_date if latest_date else "2015-01-01"  # Default to earliest date

async def fetch_and_store_ticker(ticker, start_date):
    """Fetch stock data for a single ticker and store it in InfluxDB asynchronously."""
    try:
        # Run yfinance.download() in a thread to avoid blocking
        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(None, functools.partial(yf.Ticker(ticker).history, start=start_date))

        print(df)
        
        if df.empty:
            logger.warning(f"⚠️ No valid data for {ticker}. Skipping...")
            return

        # Prepare a list of InfluxDB Points for batch writing
        points = []
        for date, row in df.iterrows():
            points.append(Point("stock_prices")\
                .tag("ticker", ticker)\
                .field("close_price", float(row["Close"]))\
                .field("volume", int(row["Volume"]) if pd.notna(row["Volume"]) else 0)\
                .time(str(date))
            )
            if len(points) > 500:
                await write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
                logger.info(f"✅ Successfully wrote {len(points)} records for {ticker} to InfluxDB.")
        await write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
        logger.info(f"✅ Successfully wrote {len(points)} records for {ticker} to InfluxDB.")

    except Exception as e:
        logger.error(f"❌ Error fetching {ticker} data: {e}")

async def fetch_stock_data(tickers: list[str]):
    """Fetch stock data from Yahoo Finance separately for each ticker and write to InfluxDB."""
    latest_date = await get_latest_stock_date()
    start_date = datetime.strptime(latest_date, '%Y-%m-%d')
    logger.info(f"Fetching stock data from {start_date.strftime('%Y-%m-%d')} for {len(tickers)} tickers...")

    # Fetch all tickers asynchronously in parallel
    tasks = [fetch_and_store_ticker(ticker, start_date) for ticker in tickers]
    await asyncio.gather(*tasks)  # Run all fetch/store tasks concurrently

    logger.info("✅ Stock data ingestion completed.")

async def update_stock_data():
    """Fetch and store stock data asynchronously."""
    tickers = await load_tickers()
    latest_date = await get_latest_stock_date()
    start_date = datetime.strptime(latest_date, '%Y-%m-%d')
    tasks = [fetch_and_store_ticker(ti, start_date) for ti in tickers]
    await asyncio.gather(*tasks)
    # await store_stock_prices(data)
    logger.info("✅ Stock data ingestion completed.")

async def fetch_latest_prices():
    """Fetch latest and previous day's prices from InfluxDB asynchronously."""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -2d)
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> filter(fn: (r) => r["_field"] == "close_price")
        |> last()
    '''
    
    result = await query_api.query(org=INFLUXDB_ORG, query=query)
    latest_prices = {}
    previous_prices = {}
    for table in result:
        for record in table.records:
            ticker = record.values["ticker"]
            date = record.get_time().date()
            price = record.values["_value"]
            if date == today:
                latest_prices[ticker] = price
            elif date == yesterday:
                previous_prices[ticker] = price
    return latest_prices, previous_prices

async def get_stock_prices_for_date(target_date: str):
    """
    Fetch closing prices for all stocks in the database for a specific date.
    If no exact match is found, it retrieves the closest available prices before the date.
    
    Args:
        target_date (str): The date in "YYYY-MM-DD" format.
        
    Returns:
        dict: A dictionary of {ticker: closing_price} pairs.
    """
    # Convert target_date to ISO 8601 timestamps for the full day.
    start_timestamp = f"{target_date}T00:00:00Z"
    end_timestamp = f"{target_date}T23:59:59Z"
    
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: {start_timestamp}, stop: {end_timestamp})
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> filter(fn: (r) => r["_field"] == "close_price")
        |> sort(columns: ["_time"], desc: false)
        |> limit(n: 1)
    '''
    
    result = await query_api.query(org=INFLUXDB_ORG, query=query)
    stock_prices = {}
    for table in result:
        for record in table.records:
            ticker = record.values["ticker"]
            price = record.values["_value"]
            stock_prices[ticker] = price
    return stock_prices

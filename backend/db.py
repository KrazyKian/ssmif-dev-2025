from collections import defaultdict
import warnings
from fastapi import requests
from requests.adapters import HTTPAdapter
import pandas as pd
from urllib3 import Retry
import yfinance as yf
from influxdb_client import InfluxDBClient, Point, WriteOptions
import requests

from datetime import datetime, timedelta
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
session = requests.Session()
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=Retry(total=3, backoff_factor=0.3))
session.mount("https://", adapter)

# Environment Variables for InfluxDB
INFLUXDB_URL = os.getenv("INFLUXB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "null")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "null")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "null")

# Initialize InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()
write_api = client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=10000))

# CSV file location
holdings_file = "holdings.csv"

def get_latest_stock_date():
    """Query InfluxDB to find the most recent stock data date, ensuring it does not return a future date."""
    
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -15y)
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> last()
    '''
    result = query_api.query(org=INFLUXDB_ORG, query=query)

    latest_date = None
    for table in result:
        for record in table.records:
            date = record.get_time().date()  # Get the date only (no time component)
            yesterday = datetime.utcnow().date()
            if date <= yesterday:
                latest_date = date.strftime('%Y-%m-%d')
    print("last seen date in DB: ", latest_date)
    return latest_date if latest_date else "2015-01-01"  # Default to earliest date

def fetch_stock_data(tickers: list[str]):
    """Fetch stock data from Yahoo Finance starting from the latest stored date."""
    if "^GSPC" not in tickers:
        tickers.append("^GSPC")
    start_date = datetime.strptime(get_latest_stock_date(), '%Y-%m-%d') - timedelta(days=1)
    logger.info(f"Fetching stock data from {start_date.strftime('%Y-%m-%d')} for {len(tickers)} tickers...")
    
    try:
        data = yf.download(tickers, start=start_date.strftime('%Y-%m-%d'), session=session)
        return data
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return None

def store_stock_prices(data: pd.DataFrame):
    """Store stock prices in InfluxDB."""
    if data is None or data.empty:
        logger.warning("No stock data to store.")
        return

    logger.info(f"Storing stock data with {len(data)} rows in InfluxDB. This may take a while....")
    
    for date, row in data.iterrows():
        for ticker in row.index.get_level_values(1).unique():
            try:
                price = row["Close"][ticker]
                open_price = row["Open"][ticker]
                volume = row["Volume"][ticker]
                if pd.notna(price):
                    point = (
                        Point("stock_prices")
                        .tag("ticker", ticker)
                        .field("close_price", float(price))
                        .field("open_price", float(open_price))
                        .field("volume", int(volume) if pd.notna(volume) else 0)
                        .time(date)
                    )
                    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
            except Exception as e:
                logger.error(f"Error storing data for {ticker} on {date}: {e}")

def update_stock_data(tickers):
    """Fetch and store stock data synchronously."""

    data = fetch_stock_data(tickers)
    store_stock_prices(data)
    logger.info("✅ Stock data ingestion completed.")

def fetch_latest_prices():
    """Fetch latest and previous day's closing prices from InfluxDB."""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -1mo)  // Adjust time range if needed
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> filter(fn: (r) => r["_field"] == "close_price")
        |> group(columns: ["ticker"])  // Group by ticker
        |> sort(columns: ["_time"], desc: true)  // Sort in descending order (latest first)
        |> limit(n: 2)  // Get the latest 2 prices per ticker
    '''
    
    result = query_api.query(org=INFLUXDB_ORG, query=query)
    
    latest_prices = defaultdict(dict)
    # latest prices = {ticker: {"open": , "prev_open": }}
    
    for table in result:
        # print(table.records)
        for i, record in enumerate(table.records):
            # print(record.values)
            ticker = record.values["ticker"]
            price = record.values["_value"]
            if i == 0:
                latest_prices[ticker]["close"] = price
            if i == 1:
                latest_prices[ticker]["prev_close"] = price
    return latest_prices
            
    



def get_stock_prices_for_date(target_date: str):
    """
    Fetch closing prices for all stocks in the database for a specific date.
    If no exact match is found, it retrieves the closest available prices before the date.
    
    Args:
        target_date (str): The date in "YYYY-MM-DD" format.
        
    Returns:
        dict: A dictionary of {ticker: closing_price} pairs.
    """
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: {target_date})
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> filter(fn: (r) => r["_field"] == "close_price")
        |> sort(columns: ["_time"], desc: false)
        |> limit(n: 1)
    '''
    
    result = query_api.query(org=INFLUXDB_ORG, query=query)

    stock_prices = {}
    for table in result:
        for record in table.records:
            ticker = record.values["ticker"]
            price = record.values["_value"]
            stock_prices[ticker] = price  # Store in dictionary {ticker: price}
    return stock_prices  # Return all stock prices for the given date

def get_monthly_stock_prices():
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: 2014-12-31T00:00:00Z)
        |> filter(fn: (r) => r["_measurement"] == "stock_prices")
        |> filter(fn: (r) => r["_field"] == "close_price")
        |> sort(columns: ["_time"], desc: false) 
        |> aggregateWindow(every: 1mo, fn: last, createEmpty: true)
'''
    result = query_api.query(org=INFLUXDB_ORG, query=query)

    stock_prices = {}

    for table in result:
        for record in table.records:
            date = record.get_time().strftime("%Y-%m-%d")  # Convert timestamp to date
            ticker = record.values["ticker"]  # Extract ticker
            price = record.values["_value"]   # Extract stock price
            if price is None:
                continue
            if date not in stock_prices:
                stock_prices[date] = {}
            
            stock_prices[date][ticker] = price  # Store data in dictionary
    return stock_prices

def get_monthly_SP_prices():
    
    query = f'''
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: 2014-12-31T00:00:00Z)
  |> filter(fn: (r) => r["_measurement"] == "stock_prices")
  |> filter(fn: (r) => r["_field"] == "close_price")
  |> filter(fn: (r) => r["ticker"] == "^GSPC")
  |> sort(columns: ["_time"], desc: false) 
  |> aggregateWindow(every: 1mo, fn: last, createEmpty: true)'''
    result = query_api.query(org=INFLUXDB_ORG, query=query)

    stock_prices = {}

    for table in result:
        for record in table.records:
            date = record.get_time().strftime("%Y-%m-%d")  # Convert timestamp to date
            price = record.values["_value"]   # Extract stock price            
            stock_prices[date] = price  # Store data in dictionary
    return stock_prices
    
def get_stock_sector(ticker):
    """
    Fetch the sector classification of a stock from Yahoo Finance.
    """
    try:
        stock = yf.Ticker(ticker)
        sector = stock.info.get("sector", "Unknown")
        return sector
    except Exception as e:
        print(f"❌ Failed to fetch sector for {ticker}: {e}")
        return "Unknown"

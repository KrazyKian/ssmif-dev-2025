import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import functools
from fastapi import FastAPI, BackgroundTasks
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np
import db
import pandas as pd
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create APScheduler for periodic tasks
scheduler = BackgroundScheduler()

holdings = pd.read_csv("holdings.csv")
holdings["Date"] = pd.to_datetime(holdings["Date"]).dt.strftime("%Y-%m-%d")



# Cache sector data to avoid repeated API calls
sector_cache = {}


def float_to_percents(value):
    return f"{value*100:.2f}%" if not np.isnan(value) else "N/A"

def monthly_portfolio_holding_values(stock_prices, holdings: pd.DataFrame):
    grouped = holdings.groupby("Date")
    portfolio_values = {}
    for trade_date, trade_data in grouped:
        
        shares_dict = dict(zip(trade_data["Symbol"], trade_data["Shares"]))
        # print(f"price_data for {trade_date}: {result}")
        tickers = shares_dict.keys()
        # Calculate portfolio value for that month
        total_value = sum(shares_dict.get(ticker, 0) * stock_prices.get(trade_date, {}).get(ticker, 0) for ticker in tickers)
        
        # Store value for this month
        portfolio_values[trade_date] = total_value
    

    # Convert dictionary to time-series format
    portfolio_series = [{"date": date, "value": round(value, 2)} for date, value in sorted(portfolio_values.items())]
    return portfolio_series


@app.on_event("startup")
async def startup_event():
    """Run stock data ingestion on startup and schedule repeated execution."""
    logger.info("🚀 Running stock data ingestion on startup...")
    db.update_stock_data(holdings["Symbol"].unique().tolist())  # Fetch stock data on app start
    for ticker in holdings['Symbol'].unique():
        sector_cache[ticker] = db.get_stock_sector(ticker)
    # Schedule job to run every minute for testing
    scheduler.add_job(
        functools.partial(db.update_stock_data, holdings["Symbol"].unique().tolist()), 
        "cron", hour=16, minute=15, misfire_grace_time=10
    )
    
    # Ensure APScheduler starts in the main thread
    if not scheduler.running:
        scheduler.start()
        logger.info("📅 Scheduled stock update job: Runs at 4:15pm.")

@app.get("/portfolio_value")
async def get_portfolio_value():
    """Returns portfolio total value over time, adjusting for monthly trades."""
    # Iterate over each trade month to compute portfolio value
    stock_prices = db.get_monthly_stock_prices()
    portfolio_series = monthly_portfolio_holding_values(stock_prices, holdings)
    # print("hold values:", portfolio_series)
    return portfolio_series

@app.get("/trades")
async def get_trades():
    """Determines monthly trades based on changes in holdings and stock prices."""
    try:
        # Load holdings data
        stock_prices = db.get_monthly_stock_prices()  # Monthly closing prices
    
        trades = []

        # Iterate over consecutive months to compute trades
        previous_month_holdings = {}

        for index, row in holdings.iterrows():
            trade_date = row["Date"]
            ticker = row["Symbol"]
            shares_held = row["Shares"]

            # Get previous month's holdings
            previous_shares = previous_month_holdings.get(ticker, 0)
            trade_volume = shares_held - previous_shares  # Net change in shares

            if trade_volume != 0:  # If there is a trade (buy/sell)
                price = stock_prices.get(trade_date, {}).get(ticker, None)

                if price is not None:
                    trades.append({
                        "Date": trade_date,
                        "Ticker": ticker,
                        "Quantity": abs(trade_volume),
                        "TotalPrice": abs(trade_volume) * price,
                        "UnitPrice": price,
                        "Type": "BUY" if trade_volume > 0 else "SELL"
                    })
            

            # Update previous month's holdings
            previous_month_holdings[ticker] = shares_held
        trades.sort(key=lambda x: x["Date"], reverse=True)
        return {"trades": trades}
    except Exception as e:
        logger.error(f"Error computing trades: {e}")
        return {"error": "Failed to determine trades"}


@app.get("/portfolio_performance")
async def get_portfolio_performance():
    """
    Returns the portfolio's performance over time compared to the S&P 500.
    Normalized to a base value of 100 at the start for percentage-based comparison.
    """
    # Load holdings data (to compute portfolio value)
    stock_prices = db.get_monthly_stock_prices()  # Historical stock prices
    portfolio_values = monthly_portfolio_holding_values(stock_prices, holdings)
    sp500_prices = db.get_monthly_SP_prices()
    # Normalize portfolio and S&P 500 values to 100 at the start
    # print("portfolio values: ", portfolio_values)
    # print("sp500 prices: ", sp500_prices)
    if not portfolio_values or not sp500_prices:
        return {"error": "Missing portfolio or S&P 500 data"}

    start_date = portfolio_values[0]['date']
    base_portfolio_value = portfolio_values[0]['value']
    base_sp500_value = sp500_prices[start_date]

    # print(portfolio_values)
    # print(sp500_prices)
    performance_data = []
    for point in portfolio_values:
        if point['date'] in sp500_prices:
            normalized_portfolio = (point['value'] / base_portfolio_value) * 100
            normalized_sp500 = (sp500_prices[point['date']] / base_sp500_value) * 100

            performance_data.append({
                "date": point['date'],
                "portfolio": normalized_portfolio,
                "sp500": normalized_sp500
            })

    return performance_data

@app.get("/sector_breakdown")
async def get_sector_breakdown():
    # Load holdings data
    stock_prices = db.get_monthly_stock_prices()

    sector_breakdown = {}

    # Compute sector-wise distribution over time
    previous_holdings = {}
    for date, trade_data in holdings.groupby("Date"):
        shares_dict = dict(zip(trade_data["Symbol"], trade_data["Shares"]))
        # print("shares_dict: ", shares_dict)
        sector_values = {}
        for index, row in trade_data.iterrows():
            ticker = row["Symbol"]
            shares = row["Shares"]
            price = stock_prices.get(date, {}).get(ticker, None)
            if price is None:
                # print(f"Skipping missing price for {ticker}")
                continue  # Skip if price is missing

            if ticker not in sector_cache:
                sector_cache[ticker] = db.get_stock_sector(ticker)
        
            sector = sector_cache[ticker]
            if sector == "Unknown":
                # print(f"Skipping unknown sector for {ticker}")
                continue

            sector_values[sector] = sector_values.get(sector, 0) + shares * price
        # print("sector values: ", sector_values)
        normalized_values = {sector: value / sum(sector_values.values()) for sector, value in sector_values.items()}
        # print("normalized values: ", normalized_values)
        sector_breakdown[date] = normalized_values

    breakdown_series = [
        {"date": date, "sectors": sector_breakdown[date]} for date in sorted(sector_breakdown.keys())
    ]

    return breakdown_series

@app.get("/holdings")
async def get_current_holdings():

    trades = await get_trades()
    trades = reversed(trades['trades'])
    cost_basis = defaultdict(list)
    current_holdings = {}
    for trade in trades:
        ticker = trade["Ticker"]
        quantity = trade["Quantity"]
        unit_price = trade["UnitPrice"]
        trade_type = trade["Type"].strip().upper()
        if trade_type == "BUY":
            # Add purchase to FIFO queue
            cost_basis[ticker].append((quantity, unit_price))

        elif trade_type == "SELL":
            # Handle selling using FIFO
            shares_to_sell = quantity
            while shares_to_sell > 0 and cost_basis[ticker]:
                bought_shares, bought_price = cost_basis[ticker][-1]

                if shares_to_sell >= bought_shares:
                    # Selling all shares from this batch
                    shares_to_sell -= bought_shares
                    cost_basis[ticker].pop()
                else:
                    # Selling only part of this batch
                    cost_basis[ticker][-1] = (bought_shares - shares_to_sell, bought_price)
                    shares_to_sell = 0


    # Compute total cost, total shares, and unit cost for each held stock
    for ticker, queue in cost_basis.items():
        total_shares = sum(shares for shares, _ in queue)
        total_cost = sum(shares * price for shares, price in queue)
        unit_cost = total_cost / total_shares if total_shares > 0 else 0
        current_holdings[ticker] = {
            "total_cost": round(total_cost, 2),
            "total_shares": total_shares,
            "unit_cost": round(unit_cost, 2)
        }
    lastest_prices =  db.fetch_latest_prices()
    # print("latest prices: ", lastest_prices)
    res = [
        {
            "ticker": ticker,
            "quantity": holding["total_shares"],
            "market_value": (market_value := 
             holding["total_shares"] 
             * lastest_prices.get(ticker, {}).get("close", "NULL")),
            "open": (open_price:=lastest_prices.get(ticker, {}).get("prev_close", "NULL")),
            "close": (close_price:=lastest_prices.get(ticker, {}).get("close", "NULL")),
            "day_change": 
                round(close_price - open_price, 2),
            "total_change": round(market_value - holding["total_cost"], 2),
            "unit_cost": round(holding["unit_cost"], 2),
            "total_cost": round(holding["total_cost"], 2),
            "day_change_prc": float_to_percents(
                (
                  lastest_prices.get(ticker, {}).get("close", "NULL") 
                  - lastest_prices.get(ticker, {}).get("prev_close", "NULL")
                )
                / lastest_prices.get(ticker, {}).get("prev_close", "NULL"),
            ),
            "total_change_prc": float_to_percents(
                (market_value - holding["total_cost"])
                / holding["total_cost"] if holding["total_cost"] > 0 else 0
            )

        }
        for ticker, holding in current_holdings.items()
    ]
    return sorted(res, key=lambda x: x["ticker"])

@app.get("/sharpe_ratio")
async def get_sharpe_ratio():
    """
    Computes the Sharpe ratio over time using monthly returns.
    """
    # Get historical stock prices
    portfolio_values = await get_portfolio_value()  # Ensure this endpoint exists
    df = pd.DataFrame(portfolio_values)

    # Convert date column to datetime and sort
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Compute monthly returns
    df["returns"] = df["value"].pct_change()

    # Compute rolling Sharpe Ratio (Assume risk-free rate = 0%)
    rolling_window = 12  # 12 months (1-year rolling Sharpe)
    df["sharpe_ratio"] = df["returns"].rolling(window=rolling_window).mean() / df["returns"].rolling(window=rolling_window).std()

    # Convert to JSON format
    sharpe_series = [{"date": row["date"].strftime("%Y-%m-%d"), "sharpe_ratio": row["sharpe_ratio"]} for _, row in df.iterrows() if not pd.isna(row["sharpe_ratio"])]

    return sharpe_series



@app.get("/")
def root():
    return {"message": "Stock price update API is running!", "status": "pass",}


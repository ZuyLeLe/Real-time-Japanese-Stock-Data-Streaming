import json
import yfinance as yf
from pymongo import MongoClient
from time import sleep
from datetime import datetime
uri = "mongodb+srv://Zuylele:<Password>@stock-data.kkn7o.mongodb.net/"

# MongoDB connection setup
client = MongoClient(uri)  # Replace with your MongoDB connection string if needed

# Two separate databases
db_3month = client['stock_3month']  # Database for 3 months of data with a 1-day interval
db_5day = client['stock_5day']      # Database for 5 days of data with a 15-minute interval

# Collections within each database
collection_3month = db_3month['historical_data']  # Collection for 3-month data
collection_5day = db_5day['historical_data']      # Collection for 5-day data

# Load tickers from JSON file
with open("Japan-ticker.json", 'r', encoding="utf-8") as f:
    stock_dict = json.load(f)

def fetch_and_store_data():
    # Fetch and store data for 3 months with 1-day interval
    for ticker, details in stock_dict.items():
        stock_info = yf.Ticker(ticker).history(period='3mo', interval='1d')

        if not stock_info.empty:
            stock_data = stock_info.reset_index().to_dict(orient='records')

            # Check for new data before inserting
            for record in stock_data:
                record['ticker'] = ticker  # Add the ticker symbol to each record
                
                # Convert the Date field to offset-naive datetime
                record_date = record['Date']
                if record_date.tzinfo is not None:  # If it's offset-aware, convert to offset-naive
                    record_date = record_date.replace(tzinfo=None)
                
                latest_entry = collection_3month.find_one(
                    {"ticker": ticker}, sort=[("Date", -1)]
                )

                if latest_entry:
                    latest_entry_date = latest_entry['Date']
                    if isinstance(latest_entry_date, str):  # If stored as a string, parse it
                        latest_entry_date = datetime.fromisoformat(latest_entry_date)

                    if latest_entry_date.tzinfo is not None:  # Ensure latest entry is offset-naive too
                        latest_entry_date = latest_entry_date.replace(tzinfo=None)

                    if record_date <= latest_entry_date:
                        continue  # Skip existing records

                collection_3month.insert_one(record)
                print(f"Inserted new 3-month data for {ticker}: {record['Date']}")
        else:
            print(f"No 3-month data found for {ticker}")

    # Fetch and store data for 5 days with 15-minute interval
    for ticker, details in stock_dict.items():
        stock_info = yf.Ticker(ticker).history(period='5d', interval='15m')

        if not stock_info.empty:
            stock_data = stock_info.reset_index().to_dict(orient='records')

            # Check for new data before inserting
            for record in stock_data:
                record['ticker'] = ticker  # Add the ticker symbol to each record
                
                # Convert the Datetime field to offset-naive datetime
                record_datetime = record['Datetime']
                if record_datetime.tzinfo is not None:  # If it's offset-aware, convert to offset-naive
                    record_datetime = record_datetime.replace(tzinfo=None)
                
                latest_entry = collection_5day.find_one(
                    {"ticker": ticker}, sort=[("Datetime", -1)]
                )

                if latest_entry:
                    latest_entry_datetime = latest_entry['Datetime']
                    if isinstance(latest_entry_datetime, str):  # If stored as a string, parse it
                        latest_entry_datetime = datetime.fromisoformat(latest_entry_datetime)

                    if latest_entry_datetime.tzinfo is not None:  # Ensure latest entry is offset-naive too
                        latest_entry_datetime = latest_entry_datetime.replace(tzinfo=None)

                    if record_datetime <= latest_entry_datetime:
                        continue  # Skip existing records

                collection_5day.insert_one(record)
                print(f"Inserted new 5-day data for {ticker}: {record['Datetime']}")
        else:
            print(f"No 5-day data found for {ticker}")

# Real-time update loop
try:
    while True:
        fetch_and_store_data()
        print(f"Update complete at {datetime.now()}. Sleeping for 15 minutes...")
        sleep(60)  # Sleep for 15 minutes (900 seconds)
except KeyboardInterrupt:
    print("Real-time update interrupted. Closing connection.")
finally:
    client.close()

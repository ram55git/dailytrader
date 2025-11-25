import pandas as pd
from datetime import datetime
from autonomous_trader import generate_watchlist
import logging

# Configure logging to print to console
logging.basicConfig(level=logging.INFO)

print("Testing generate_watchlist...")
try:
    watchlist = generate_watchlist()
    print(f"Watchlist generated with {len(watchlist)} stocks")
    if not watchlist.empty:
        print(watchlist.head())
    else:
        print("Watchlist is empty.")
except Exception as e:
    print(f"Error: {e}")

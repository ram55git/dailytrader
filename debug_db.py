from trading_engine import get_watchlist_from_db, save_watchlist
from autonomous_trader import generate_watchlist
import pandas as pd

print("Checking database watchlist...")
try:
    df = get_watchlist_from_db()
    print(f"Rows in DB: {len(df)}")
    if not df.empty:
        print(df.head())
    else:
        print("DB is empty.")
        
    print("\nRegenerating and saving...")
    watchlist = generate_watchlist()
    save_watchlist(watchlist)
    print("Saved.")
    
    print("\nChecking database again...")
    df_new = get_watchlist_from_db()
    print(f"Rows in DB: {len(df_new)}")
    if not df_new.empty:
        print(df_new.head())
except Exception as e:
    print(f"Error: {e}")

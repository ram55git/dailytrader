from trading_engine import get_watchlist_from_db, get_open_trades
import pandas as pd

print("--- Checking Database Content ---")

try:
    # Check Open Trades
    trades = get_open_trades()
    print(f"Open Trades Count: {len(trades)}")
    if not trades.empty:
        print("Sample Trade:")
        print(trades.iloc[0])
    else:
        print("No open trades.")

    print("\n--- Checking Watchlist ---")
    # Check Watchlist
    watchlist = get_watchlist_from_db()
    print(f"Watchlist Count: {len(watchlist)}")
    if not watchlist.empty:
        print("Sample Watchlist Item:")
        print(watchlist.iloc[0])
        print("\nColumns:", watchlist.columns.tolist())
    else:
        print("Watchlist is empty.")

except Exception as e:
    print(f"Error: {e}")

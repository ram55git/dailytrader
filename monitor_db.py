import time
from trading_engine import get_watchlist_from_db
import pandas as pd
from datetime import datetime

print("Monitoring watchlist table in DB...")
print("Press Ctrl+C to stop.")

last_count = -1

try:
    while True:
        try:
            df = get_watchlist_from_db()
            count = len(df)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if count != last_count:
                print(f"[{timestamp}] Watchlist count changed: {last_count} -> {count}")
                last_count = count
            else:
                # print(f"[{timestamp}] Count: {count}", end='\r')
                pass
                
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(2)
except KeyboardInterrupt:
    print("\nStopped.")

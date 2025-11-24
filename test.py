import pandas as pd
from datetime import date
import streamlit as st
import pytz
import numpy as np
from datetime import datetime, time, timedelta
import time as time_module
from streamlit_autorefresh import st_autorefresh
from nsepython import get_bhavcopy as nse_get_bhavcopy
from nsepython import get_bhavcopy
import nselib

from trading_engine import (
    now_ist, is_market_hours, is_market_open, last_two_trading_days,
    init_db, get_open_trades, open_positions_for_watchlist,
    update_positions_and_apply_exits, force_eod_exit,
    calculate_and_save_daily_pnl
)

def get_bhavcopy(trade_date_str: str):
    """Fetch bhavcopy data for a given date"""
    try:
        print(f"Fetching bhavcopy for {trade_date_str}")
        data = nse_get_bhavcopy(trade_date_str)
        return data
    except Exception as e:
        print(f"Error fetching bhavcopy: {e}")
        return []

if __name__ == "__main__":
    trade_date_last = last_two_trading_days(datetime.now().date())
    trade_date_previous = last_two_trading_days(trade_date_last)
    data_prev = pd.DataFrame(get_bhavcopy(trade_date_previous.strftime('%d-%m-%Y')))
    data_last = pd.DataFrame(get_bhavcopy(trade_date_last.strftime('%d-%m-%Y')))
    
    if data_prev.empty or data_last.empty:
        print("Bhavcopy data is empty")
        
    
    data_merged = pd.merge(data_last, data_prev, on='SYMBOL', suffixes=('_last', '_previous'))
    data_merged = data_merged.dropna(subset=[' CLOSE_PRICE_last', ' CLOSE_PRICE_previous', 
                                             ' TTL_TRD_QNTY_last', ' TTL_TRD_QNTY_previous',
                                             ' OPEN_PRICE_last'])
    
    print (data_merged.to_csv('data_merged.csv'))
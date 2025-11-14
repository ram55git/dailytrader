import nsetools
from nsepython import *
import pandas as pd
from datetime import date
import streamlit as st
import pytz
import numpy as np
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
import nselib 
import time
from streamlit_autorefresh import st_autorefresh
import requests

# Import shared trading engine functions for Supabase connectivity
from trading_engine import (
    get_db_connection, init_db, save_trade, update_trade,
    get_open_trades, get_trades_by_date, save_daily_pnl,
    get_pnl_history, get_cumulative_pnl, now_ist, is_market_hours,
    is_market_open, get_current_price, calculate_and_save_daily_pnl
)

from nsetools import Nse
nse_client = nsetools.Nse()

# Use shared constants
IST = pytz.timezone("Asia/Kolkata")
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 15
REFRESH_SECONDS = 30  # Changed to seconds for more granular control


def last_two_trading_days(start_date):
    """
    Finds the most recent previous trading day.
    """
    holiday_data = pd.DataFrame(nselib.trading_holiday_calendar())
    fil_holiday_data = holiday_data[holiday_data['Product'] == 'Equities']
    holidays_set = set(pd.to_datetime(fil_holiday_data['tradingDate'], format='%d-%b-%Y').dt.date)

    current_date = start_date - timedelta(days=1)
    while current_date.weekday() >= 5 or current_date in holidays_set:
        current_date -= timedelta(days=1)
    return current_date

# Find the two most recent trading days
    

    

def now_ist() -> datetime:
    return datetime.now(IST)

def is_market_hours() -> bool:
    """Check if current time is within market hours (9:15 AM - 3:30 PM IST)"""
    now = now_ist()
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)  # Market actually closes at 3:30 PM
    return market_open <= now <= market_close

def ensure_session_state():
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = pd.DataFrame()
    if "positions" not in st.session_state:
        # Initialize positions with proper columns even if empty
        positions = get_open_trades()
        if positions.empty:
            positions = pd.DataFrame(columns=[
                "id", "SYMBOL", "entry_price", "qty", "max_profit_pct",
                "is_open", "exit_reason", "entry_time", "exit_time",
                "exit_price", "pnl_pct", "current_price", "pnl_abs"
            ])
        st.session_state.positions = positions
    if "last_filter_date" not in st.session_state:
        st.session_state.last_filter_date = None
    if "initial_margin" not in st.session_state:
        st.session_state.initial_margin = 100000.0  # Default initial margin


def is_market_open(now: datetime) -> bool:
	start = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
	end = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
	return start <= now <= end

# get_current_price is imported from trading_engine.py


def open_positions_for_watchlist(watchlist: pd.DataFrame, capital_per_trade: float = 10000.0) -> None:
    """Open new positions from the watchlist if entry conditions are met.

    Entry conditions:
    1. Entry price must be GREATER than previous day's high
    2. Time must be after 9:20 AM (no entries in first 5 minutes)
    """
    # Check time - no entries before 9:20 AM
    now = now_ist()
    entry_start_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
    
    if now < entry_start_time:
        # Too early to enter positions
        return
    
    positions = st.session_state.positions
    open_symbols = set()
    try:
        if not positions.empty and 'is_open' in positions.columns:
            open_symbols = set(positions[positions['is_open'].astype(bool)]['SYMBOL'])
    except Exception as e:
        st.error(f"Error processing positions: {str(e)}")
        open_symbols = set()

    for _, row in watchlist.iterrows():
        symbol = row["SYMBOL"]
        if symbol in open_symbols:
            continue

        last_day_high = row.get(" HIGH_PRICE_last", row.get(" CLOSE_PRICE_last", 0))
        entry_price = get_current_price(symbol)
        
        if np.isnan(entry_price) or entry_price <= 0.0:
            continue

        # Entry logic: entry price must be GREATER than previous day's high
        if entry_price > last_day_high:
            qty = max(1, int(capital_per_trade // entry_price))
            new_pos = {
                "SYMBOL": symbol,
                "entry_price": entry_price,
                "qty": qty,
                "max_profit_pct": 0.0,
                "is_open": True,
                "exit_reason": "",
                "entry_time": now_ist(),
                "exit_time": None,
                "exit_price": None,
                "pnl_pct": 0.0,
                "current_price": entry_price,
                "pnl_abs": 0.0,
            }
            # Save trade to DB and capture id
            try:
                trade_id = save_trade(new_pos)
            except Exception:
                trade_id = None
            if trade_id:
                new_pos["id"] = trade_id
            st.session_state.positions = pd.concat([st.session_state.positions, pd.DataFrame([new_pos])], ignore_index=True)


def update_positions_and_apply_exits() -> None:
    positions = st.session_state.positions
    if positions.empty:
        return
    rows = []
    any_position_closed = False
    
    for _, pos in positions.iterrows():
        # Get current price for all positions (open or closed)
        current_price = get_current_price(pos["SYMBOL"]) if pos["is_open"] else pos.get("exit_price")
        
        # Create a copy of the position dictionary
        pos_dict = pos.to_dict()
        
        # Update current price and calculate PnL for all positions
        pos_dict["current_price"] = current_price
        
        # For closed positions, maintain their exit price and PnL
        if not pos["is_open"]:
            pos_dict["pnl_abs"] = (pos["exit_price"] - pos["entry_price"]) * pos["qty"]
            pos_dict["pnl_pct"] = (pos["exit_price"] - pos["entry_price"]) / pos["entry_price"] * 100.0
            rows.append(pos_dict)
            continue
        
        # For open positions, calculate current PnL
        if np.isnan(current_price) or current_price <= 0:
            pos_dict["pnl_abs"] = 0.0
            pos_dict["pnl_pct"] = 0.0
            rows.append(pos_dict)
            continue
        
        # Calculate PnL
        pnl_abs = (current_price - pos["entry_price"]) * pos["qty"]
        pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"] * 100.0
        max_profit_pct = max(pos["max_profit_pct"], pnl_pct)
        
        # Update position with current values
        pos_dict.update({
            "current_price": current_price,
            "pnl_abs": pnl_abs,
            "pnl_pct": pnl_pct,
            "max_profit_pct": max_profit_pct
        })
        
        # Exit rules
        position_was_open = True
        if pnl_pct <= -2.0:
            pos_dict.update({
                "is_open": False,
                "exit_reason": "StopLoss -2%",
                "exit_time": now_ist(),
                "exit_price": current_price
            })
            any_position_closed = True
        elif max_profit_pct - pnl_pct >= 10.0 and max_profit_pct > 0.0:
            pos_dict.update({
                "is_open": False,
                "exit_reason": "Trail 10% from peak",
                "exit_time": now_ist(),
                "exit_price": current_price
            })
            any_position_closed = True
        
        rows.append(pos_dict)
        
        # If position was closed, update the database
        if not pos_dict["is_open"] and position_was_open:
            update_trade(pos_dict)

    st.session_state.positions = pd.DataFrame(rows)
    
    # Recalculate daily P&L if any position was closed
    if any_position_closed:
        calculate_and_save_daily_pnl(now_ist())
    

def force_eod_exit() -> None:
	"""Close all open positions at end of day and update their exit info in the database."""
	now = now_ist()
	close_dt = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
	if now >= close_dt:
		positions = st.session_state.positions
		rows = []
		for _, pos in positions.iterrows():
			if pos["is_open"]:
				current_price = get_current_price(pos["SYMBOL"])
				if np.isnan(current_price) or current_price <= 0:
					current_price = pos.get("current_price", pos["entry_price"])
				
				pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"] * 100.0
				position_pnl = (current_price - pos["entry_price"]) * pos["qty"]
				
				pos_dict = pos.to_dict()
				pos_dict.update({
					"is_open": False,
					"exit_reason": "EOD Exit",
					"exit_time": now,
					"exit_price": current_price,
					"pnl_pct": pnl_pct,
					"pnl_abs": position_pnl,
					"current_price": current_price
				})
				
				# Update database with exit info
				if "id" in pos_dict and pos_dict["id"]:
					update_trade(pos_dict)
				
				rows.append(pos_dict)
			else:
				rows.append(pos.to_dict())
		
		st.session_state.positions = pd.DataFrame(rows)
		
		# Calculate and save total daily P&L from ALL closed positions today
		calculate_and_save_daily_pnl(now)


# All database functions are now imported from trading_engine.py
# (init_db, save_trade, update_trade, get_open_trades, get_trades_by_date, 
#  save_daily_pnl, calculate_and_save_daily_pnl, get_cumulative_pnl, get_pnl_history)


	
def main():
        
    init_db()
    st.set_page_config(page_title="NSE Momentum Screener - Paper Trade", layout="wide")
    ensure_session_state()
    
    # Auto-refresh only during market hours
    if is_market_hours():
        st_autorefresh(interval=REFRESH_SECONDS * 1000, key="autorefresh")
    else:
        st.info("🕒 Market is closed. Auto-refresh is disabled outside market hours (9:15 AM - 3:30 PM IST).")
    
    
    st.title("Day Trader (Paper Trading)")
    st.caption("Filters stocks with >5% price increase and >=5x volume vs previous day, paper-trades intraday with SL and trailing exits.")
    
    now = now_ist()
    st.sidebar.subheader("Controls")
    
    # Total Available Margin input
    total_margin = st.sidebar.number_input(
        "Total Available Margin (₹)", 
        min_value=10000, 
        max_value=10000000, 
        value=int(st.session_state.initial_margin), 
        step=10000,
        help="Your total trading capital"
    )
    
    # Update initial margin if changed
    if total_margin != st.session_state.initial_margin:
        st.session_state.initial_margin = total_margin
    
    capital_per_trade = st.sidebar.number_input("Capital per trade (₹)", min_value=1000, max_value=1000000, value=10000, step=1000)
    
    # Display Entry Rules
    st.sidebar.subheader("Entry Rules")
    st.sidebar.info(
        "✓ Time: After 9:20 AM only\n\n"
        "✓ Price: Entry > Prev Day High\n\n"
        "(No entries in first 5 mins)"
    )
    
    # Calculate and display current cash in hand
    cumulative_pnl = get_cumulative_pnl()
    current_cash = st.session_state.initial_margin + cumulative_pnl
    
    st.sidebar.subheader("Account Summary")
    st.sidebar.metric("Initial Margin", f"₹{st.session_state.initial_margin:,.2f}")
    st.sidebar.metric("Cumulative P&L", f"₹{cumulative_pnl:,.2f}", delta=f"₹{cumulative_pnl:,.2f}")
    st.sidebar.metric("Current Cash in Hand", f"₹{current_cash:,.2f}", delta=None)
    
    # Removed the refresh slider as we're using a fixed 30-second refresh
 
 
    trade_date_last = last_two_trading_days(datetime.now().date())
    trade_date_previous = last_two_trading_days(trade_date_last)
    
    
    st.write(f"Prev day: {trade_date_previous} | Last day: {trade_date_last} | Now: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Load bhavcopy data
    with st.spinner("Loading previous day bhavcopy..."):
        data_prev = pd.DataFrame(get_bhavcopy(trade_date_previous.strftime('%d-%m-%Y')))
    with st.spinner("Loading last day bhavcopy..."):
        data_last = pd.DataFrame(get_bhavcopy(trade_date_last.strftime('%d-%m-%Y')))
    data_merged = pd.merge(data_last, data_prev, on='SYMBOL', suffixes=('_last', '_previous'))
   
    data_merged = data_merged.dropna(subset=[' CLOSE_PRICE_last', ' CLOSE_PRICE_previous', ' TTL_TRD_QNTY_last', ' TTL_TRD_QNTY_previous'])
    
    
    data_merged["price_change_pct"] = (data_merged[" CLOSE_PRICE_last"] - data_merged[" CLOSE_PRICE_previous"]) / data_merged[" CLOSE_PRICE_previous"] * 100.0
    data_merged["volume_ratio"] = data_merged[" TTL_TRD_QNTY_last"] / data_merged[" TTL_TRD_QNTY_previous"]
    data_merged["fract_close"]= (data_merged[" HIGH_PRICE_last"] - data_merged[" CLOSE_PRICE_last"])/(data_merged[" HIGH_PRICE_last"] - data_merged[" LOW_PRICE_last"])
    data_merged["fract_body"]= abs((data_merged[" CLOSE_PRICE_last"] - data_merged[" OPEN_PRICE_last"]))/(data_merged[" HIGH_PRICE_last"] - data_merged[" LOW_PRICE_last"])
    
    data_filtered = data_merged[(data_merged["price_change_pct"] > 5.0) & (data_merged["volume_ratio"] >= 5.0)& (data_merged["fract_close"]<0.3)& (data_merged["fract_body"]>0.7)]
    
    #st.write(data_filtered[['SYMBOL', ' CLOSE_PRICE_last', ' TTL_TRD_QNTY_last', ' CLOSE_PRICE_previous', ' TTL_TRD_QNTY_previous', 'price_change_pct', 'volume_ratio']])
    
    
    if not data_filtered.empty:
        st.subheader("Filtered candidates")
        st.dataframe(data_filtered[['SYMBOL', ' CLOSE_PRICE_last', ' TTL_TRD_QNTY_last', ' CLOSE_PRICE_previous', ' TTL_TRD_QNTY_previous', 'price_change_pct', 'volume_ratio']])
        #st.dataframe(data_filtered, use_container_width=True)
        st.session_state.watchlist = data_filtered[["SYMBOL"," CLOSE_PRICE_last"," HIGH_PRICE_last"]].copy()
    else:
        st.info("No candidates met the criteria today.")
        
   
    
    # Show entry status
    entry_start_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
    if is_market_open(now):
        if now < entry_start_time:
            minutes_to_entry = int((entry_start_time - now).total_seconds() / 60)
            st.warning(f"⏳ Entries will be allowed after 9:20 AM (in {minutes_to_entry} minute(s))")
        else:
            st.success("✅ Entry conditions active: Price must be > Previous Day's High")
        open_positions_for_watchlist(st.session_state.watchlist, capital_per_trade=capital_per_trade)
    else:
        st.info("Market is closed. No new positions will be opened.")

    update_positions_and_apply_exits()
    force_eod_exit()

    # Display today's P&L prominently
    today_date = now.strftime("%Y-%m-%d")
    
    # Get today's P&L from Supabase
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_pnl FROM daily_pnl WHERE date = %s", (today_date,))
    result = cursor.fetchone()
    today_pnl = result[0] if result else 0.0
    cursor.close()
    conn.close()
    
    # Calculate unrealized P&L from open positions
    unrealized_pnl = 0.0
    if not st.session_state.positions.empty:
        open_positions = st.session_state.positions[st.session_state.positions['is_open'] == True]
        if not open_positions.empty:
            unrealized_pnl = open_positions['pnl_abs'].sum()
    
    # Display P&L metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Today's Realized P&L", f"₹{today_pnl:.2f}", delta=None)
    with col2:
        st.metric("Unrealized P&L (Open)", f"₹{unrealized_pnl:.2f}", delta=None)
    with col3:
        total_today_pnl = today_pnl + unrealized_pnl
        st.metric("Total P&L (Today)", f"₹{total_today_pnl:.2f}", delta=None)
    with col4:
        # Show current cash including today's P&L
        current_cash_with_today = current_cash + unrealized_pnl
        pnl_return_pct = (cumulative_pnl / st.session_state.initial_margin * 100) if st.session_state.initial_margin > 0 else 0
        st.metric("Cash + Unrealized", f"₹{current_cash_with_today:,.2f}", delta=f"{pnl_return_pct:.2f}%")

    st.subheader("Positions")
    positions = st.session_state.positions.copy()
    if not positions.empty:
        # Format and display positions with current prices and PnL
        display_cols = [
            "SYMBOL", "entry_price", "current_price", "qty", 
            "pnl_abs", "pnl_pct", "max_profit_pct", "is_open", 
            "exit_reason", "entry_time", "exit_time"
        ]
        display_positions = positions[display_cols].copy()
        
        # Format numeric columns
        display_positions["entry_price"] = display_positions["entry_price"].round(2)
        display_positions["current_price"] = display_positions["current_price"].round(2)
        display_positions["pnl_abs"] = display_positions["pnl_abs"].round(2)
        display_positions["pnl_pct"] = display_positions["pnl_pct"].round(2)
        display_positions["max_profit_pct"] = display_positions["max_profit_pct"].round(2)
        
        st.dataframe(display_positions, use_container_width=True)
    else:
        st.write("No positions yet.")
        

    
	 # Display P&L Summary
    st.subheader("P&L Summary")
    pnl_history = get_pnl_history()
    if not pnl_history.empty:
    # Weekly Summary
        st.write("#### Weekly P&L")
        pnl_history["week"] = pnl_history["date"].dt.to_period("W")
        weekly_pnl = pnl_history.groupby("week")["total_pnl"].sum().reset_index()
        weekly_pnl["week"] = weekly_pnl["week"].astype(str)
        st.dataframe(weekly_pnl, use_container_width=True)

        # Monthly Summary
        st.write("#### Monthly P&L")
        pnl_history["month"] = pnl_history["date"].dt.to_period("M")
        monthly_pnl = pnl_history.groupby("month")["total_pnl"].sum().reset_index()
        monthly_pnl["month"] = monthly_pnl["month"].astype(str)
        st.dataframe(monthly_pnl, use_container_width=True)

        # Yearly Summary
        st.write("#### Yearly P&L")
        pnl_history["year"] = pnl_history["date"].dt.to_period("Y")
        yearly_pnl = pnl_history.groupby("year")["total_pnl"].sum().reset_index()
        yearly_pnl["year"] = yearly_pnl["year"].astype(str)
        st.dataframe(yearly_pnl, use_container_width=True)
    else:
        st.write("No P&L history available.")
    
    # Historical Trades by Date Section
    st.subheader("Historical Trades")
    st.write("Select a date to view all trades closed on that day:")
    
    # Date picker
    selected_date = st.date_input(
        "Select Date",
        value=datetime.now(IST).date(),
        max_value=datetime.now(IST).date(),
        key="trade_history_date"
    )
    
    # Convert date to string format for database query
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Get trades for selected date
    trades_on_date = get_trades_by_date(date_str)
    
    if not trades_on_date.empty:
        # Calculate summary statistics
        total_trades = len(trades_on_date)
        winning_trades = len(trades_on_date[trades_on_date['profit_abs'] > 0])
        losing_trades = len(trades_on_date[trades_on_date['profit_abs'] < 0])
        total_profit = trades_on_date['profit_abs'].sum()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Display summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Trades", total_trades)
        with col2:
            st.metric("Winning", winning_trades, delta=None)
        with col3:
            st.metric("Losing", losing_trades, delta=None)
        with col4:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col5:
            st.metric("Total P&L", f"₹{total_profit:.2f}")
        
        # Format and display trades
        display_trades = trades_on_date.copy()
        display_trades["entry_price"] = display_trades["entry_price"].round(2)
        display_trades["exit_price"] = display_trades["exit_price"].round(2)
        display_trades["pnl_pct"] = display_trades["pnl_pct"].round(2)
        display_trades["profit_abs"] = display_trades["profit_abs"].round(2)
        
        # Rename columns for better display
        display_trades = display_trades.rename(columns={
            "SYMBOL": "Symbol",
            "entry_price": "Entry Price",
            "exit_price": "Exit Price",
            "qty": "Quantity",
            "pnl_pct": "P&L %",
            "profit_abs": "Profit (₹)",
            "exit_reason": "Exit Reason",
            "entry_time": "Entry Time",
            "exit_time": "Exit Time"
        })
        
        st.dataframe(display_trades, use_container_width=True)
    else:
        st.info(f"No closed trades found for {date_str}")
    
    
    #st_autorefresh(interval=120000, key="datarefresh")
        
    
    
    
    
    
    
    

if __name__ == "__main__":
    main()


import pandas as pd
from datetime import date
import streamlit as st
import pytz
import numpy as np
from datetime import datetime, time, timedelta
import time as time_module
from streamlit_autorefresh import st_autorefresh
from nsepython import get_bhavcopy as nse_get_bhavcopy
import nselib

# Import shared trading engine functions for Supabase connectivity
# NOTE: This is a READ-ONLY dashboard - no trading actions are performed here
# All trading is done by autonomous_trader.py
from trading_engine import (
    get_db_connection, init_db,
    get_open_trades, get_trades_by_date,
    get_pnl_history, get_cumulative_pnl, now_ist, is_market_hours,
    is_market_open, get_current_price, last_two_trading_days
)

# Use shared constants
IST = pytz.timezone("Asia/Kolkata")
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 15
REFRESH_SECONDS = 30  # Changed to seconds for more granular control


# Use shared constants from trading_engine
# last_two_trading_days is imported from trading_engine

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

# ============================================================================
# READ-ONLY VIEWER FUNCTIONS
# All trading actions are performed by autonomous_trader.py
# ============================================================================

def update_positions_display() -> None:
    """Update position display with current prices and P&L (read-only)."""
    positions = st.session_state.positions
    if positions.empty:
        return
    
    rows = []
    for _, pos in positions.iterrows():
        # Get current price for display purposes only
        current_price = get_current_price(pos["SYMBOL"]) if pos["is_open"] else pos.get("exit_price")
        
        # Create a copy of the position dictionary
        pos_dict = pos.to_dict()
        
        # Update current price and calculate PnL for display
        pos_dict["current_price"] = current_price
        
        # For closed positions, maintain their exit price and PnL
        if not pos["is_open"]:
            pos_dict["pnl_abs"] = (pos["exit_price"] - pos["entry_price"]) * pos["qty"]
            pos_dict["pnl_pct"] = (pos["exit_price"] - pos["entry_price"]) / pos["entry_price"] * 100.0
            rows.append(pos_dict)
            continue
        
        # For open positions, calculate current PnL for display
        if np.isnan(current_price) or current_price <= 0:
            pos_dict["pnl_abs"] = 0.0
            pos_dict["pnl_pct"] = 0.0
            rows.append(pos_dict)
            continue
        
        # Calculate PnL for display
        pnl_abs = (current_price - pos["entry_price"]) * pos["qty"]
        pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"] * 100.0
        max_profit_pct = pos.get("max_profit_pct", 0.0)
        
        # Update position with current values (display only)
        pos_dict.update({
            "current_price": current_price,
            "pnl_abs": pnl_abs,
            "pnl_pct": pnl_pct,
            "max_profit_pct": max_profit_pct
        })
        
        rows.append(pos_dict)

    st.session_state.positions = pd.DataFrame(rows)

	
def main():
        
    init_db()
    st.set_page_config(page_title="NSE Momentum Screener - Monitoring Dashboard", layout="wide")
    ensure_session_state()
    
    # Auto-refresh only during market hours
    if is_market_hours():
        st_autorefresh(interval=REFRESH_SECONDS * 1000, key="autorefresh")
    else:
        st.info("🕒 Market is closed. Auto-refresh is disabled outside market hours (9:15 AM - 3:30 PM IST).")
    
    
    st.title("📊 Day Trader - Monitoring Dashboard")
    st.caption("**READ-ONLY VIEWER** - Displaying trades executed by autonomous_trader.py on Railway.app")
    st.info("ℹ️ This dashboard only displays data. All trading actions are performed by the autonomous bot running on Railway.", icon="ℹ️")
    
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
    cumulative_pnl = float(get_cumulative_pnl())
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
        data_prev = pd.DataFrame(nse_get_bhavcopy(trade_date_previous.strftime('%d-%m-%Y')))
    with st.spinner("Loading last day bhavcopy..."):
        data_last = pd.DataFrame(nse_get_bhavcopy(trade_date_last.strftime('%d-%m-%Y')))
    data_merged = pd.merge(data_last, data_prev, on='SYMBOL', suffixes=('_last', '_previous'))
   
    data_merged = data_merged.dropna(subset=[' CLOSE_PRICE_last', ' CLOSE_PRICE_previous', ' TTL_TRD_QNTY_last', ' TTL_TRD_QNTY_previous'])
    
    
    data_merged["price_change_pct"] = (data_merged[" CLOSE_PRICE_last"] - data_merged[" CLOSE_PRICE_previous"]) / data_merged[" CLOSE_PRICE_previous"] * 100.0
    data_merged["volume_ratio"] = data_merged[" TTL_TRD_QNTY_last"] / data_merged[" TTL_TRD_QNTY_previous"]
    
    # Filter based on criteria:
    # 1. Price change > 5%
    # 2. Volume ratio >= 5x
    # 3. Bullish candle (Close > Open)
    data_filtered = data_merged[
        (data_merged["price_change_pct"] > 5.0) & 
        (data_merged["volume_ratio"] >= 5.0) & 
        (data_merged[" CLOSE_PRICE_last"] > data_merged[" OPEN_PRICE_last"])
    ]
    
    #st.write(data_filtered[['SYMBOL', ' CLOSE_PRICE_last', ' TTL_TRD_QNTY_last', ' CLOSE_PRICE_previous', ' TTL_TRD_QNTY_previous', 'price_change_pct', 'volume_ratio']])
    
    
    if not data_filtered.empty:
        st.subheader("Filtered candidates")
        st.dataframe(data_filtered[['SYMBOL', ' CLOSE_PRICE_last', ' TTL_TRD_QNTY_last', ' CLOSE_PRICE_previous', ' TTL_TRD_QNTY_previous', 'price_change_pct', 'volume_ratio']])
        #st.dataframe(data_filtered, use_container_width=True)
        st.session_state.watchlist = data_filtered[["SYMBOL"," CLOSE_PRICE_last"," HIGH_PRICE_last"]].copy()
    else:
        st.info("No candidates met the criteria today.")
        
   
    
    # Show market status (read-only info)
    entry_start_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
    if is_market_open(now):
        if now < entry_start_time:
            minutes_to_entry = int((entry_start_time - now).total_seconds() / 60)
            st.info(f"ℹ️ Trading starts at 9:20 AM (in {minutes_to_entry} minute(s)) - Managed by autonomous_trader.py")
        else:
            st.info("ℹ️ Trading active - All trades managed by autonomous_trader.py")
    else:
        st.info("Market is closed. Trading resumes next market day.")

    # Update position display with current prices (read-only)
    update_positions_display()

    # Display today's P&L prominently
    today_date = now.strftime("%Y-%m-%d")
    
    # Get today's P&L from Supabase
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_pnl FROM daily_pnl WHERE date = %s", (today_date,))
    result = cursor.fetchone()
    today_pnl = float(result[0]) if result else 0.0
    cursor.close()
    conn.close()
    
    # Calculate unrealized P&L from open positions
    unrealized_pnl = 0.0
    if not st.session_state.positions.empty:
        open_positions = st.session_state.positions[st.session_state.positions['is_open'] == True]
        if not open_positions.empty:
            unrealized_pnl = float(open_positions['pnl_abs'].sum())
    
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


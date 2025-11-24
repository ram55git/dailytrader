"""
Trading Engine Module - Core trading logic separated from UI
This module contains all trading functions that can run autonomously
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import nselib
import psycopg2
#from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, List, Tuple

# Load configuration
from config import DB_CONFIG, validate_config

# Validate configuration on import
validate_config()

# Configuration
IST = pytz.timezone("Asia/Kolkata")
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 15


# ============= UTILITY FUNCTIONS =============

def now_ist() -> datetime:
    """Get current time in IST timezone"""
    return datetime.now(IST)


def is_market_hours() -> bool:
    """Check if current time is within market hours (9:15 AM - 3:30 PM IST)"""
    now = now_ist()
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def is_market_open(now: datetime) -> bool:
    """Check if market is currently open"""
    start = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    end = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    return start <= now <= end


def last_two_trading_days(start_date):
    """Find the most recent previous trading day excluding weekends and holidays"""
    holiday_data = pd.DataFrame(nselib.trading_holiday_calendar())
    fil_holiday_data = holiday_data[holiday_data['Product'] == 'Equities']
    holidays_set = set(pd.to_datetime(fil_holiday_data['tradingDate'], format='%d-%b-%Y').dt.date)

    current_date = start_date - timedelta(days=1)
    while current_date.weekday() >= 5 or current_date in holidays_set:
        current_date -= timedelta(days=1)
    return current_date


def get_current_price(symbol: str) -> float:
    """Fetch current price from Google Finance"""
    try:
        ltp = float((BeautifulSoup((requests.get(f'https://www.google.com/finance/quote/{symbol}:NSE')).text, 'html.parser')
                    .find(class_="YMlKec fxKbKc").text.strip()[1:].replace(",", "")))
        return ltp
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return np.nan


# ============= DATABASE FUNCTIONS =============

def get_db_connection():
    """Create and return a database connection"""
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create trades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(50),
            entry_price DECIMAL(10, 2),
            qty INTEGER,
            max_profit_pct DECIMAL(10, 2),
            is_open BOOLEAN,
            exit_reason TEXT,
            entry_time TIMESTAMP,
            exit_time TIMESTAMP,
            exit_price DECIMAL(10, 2),
            pnl_pct DECIMAL(10, 2)
        )
    """)
    
    # Create daily_pnl table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_pnl (
            date DATE PRIMARY KEY,
            total_pnl DECIMAL(10, 2)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully")


def save_trade(trade: dict) -> Optional[int]:
    """Save a new trade to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert datetime objects to strings
    entry_time_str = trade["entry_time"].strftime("%Y-%m-%d %H:%M:%S") if trade["entry_time"] else None
    exit_time_str = trade["exit_time"].strftime("%Y-%m-%d %H:%M:%S") if trade["exit_time"] else None
    
    cursor.execute("""
        INSERT INTO trades (symbol, entry_price, qty, max_profit_pct, is_open, exit_reason, 
                           entry_time, exit_time, exit_price, pnl_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        trade["SYMBOL"],
        trade["entry_price"],
        trade["qty"],
        trade["max_profit_pct"],
        trade["is_open"],
        trade["exit_reason"],
        entry_time_str,
        exit_time_str,
        trade["exit_price"],
        trade["pnl_pct"],
    ))
    
    trade_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return trade_id


def update_trade(trade: dict):
    """Update an existing trade in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert datetime to string if it's a datetime object
    exit_time_str = trade["exit_time"]
    if isinstance(exit_time_str, datetime):
        exit_time_str = exit_time_str.strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        UPDATE trades
        SET is_open = %s, exit_reason = %s, exit_time = %s, exit_price = %s, 
            pnl_pct = %s, max_profit_pct = %s
        WHERE id = %s
    """, (
        trade["is_open"],
        trade["exit_reason"],
        exit_time_str,
        trade["exit_price"],
        trade["pnl_pct"],
        trade["max_profit_pct"],
        trade["id"],
    ))
    
    conn.commit()
    cursor.close()
    conn.close()


def get_open_trades() -> pd.DataFrame:
    """Retrieve all open trades from database"""
    conn = get_db_connection()
    
    query = """
        SELECT 
            id,
            symbol as "SYMBOL",
            entry_price,
            qty,
            max_profit_pct,
            is_open,
            exit_reason,
            entry_time,
            exit_time,
            exit_price,
            pnl_pct,
            NULL as current_price,
            0 as pnl_abs
        FROM trades 
        WHERE is_open = TRUE
    """
    
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['is_open'] = df['is_open'].astype(bool)
    
    conn.close()
    return df


def get_trades_by_date(selected_date: str) -> pd.DataFrame:
    """Retrieve all closed trades for a specific date"""
    conn = get_db_connection()
    
    query = """
        SELECT 
            symbol as "SYMBOL",
            entry_price,
            exit_price,
            qty,
            pnl_pct,
            exit_reason,
            entry_time,
            exit_time,
            (exit_price - entry_price) * qty as profit_abs
        FROM trades 
        WHERE is_open = FALSE 
        AND DATE(exit_time) = %s
        ORDER BY exit_time
    """
    
    df = pd.read_sql_query(query, conn, params=(selected_date,))
    conn.close()
    return df


def save_daily_pnl(date: str, total_pnl: float):
    """Save or update daily P&L"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO daily_pnl (date, total_pnl) 
        VALUES (%s, %s)
        ON CONFLICT (date) 
        DO UPDATE SET total_pnl = %s
    """, (date, total_pnl, total_pnl))
    
    conn.commit()
    cursor.close()
    conn.close()


def get_pnl_history() -> pd.DataFrame:
    """Get historical P&L data"""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT date, total_pnl FROM daily_pnl ORDER BY date", conn)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    conn.close()
    return df


def get_cumulative_pnl() -> float:
    """Calculate cumulative P&L from all historical data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_pnl) FROM daily_pnl")
    result = cursor.fetchone()
    cumulative = result[0] if result and result[0] else 0.0
    cursor.close()
    conn.close()
    return cumulative


# ============= TRADING LOGIC FUNCTIONS =============

def open_positions_for_watchlist(watchlist: pd.DataFrame, positions: pd.DataFrame, 
                                 capital_per_trade: float = 10000.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Open new positions from the watchlist if entry conditions are met.
    
    Entry conditions:
    1. Entry price must be > 1.01 * Previous Day's Close (1% higher)
    2. Time must be after 9:20 AM (no entries in first 5 minutes)
    
    Returns:
        Tuple of (updated positions DataFrame, list of messages)
    """
    messages = []
    now = now_ist()
    
    # Check time - no entries before 9:20 AM
    entry_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
    if now < entry_time:
        messages.append(f"⏰ Waiting for 9:20 AM to start entries (Current: {now.strftime('%H:%M:%S')})")
        return positions, messages
    
    for _, row in watchlist.iterrows():
        symbol = row["SYMBOL"]
        last_day_close = row.get("CLOSE_PRICE_last", 0)
        target_entry_price = last_day_close * 1.01
        
        # Skip if already in positions
        if not positions.empty and symbol in positions["SYMBOL"].values:
            continue
        
        entry_price = get_current_price(symbol)
        
        if np.isnan(entry_price) or entry_price <= 0.0:
            continue
        
        # Entry logic: entry price > 1.01 * last day's close price
        if entry_price > target_entry_price:
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
            
            try:
                trade_id = save_trade(new_pos)
                if trade_id:
                    new_pos["id"] = trade_id
                    positions = pd.concat([positions, pd.DataFrame([new_pos])], ignore_index=True)
                    messages.append(f"✅ Opened position: {symbol} @ ₹{entry_price:.2f}, Qty: {qty}")
            except Exception as e:
                messages.append(f"❌ Error saving trade for {symbol}: {e}")
    
    return positions, messages


def update_positions_and_apply_exits(positions: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Update positions with current prices and apply exit conditions:
    - Stop loss at -2%
    - Trailing stop at 10% drawdown from peak profit
    
    Returns:
        Tuple of (updated positions DataFrame, list of messages)
    """
    messages = []
    now = now_ist()
    
    if positions.empty:
        return positions, messages
    
    rows = []
    for _, pos in positions.iterrows():
        if pos["is_open"]:
            current_price = get_current_price(pos["SYMBOL"])
            if np.isnan(current_price) or current_price <= 0:
                current_price = pos.get("current_price", pos["entry_price"])
            
            pnl_pct = (current_price - pos["entry_price"]) / pos["entry_price"] * 100.0
            position_pnl = (current_price - pos["entry_price"]) * pos["qty"]
            
            max_profit_pct = max(pos["max_profit_pct"], pnl_pct)
            
            pos_dict = pos.to_dict()
            pos_dict.update({
                "current_price": current_price,
                "pnl_pct": pnl_pct,
                "pnl_abs": position_pnl,
                "max_profit_pct": max_profit_pct
            })
            
            # Exit condition 1: Stop loss at -2%
            if pnl_pct <= -2.0:
                pos_dict.update({
                    "is_open": False,
                    "exit_reason": "Stop Loss -2%",
                    "exit_time": now_ist(),
                    "exit_price": current_price
                })
                messages.append(f"🛑 Stop Loss: {pos['SYMBOL']} @ ₹{current_price:.2f}, P&L: {pnl_pct:.2f}%")
            
            # Exit condition 2: Trailing stop - if profit drops 10% from peak
            elif max_profit_pct > 0 and (max_profit_pct - pnl_pct >= 10.0):
                pos_dict.update({
                    "is_open": False,
                    "exit_reason": "Trail 10% from peak",
                    "exit_time": now_ist(),
                    "exit_price": current_price
                })
                messages.append(f"📉 Trailing Stop: {pos['SYMBOL']} @ ₹{current_price:.2f}, Peak: {max_profit_pct:.2f}%, Current: {pnl_pct:.2f}%")
            
            # Update database if position was closed
            if not pos_dict["is_open"] and "id" in pos_dict and pos_dict["id"]:
                update_trade(pos_dict)
            
            rows.append(pos_dict)
        else:
            rows.append(pos.to_dict())
    
    positions = pd.DataFrame(rows)
    return positions, messages


def force_eod_exit(positions: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Close all open positions at end of day (3:15 PM)
    
    Returns:
        Tuple of (updated positions DataFrame, list of messages)
    """
    messages = []
    now = now_ist()
    close_dt = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    
    if now < close_dt:
        return positions, messages
    
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
            
            if "id" in pos_dict and pos_dict["id"]:
                update_trade(pos_dict)
            
            messages.append(f"🌙 EOD Exit: {pos['SYMBOL']} @ ₹{current_price:.2f}, P&L: {pnl_pct:.2f}%")
            rows.append(pos_dict)
        else:
            rows.append(pos.to_dict())
    
    positions = pd.DataFrame(rows)
    return positions, messages


def calculate_and_save_daily_pnl(current_time: datetime = None) -> float:
    """
    Calculate and save total daily P&L from all closed trades today
    
    Returns:
        Total P&L for the day
    """
    if current_time is None:
        current_time = now_ist()
    
    today_date = current_time.strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all trades that were closed today
    cursor.execute("""
        SELECT SUM((exit_price - entry_price) * qty) as total_pnl
        FROM trades
        WHERE is_open = FALSE
        AND DATE(exit_time) = %s
    """, (today_date,))
    
    result = cursor.fetchone()
    total_pnl = result[0] if result and result[0] else 0.0
    
    cursor.close()
    conn.close()
    
    # Save to daily_pnl table
    save_daily_pnl(today_date, total_pnl)
    
    return total_pnl


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    try:
        init_db()
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

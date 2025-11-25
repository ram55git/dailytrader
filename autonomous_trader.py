"""
Autonomous Trading Bot - Runs independently without Streamlit
This service runs the trading logic on a schedule throughout the trading day
"""

import schedule
import time
import logging
from datetime import datetime
import pandas as pd
from nsepython import get_bhavcopy as nse_get_bhavcopy
import nselib

# Load configuration
from config import CAPITAL_PER_TRADE, PRICE_CHANGE_THRESHOLD, VOLUME_RATIO_THRESHOLD

from trading_engine import (
    now_ist, is_market_hours, is_market_open, last_two_trading_days,
    init_db, get_open_trades, open_positions_for_watchlist,
    update_positions_and_apply_exits, force_eod_exit,
    calculate_and_save_daily_pnl, save_watchlist
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_bhavcopy(trade_date_str: str):
    """Fetch bhavcopy data for a given date"""
    try:
        logger.info(f"Fetching bhavcopy for {trade_date_str}")
        data = nse_get_bhavcopy(trade_date_str)
        return data
    except Exception as e:
        logger.error(f"Error fetching bhavcopy: {e}")
        return []


def generate_watchlist() -> pd.DataFrame:
    """
    Generate watchlist based on momentum criteria:
    - Price change > 5% from previous day
    - Volume ratio >= 5x from previous day
    """
    logger.info("Generating watchlist...")
    
    trade_date_last = last_two_trading_days(datetime.now().date())
    trade_date_previous = last_two_trading_days(trade_date_last)
    
    logger.info(f"Prev day: {trade_date_previous} | Last day: {trade_date_last}")
    
    # Load bhavcopy data
    data_prev = pd.DataFrame(get_bhavcopy(trade_date_previous.strftime('%d-%m-%Y')))
    data_last = pd.DataFrame(get_bhavcopy(trade_date_last.strftime('%d-%m-%Y')))
    
    if data_prev.empty or data_last.empty:
        logger.warning("Bhavcopy data is empty")
        return pd.DataFrame()
    
    data_merged = pd.merge(data_last, data_prev, on='SYMBOL', suffixes=('_last', '_previous'))
    data_merged = data_merged.dropna(subset=[' CLOSE_PRICE_last', ' CLOSE_PRICE_previous', 
                                             ' TTL_TRD_QNTY_last', ' TTL_TRD_QNTY_previous',
                                             ' OPEN_PRICE_last'])
    
    # Calculate metrics
    data_merged["price_change_pct"] = (
        (data_merged[" CLOSE_PRICE_last"] - data_merged[" CLOSE_PRICE_previous"]) / 
        data_merged[" CLOSE_PRICE_previous"] * 100.0
    )
    data_merged["volume_ratio"] = (
        data_merged[" TTL_TRD_QNTY_last"] / data_merged[" TTL_TRD_QNTY_previous"]
    )
    
    # Filter based on criteria
    # 1. Price change >= Threshold
    # 2. Volume ratio >= Threshold
    # 3. Bullish candle: Close > Open
    filtered = data_merged[
        (data_merged["price_change_pct"] >= PRICE_CHANGE_THRESHOLD) &
        (data_merged["volume_ratio"] >= VOLUME_RATIO_THRESHOLD) &
        (data_merged[" CLOSE_PRICE_last"] > data_merged[" OPEN_PRICE_last"])
    ]
    
    # Select required columns
    watchlist = filtered[["SYMBOL", "price_change_pct", "volume_ratio", " HIGH_PRICE_last", " CLOSE_PRICE_last", " CLOSE_PRICE_previous"]].copy()
    watchlist = watchlist.rename(columns={
        " HIGH_PRICE_last": "HIGH_PRICE_last", 
        " CLOSE_PRICE_last": "CLOSE_PRICE_last",
        " CLOSE_PRICE_previous": "CLOSE_PRICE_previous"
    })
    watchlist = watchlist.sort_values("price_change_pct", ascending=False)
    
    logger.info(f"Watchlist generated with {len(watchlist)} stocks")
    return watchlist


class TradingBot:
    def __init__(self):
        self.positions = pd.DataFrame()
        self.watchlist = pd.DataFrame()
        self.is_running = False
        self.last_generation_date = None
        
    def initialize(self):
        """Initialize the bot and database"""
        logger.info("Initializing trading bot...")
        try:
            init_db()
            self.positions = get_open_trades()
            logger.info(f"Loaded {len(self.positions)} open positions")
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise
    
    def generate_daily_watchlist(self):
        """Generate watchlist at market open (9:15 AM)"""
        today = datetime.now().date()
        if self.last_generation_date == today:
            logger.info(f"Watchlist already generated for today ({today})")
            return
        
        logger.info("🔍 Generating daily watchlist...")
        try:
            self.watchlist = generate_watchlist()
            
            # Save to database for Streamlit app
            save_watchlist(self.watchlist)
            logger.info("💾 Watchlist saved to database")
            
            self.last_generation_date = today
            logger.info(f"✅ Watchlist generated: {len(self.watchlist)} stocks")
            if not self.watchlist.empty:
                logger.info(f"Top stocks: {self.watchlist['SYMBOL'].head(5).tolist()}")
        except Exception as e:
            logger.error(f"❌ Error generating watchlist: {e}")
    
    def monitor_and_trade(self):
        """Main trading loop - runs every 30 seconds during market hours"""
        now = now_ist()
        
        # Stop monitoring after 3:25 PM (give 10 mins buffer after 3:15 exit)
        cutoff_time = now.replace(hour=15, minute=25, second=0, microsecond=0)
        if now > cutoff_time:
            logger.info("🛑 Market closed (post 3:25 PM). Stopping monitoring.")
            return

        # Use is_market_hours (up to 3:30 PM) instead of is_market_open (up to 3:15 PM)
        # This ensures we keep running to trigger the 3:15 PM EOD exit
        if not is_market_hours():
            logger.debug("Market is closed, skipping monitoring")
            return
        
        logger.info("📊 Monitoring positions...")
        
        try:
            # Reload current positions from database
            self.positions = get_open_trades()
            
            # Update positions with current prices and apply exit conditions
            self.positions, exit_messages = update_positions_and_apply_exits(self.positions)
            for msg in exit_messages:
                logger.info(msg)
            
            # Check for EOD exit
            self.positions, eod_messages = force_eod_exit(self.positions)
            for msg in eod_messages:
                logger.info(msg)
            
            # Try to open new positions from watchlist
            if not self.watchlist.empty:
                self.positions, entry_messages = open_positions_for_watchlist(
                    self.watchlist, self.positions, CAPITAL_PER_TRADE
                )
                for msg in entry_messages:
                    logger.info(msg)
            
            logger.info(f"Current open positions: {len(self.positions[self.positions['is_open']])}")
            
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}", exc_info=True)
    
    def end_of_day_tasks(self):
        """End of day tasks - calculate and save P&L"""
        logger.info("🌙 Running end of day tasks...")
        
        try:
            # Force close any remaining open positions
            self.positions, messages = force_eod_exit(self.positions)
            for msg in messages:
                logger.info(msg)
            
            # Calculate and save daily P&L
            total_pnl = calculate_and_save_daily_pnl()
            logger.info(f"💰 Daily P&L saved: ₹{total_pnl:.2f}")
            
            # Reset watchlist for next day (not strictly necessary with date check, but good for cleanup)
            # self.last_generation_date will be updated when generate_daily_watchlist runs tomorrow
            
        except Exception as e:
            logger.error(f"❌ Error in EOD tasks: {e}", exc_info=True)
    
    def start(self):
        """Start the autonomous trading bot"""
        logger.info("🚀 Starting Autonomous Trading Bot...")
        
        self.initialize()
        self.is_running = True
        
        # ALWAYS check/generate watchlist on startup
        # This ensures DB is populated even if bot is restarted or started late
        logger.info("Bot started, checking watchlist status...")
        self.generate_daily_watchlist()
        
        # Schedule tasks
        schedule.every().day.at("09:15").do(self.generate_daily_watchlist)
        schedule.every(30).seconds.do(self.monitor_and_trade)
        schedule.every().day.at("15:20").do(self.end_of_day_tasks)
        
        logger.info("📅 Scheduled tasks:")
        logger.info("  - Generate watchlist: Daily at 9:15 AM")
        logger.info("  - Monitor & trade: Every 30 seconds")
        logger.info("  - EOD tasks: Daily at 3:20 PM")
        
        # Main loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping bot (KeyboardInterrupt)...")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            self.is_running = False
    
    def stop(self):
        """Stop the bot"""
        logger.info("Stopping trading bot...")
        self.is_running = False


def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("AUTONOMOUS TRADING BOT")
    logger.info("=" * 80)
    
    bot = TradingBot()
    
    try:
        bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Trading bot shutdown complete")


if __name__ == "__main__":
    main()

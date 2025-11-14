# 📈 DailyTrader - Autonomous NSE Stock Trading System

An automated paper trading system for NSE stocks that runs autonomously as a background service with an optional Streamlit dashboard for monitoring.

## 🌟 Features

- **Autonomous Trading**: Runs as a Windows Service, no manual intervention needed
- **Cloud Database**: Uses Supabase PostgreSQL for reliable data storage
- **Momentum Strategy**: Trades stocks with >5% price increase and 5x volume
- **Risk Management**: 
  - Stop loss at -2%
  - Trailing stop at 10% from peak profit
  - EOD exit at 3:15 PM
- **Entry Control**: Only enters after 9:20 AM when price > previous day high
- **Monitoring Dashboard**: Optional Streamlit UI for real-time monitoring
- **Historical Analysis**: View trades by date with P&L metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Supabase Cloud                      │
│              (PostgreSQL Database)                   │
└────────────────┬────────────────────────────────────┘
                 │
                 │ (Both connect to same DB)
                 │
      ┌──────────┴───────────┐
      │                      │
      ▼                      ▼
┌─────────────┐      ┌──────────────┐
│ Autonomous  │      │  Streamlit   │
│ Trading Bot │      │  Dashboard   │
│  (Service)  │      │  (Optional)  │
└─────────────┘      └──────────────┘
```

## 📁 Project Structure

```
DailyTrader/
├── config.py                  # Configuration loader
├── trading_engine.py          # Core trading logic
├── autonomous_trader.py       # Background service
├── app.py                     # Streamlit dashboard
├── service_installer.py       # Windows service installer
├── .env.example              # Environment template
├── .env                      # Your credentials (gitignored)
├── requirements.txt          # Python dependencies
├── DEPLOYMENT_GUIDE.md       # Detailed setup instructions
├── setup.ps1                 # Quick setup script
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (free tier works)
- Windows OS (for service installation)

### Setup (5 minutes)

1. **Clone/Download this repository**

2. **Run the setup script**:
```powershell
.\setup.ps1
```

3. **Follow the prompts** to:
   - Create virtual environment
   - Install dependencies
   - Configure Supabase credentials
   - Test connection

For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## 🔧 Configuration

Edit `.env` file with your Supabase credentials:

```env
SUPABASE_HOST=db.xxxxx.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-password
SUPABASE_PORT=5432

# Optional trading config
CAPITAL_PER_TRADE=10000
PRICE_CHANGE_THRESHOLD=5.0
VOLUME_RATIO_THRESHOLD=5.0
```

## 📊 Usage

### Run Autonomous Bot (Background Service)

```powershell
# Run manually for testing
python autonomous_trader.py

# Or install as Windows Service (see DEPLOYMENT_GUIDE.md)
nssm install DailyTradingBot
nssm start DailyTradingBot
```

### Run Streamlit Dashboard

```powershell
streamlit run app.py
```

Dashboard features:
- Live positions monitoring
- P&L tracking (daily, weekly, monthly, yearly)
- Historical trades viewer with date filter
- Account summary with cumulative returns

## 🎯 Trading Logic

### Entry Conditions (ALL must be met)
1. Time > 9:20 AM (no entries in first 5 minutes)
2. Current price > Previous day's high
3. Price change > 5% from previous day
4. Volume > 5x previous day's volume

### Exit Conditions (ANY triggers exit)
1. **Stop Loss**: -2% from entry
2. **Trailing Stop**: 10% drawdown from peak profit
3. **EOD Exit**: 3:15 PM (all positions closed)

## 📅 Daily Schedule

The autonomous bot follows this schedule:

| Time     | Action                           |
|----------|----------------------------------|
| 9:15 AM  | Generate watchlist from bhavcopy |
| 9:20 AM+ | Start taking positions           |
| Ongoing  | Monitor every 30 seconds         |
| 3:15 PM  | Force close all positions        |
| 3:20 PM  | Calculate & save daily P&L       |

## 🗄️ Database Schema

### `trades` table
- Track individual trades
- Entry/exit prices, quantities, P&L
- Exit reasons (Stop Loss, Trailing Stop, EOD)

### `daily_pnl` table
- Aggregated daily P&L
- Historical performance tracking

## 📈 Monitoring

### View Logs
```powershell
# Application logs
Get-Content .\logs\trading_bot.log -Tail 50 -Wait

# Service logs (if installed as service)
Get-Content .\logs\service_output.log -Tail 50 -Wait
```

### Check Service Status
```powershell
nssm status DailyTradingBot
Get-Service DailyTradingBot
```

## 🛠️ Maintenance

### Update Code
```powershell
git pull
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade
nssm restart DailyTradingBot
```

### Backup Database
Supabase automatically backs up daily. Manual backup:
- Supabase Dashboard → Database → Export

### View Performance
- Use Streamlit dashboard
- Query Supabase directly via SQL Editor
- Check daily_pnl table for historical performance

## 🔒 Security

- ✅ Environment variables in `.env` (gitignored)
- ✅ Supabase RLS (Row Level Security) enabled
- ✅ No hardcoded credentials
- ✅ Secure connection to PostgreSQL

## 🐛 Troubleshooting

### Bot not trading?
1. Check logs: `Get-Content .\logs\trading_bot.log -Tail 50`
2. Verify market hours (9:15 AM - 3:30 PM IST)
3. Check watchlist generation succeeded
4. Ensure Supabase connection works

### Database errors?
1. Verify `.env` credentials
2. Test: `python trading_engine.py`
3. Check Supabase project status

### Service won't start?
1. Check Windows Event Viewer
2. Test manually: `python autonomous_trader.py`
3. Verify paths in NSSM service config

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[.env.example](.env.example)** - Environment variables template
- **Code comments** - Detailed inline documentation

## ⚠️ Disclaimer

This is a **paper trading** system for educational purposes only. No real money is involved. Always test thoroughly before considering any real trading implementation.

## 📝 License

MIT License - Feel free to modify and use for your needs.

---

**Happy Trading! 🚀**
- Open: 09:15
- Close: 15:30

## License
MIT

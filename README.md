# 📈 DailyTrader - Autonomous NSE Stock Trading System

An automated paper trading system for NSE stocks that runs autonomously on Railway.app with a Streamlit Cloud dashboard for monitoring.

## 🌟 Features

- **Fully Cloud-Based**: Runs 24/7 on Railway.app, no local hosting needed
- **Cloud Database**: Uses Supabase PostgreSQL for reliable data storage
- **Real-time Dashboard**: Streamlit Cloud for monitoring from anywhere
- **Momentum Strategy**: Trades stocks with >5% price increase and 5x volume
- **Risk Management**: 
  - Stop loss at -2%
  - Trailing stop at 10% from peak profit
  - EOD exit at 3:20 PM
- **Entry Control**: Only enters after 9:20 AM when price > previous day high
- **Historical Analysis**: View trades by date with P&L metrics
- **Cost-Effective**: ~$5/month (first month FREE with Railway credit!)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│             Supabase PostgreSQL (FREE)               │
│              - trades table                          │
│              - daily_pnl table                       │
└────────────────┬────────────────────────────────────┘
                 │
                 │ (Both connect via environment vars)
                 │
      ┌──────────┴───────────┐
      │                      │
      ▼                      ▼
┌─────────────┐      ┌──────────────────┐
│ Railway.app │      │ Streamlit Cloud  │
│ ($5/month)  │      │    (FREE)        │
│             │      │                  │
│ autonomous_ │      │    app.py        │
│ trader.py   │      │  - Monitor       │
│             │      │  - Analytics     │
│ Runs 24/7   │      │  - P&L           │
└─────────────┘      └──────────────────┘
```

## 📁 Project Structure

```
DailyTrader/
├── config.py                    # Configuration loader
├── trading_engine.py            # Core trading logic & DB functions
├── autonomous_trader.py         # Background trading bot
├── app.py                       # Streamlit dashboard
├── Procfile                     # Railway deployment config
├── railway.json                 # Railway settings
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── RAILWAY_DEPLOYMENT_GUIDE.md  # Complete setup guide
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites

- GitHub account (for deployment)
- Railway.app account (sign up for $5 free credit)
- Supabase account (free tier)
- Git installed locally

### Deployment (30 minutes)

Follow the comprehensive guide: **[RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md)**

**Quick overview:**
1. Create Supabase database → Get credentials
2. Push code to GitHub
3. Deploy to Railway.app → Set environment variables
4. Deploy dashboard to Streamlit Cloud → Configure secrets
5. Done! Monitor at `https://yourapp.streamlit.app`

## 🔧 Configuration

### Environment Variables (Railway.app & Streamlit Cloud)

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

**For Railway:** Set in Variables tab
**For Streamlit:** Set in Secrets (TOML format)

## 📊 Usage

### Monitor Your Bot

**Streamlit Dashboard** (Recommended)
- Open: `https://yourapp.streamlit.app`
- Features:
  - Live positions monitoring
  - P&L tracking (daily, weekly, monthly, yearly)
  - Historical trades viewer with date filter
  - Account summary with cumulative returns
  - Real-time updates from Supabase

**Railway Logs**
```
1. Go to railway.app
2. Click your project
3. Click "View Logs"
4. See real-time bot activity
```

**Local Testing** (before deploying)
```powershell
# Create .env file with Supabase credentials
python autonomous_trader.py
```

## 🎯 Trading Logic

### Entry Conditions (ALL must be met)
1. Time > 9:20 AM (no entries in first 5 minutes)
2. Current price > Previous day's high
3. Price change > 5% from previous day
4. Volume > 5x previous day's volume

### Exit Conditions (ANY triggers exit)
1. **Stop Loss**: -2% from entry
2. **Trailing Stop**: 10% drawdown from peak profit
3. **EOD Exit**: 3:20 PM (all positions closed)

## 📅 Daily Schedule

The autonomous bot follows this schedule (all times IST):

| Time     | Action                           |
|----------|----------------------------------|
| 9:15 AM  | Generate watchlist from bhavcopy |
| 9:20 AM+ | Start taking positions           |
| Ongoing  | Monitor every 30 seconds         |
| 3:20 PM  | Force close all positions        |
| 3:25 PM  | Calculate & save daily P&L       |

Bot runs 24/7 on Railway but only trades during market hours (Mon-Fri, 9:15 AM - 3:30 PM IST)

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
# Local changes
git add .
git commit -m "Update trading logic"
git push

# Railway automatically redeploys! 🚀
```

### Monitor Costs
- **Railway:** Check usage at railway.app/account
- **Supabase:** Monitor storage in dashboard (500 MB free)
- **Streamlit:** Completely free, no limits on community tier

### View Performance
- **Streamlit Dashboard:** Full analytics and charts
- **Supabase Table Editor:** Raw data view
- **Railway Metrics:** CPU/Memory usage

### Backup Database
Supabase automatically backs up daily. Manual backup:
- Supabase Dashboard → Database → Backups
- Or export via SQL Editor

## 🔒 Security

- ✅ Environment variables (Railway Variables & Streamlit Secrets)
- ✅ No credentials in code or GitHub
- ✅ Supabase connection encryption (SSL)
- ✅ `.env` and credentials gitignored

## 🐛 Troubleshooting

### Bot not trading?
1. **Check Railway logs:** railway.app → Your Project → View Logs
2. **Verify market hours:** 9:15 AM - 3:30 PM IST, Mon-Fri
3. **Check environment variables:** Railway → Variables tab
4. **Test database:** Supabase → Table Editor (should have trades)

### Database connection errors?
1. **Verify credentials:** Railway Variables match Supabase exactly
2. **Check Supabase status:** Dashboard should show "Healthy"
3. **Port number:** Should be `5432` (number, not string)
4. **Host format:** No `http://` prefix, just `db.xxx.supabase.co`

### Streamlit not updating?
1. **Check secrets:** Streamlit Cloud → Settings → Secrets
2. **Reboot app:** Settings → Reboot
3. **Verify Supabase data:** Should have recent trades
4. **Check logs:** Streamlit Cloud → Manage app → Logs

### Railway deployment failed?
1. **Check build logs:** Railway → Deployments → Click failed build
2. **Verify Procfile:** Should contain `worker: python autonomous_trader.py`
3. **Check requirements.txt:** All dependencies listed
4. **Redeploy:** Settings → Redeploy

See **[RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md)** for detailed troubleshooting.

## 💰 Cost Summary

| Service | Cost |
|---------|------|
| Railway.app | $5/month (1st month FREE) |
| Supabase | FREE (500 MB) |
| Streamlit Cloud | FREE (unlimited) |
| **Total** | **$5/month** |

**First month is FREE!** Railway gives you $5 credit on signup.

## 📚 Documentation

- **[RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md)** - Complete cloud deployment guide
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

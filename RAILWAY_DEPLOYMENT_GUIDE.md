# 🚀 Railway.app Deployment Guide
## Deploy DailyTrader on Railway + Streamlit Cloud

---

## 📋 **Overview**

This guide will help you deploy:
- **Railway.app** - Autonomous trading bot ($5/month with $5 free credit = FREE first month!)
- **Streamlit Cloud** - Monitoring dashboard (Free forever)
- **Supabase PostgreSQL** - Shared database (Free tier)

**Cost: $0 first month, then ~$5/month** 💰

---

## 🗄️ **Part 1: Setup Supabase Database** (15 minutes)

### Step 1: Create Supabase Project

1. Go to **[supabase.com](https://supabase.com)** → Sign in/Sign up
2. Click **"New Project"**
3. Fill in details:
   - **Organization**: Your organization
   - **Project Name**: `DailyTrader`
   - **Database Password**: Create a strong password (SAVE THIS!)
   - **Region**: Choose closest to you (Singapore for Asia, US East for Americas)
   - **Pricing Plan**: Free
4. Click **"Create new project"**
5. Wait 2-3 minutes for provisioning

### Step 2: Get Database Credentials

1. In Supabase dashboard, click **"Settings"** (gear icon)
2. Click **"Database"**
3. Scroll to **"Connection Info"** section
4. Note these values:
   ```
   Host: db.xxxxxxxxxxxxx.supabase.co
   Database name: postgres
   Port: 5432
   User: postgres
   Password: [your password from step 1]
   ```

### Step 3: Create Database Tables

1. Click **"SQL Editor"** in left sidebar
2. Click **"+ New query"**
3. Paste this SQL:

```sql
-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    entry_price DECIMAL(10, 2) NOT NULL,
    qty INTEGER NOT NULL,
    max_profit_pct DECIMAL(10, 2) DEFAULT 0,
    is_open BOOLEAN DEFAULT TRUE,
    exit_reason TEXT,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    exit_price DECIMAL(10, 2),
    pnl_pct DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create daily_pnl table
CREATE TABLE IF NOT EXISTS daily_pnl (
    date DATE PRIMARY KEY,
    total_pnl DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_is_open ON trades(is_open);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_daily_pnl_date ON daily_pnl(date DESC);

-- Verify tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

4. Click **"Run"** or press **F5**
5. Verify you see: `daily_pnl`, `trades` in results

✅ **Supabase setup complete!**

---

## 🚂 **Part 2: Deploy Bot to Railway.app** (20 minutes)

### Step 1: Create Railway Account

1. Go to **[railway.app](https://railway.app)**
2. Click **"Login"** → Sign up with **GitHub**
3. Authorize Railway to access your GitHub
4. You'll get **$5 free credit** (enough for first month!)

### Step 2: Prepare Your Code

On your local machine:

```powershell
# Navigate to project folder
cd "C:\Users\srira\Documents\ProjectDragon\python programs\DailyTrader"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"
```

### Step 3: Push to GitHub

```powershell
# Create new repository on GitHub (github.com):
# 1. Go to github.com → Click "+" → "New repository"
# 2. Name: DailyTrader
# 3. Make it Public or Private
# 4. Don't initialize with README
# 5. Click "Create repository"

# Link local repo to GitHub (replace with your URL)
git remote add origin https://github.com/yourusername/DailyTrader.git

# Push code
git branch -M main
git push -u origin main
```

### Step 4: Deploy to Railway

1. Go to **[railway.app/new](https://railway.app/new)**
2. Click **"Deploy from GitHub repo"**
3. Click **"Configure GitHub App"** (if first time)
4. Select your **DailyTrader** repository
5. Click **"Deploy Now"**

Railway will automatically detect Python and start deployment!

### Step 5: Configure Environment Variables

1. In Railway dashboard, click on your deployed service
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. Add these variables (one by one):

```
SUPABASE_HOST=db.xxxxxxxxxxxxx.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-supabase-password-here
SUPABASE_PORT=5432
CAPITAL_PER_TRADE=10000
PRICE_CHANGE_THRESHOLD=5.0
VOLUME_RATIO_THRESHOLD=5.0
```

5. Click **"Deploy"** after adding all variables

### Step 6: Verify Deployment

1. Click **"Deployments"** tab
2. Wait for build to complete (2-3 minutes)
3. Status should show **"SUCCESS"** with green checkmark
4. Click **"View Logs"** to see bot activity

✅ **Railway deployment complete!**

---

## 📊 **Part 3: Deploy Streamlit Dashboard** (15 minutes)

### Step 1: Verify Code is on GitHub

Your code should already be on GitHub from Part 2, Step 3. If not:

```powershell
cd "C:\Users\srira\Documents\ProjectDragon\python programs\DailyTrader"
git add .
git commit -m "Add Streamlit dashboard"
git push
```

### Step 2: Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **"New app"**
3. Fill in details:
   - **Repository**: Select `yourusername/DailyTrader`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Choose custom subdomain (e.g., `dailytrader`)

4. Click **"Advanced settings"**
5. Set **Python version**: `3.11`
6. In **"Secrets"** section, paste:

```toml
# .streamlit/secrets.toml format
SUPABASE_HOST = "db.xxxxxxxxxxxxx.supabase.co"
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "your-supabase-password"
SUPABASE_PORT = "5432"
```

7. Click **"Deploy!"**
8. Wait 3-5 minutes for deployment
9. Your app will be live at: `https://dailytrader.streamlit.app`

✅ **Streamlit dashboard deployed!**

---

## ✅ **Part 4: Verification & Testing** (10 minutes)

### Test Complete System

1. **Check Railway bot is running:**
   - Go to Railway dashboard → Your project
   - Click **"View Logs"**
   - Should see logs like:
     ```
     Trading bot initialized
     Market is CLOSED (Current time: ...)
     Next check at: ...
     ```

2. **Verify Supabase has data:**
   - Go to Supabase dashboard
   - Click **"Table Editor"**
   - Check `trades` and `daily_pnl` tables
   - Should see data if bot ran during market hours (9:15 AM - 3:30 PM IST)

3. **Test Streamlit Dashboard:**
   - Open your Streamlit Cloud URL
   - Should load and show:
     - Connected to Supabase ✓
     - Positions (if market hours)
     - Historical trades
     - P&L summaries

4. **Test End-to-End:**
   - Railway bot takes trade → Writes to Supabase
   - Streamlit refreshes → Shows trade from Supabase
   - Both see same data! 🎉

---

## 💰 **Cost Breakdown**

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| **Supabase** | Free Tier | $0 |
| **Railway.app** | Hobby Plan | $5 |
| **Streamlit Cloud** | Community (Free) | $0 |
| **Total** | | **$5/month** 💵 |

### Free Credits & Limits:

**Railway.app:**
- $5 free credit on signup (covers first month!)
- After that: $5/month for Hobby plan
- Includes: 512 MB RAM, shared CPU
- No sleep/downtime - runs 24/7

**Supabase (Free Tier):**
- 500 MB database space
- 2 GB bandwidth
- 50 MB file storage
- No credit card required

**Streamlit Cloud (Community):**
- 1 GB resources per app
- Unlimited public apps
- Free forever

---

## 📱 **Daily Operations**

### Morning (9:00 AM IST):
- Bot automatically wakes up at 9:15 AM
- Generates watchlist
- Starts monitoring

### During Market Hours:
- Monitor via Streamlit dashboard: `https://yourapp.streamlit.app`
- Check positions in real-time
- View P&L updates

### After Market Close (3:30 PM IST):
- Bot automatically closes all positions at 3:20 PM
- Calculates daily P&L
- Saves to Supabase

### Anytime - Check Railway Logs:
1. Go to [railway.app](https://railway.app)
2. Click on your project
3. Click **"View Logs"**
4. See real-time bot activity

---

## 🔧 **Maintenance**

### Update Code:

**Method 1: Via Git (Recommended)**
```powershell
# Make changes to your code locally
# Then commit and push
cd "C:\Users\srira\Documents\ProjectDragon\python programs\DailyTrader"
git add .
git commit -m "Update trading logic"
git push
```
Railway will automatically detect the push and redeploy! 🚀

**Method 2: Via Railway Dashboard**
1. Go to Railway dashboard
2. Click **"Deployments"**
3. Click **"Redeploy"** on latest deployment

### Restart Service:

1. Go to Railway dashboard
2. Click on your service
3. Click **"Settings"** tab
4. Scroll to bottom
5. Click **"Restart"**

### View Logs:

```
# Real-time logs
Railway Dashboard → Your Project → View Logs

# Filter logs
Click "Filter" → Select log level (Info, Warning, Error)

# Download logs
Click "..." → "Download Logs"
```

### Monitor Resource Usage:

1. Railway Dashboard → Your Project
2. Click **"Metrics"** tab
3. See:
   - CPU usage
   - Memory usage
   - Network traffic
   - Deployment status

---

## 🐛 **Troubleshooting**

### Bot not starting:

**Check Railway Logs:**
1. Railway Dashboard → View Logs
2. Look for errors like:
   - `ModuleNotFoundError` → Missing dependency in requirements.txt
   - `Connection refused` → Database credentials wrong
   - `Syntax error` → Code error

**Fix:**
```powershell
# Fix locally, then push
git add .
git commit -m "Fix deployment issue"
git push
# Railway auto-redeploys
```

### Database connection errors:

**Test credentials:**
1. Check Railway variables are exactly matching Supabase
2. Verify SUPABASE_HOST doesn't have `http://` or `https://`
3. Check SUPABASE_PORT is `5432` (number, not string)

**Fix in Railway:**
1. Railway Dashboard → Variables tab
2. Edit wrong variable
3. Click "Deploy" to restart with new values

### Streamlit not showing data:

1. **Check Secrets:** Streamlit Cloud → Settings → Secrets
   - Must match Railway variables exactly
2. **Check Supabase:** Table Editor → Should have data
3. **Restart app:** Settings → Reboot app
4. **Check logs:** Streamlit Cloud → Manage app → View logs

### Railway deployment failed:

**Common issues:**

1. **Build failed:**
   - Check `requirements.txt` has all dependencies
   - Check Python version compatibility

2. **Start command not found:**
   - Verify `Procfile` exists
   - Check `Procfile` has correct command

3. **Out of memory:**
   - Railway Hobby plan has 512 MB RAM
   - Optimize code or upgrade plan

**Fix:**
```powershell
# Update requirements.txt or Procfile
git add .
git commit -m "Fix deployment"
git push
```

### Bot running but not trading:

**Check:**
1. **Time:** Bot only runs during market hours (9:15 AM - 3:30 PM IST)
2. **Day:** Monday-Friday only (no weekends/holidays)
3. **Watchlist:** Railway logs → Should show watchlist generation
4. **Positions:** Supabase → Check `trades` table

**Manual test:**
1. Railway Dashboard → View Logs
2. Look for: `"Generated watchlist with X symbols"`
3. Look for: `"Monitoring X positions"`

---

## 🔄 **How It All Works Together**

```
┌─────────────────────────────────────────┐
│    Supabase PostgreSQL (Free)           │
│    - trades table                       │
│    - daily_pnl table                    │
│    - Real-time data sync                │
└────────────┬────────────────────────────┘
             │
             │ Both connect via environment variables
             │
  ┌──────────┴────────────┐
  │                       │
  ▼                       ▼
┌────────────────┐  ┌──────────────────┐
│ Railway.app    │  │ Streamlit Cloud  │
│ ($5/month)     │  │ (FREE)           │
│                │  │                  │
│ autonomous_    │  │   app.py         │
│ trader.py      │  │                  │
│                │  │ - View positions │
│ - Runs 24/7    │  │ - Monitor P&L    │
│ - Never sleeps │  │ - See trades     │
│ - Auto-trades  │  │ - Analytics      │
│ - Logs visible │  │                  │
│                │  │ Public URL:      │
│ GitHub →       │  │ *.streamlit.app  │
│ Auto-deploys   │  │                  │
└────────────────┘  └──────────────────┘
```

### Deployment Flow:
1. **You push code** to GitHub
2. **Railway detects** push → Auto-builds → Auto-deploys
3. **Bot runs** on Railway 24/7
4. **Streamlit** pulls from same GitHub repo
5. **Both connect** to Supabase for data sync

---

## 🎯 **Success Checklist**

- [ ] Supabase project created
- [ ] Database tables created (trades, daily_pnl)
- [ ] Railway account created ($5 free credit)
- [ ] Code pushed to GitHub
- [ ] Railway connected to GitHub repo
- [ ] Environment variables set in Railway
- [ ] Railway deployment successful (green checkmark)
- [ ] Railway logs showing bot activity
- [ ] Streamlit app deployed to Streamlit Cloud
- [ ] Secrets configured in Streamlit Cloud
- [ ] Dashboard accessible via public URL
- [ ] Dashboard showing data from Supabase
- [ ] End-to-end test: Bot → Supabase → Dashboard ✓

---

## 🚀 **You're Live!**

Your autonomous trading system is now running in the cloud:
- ✅ Bot runs 24/7 on Railway.app
- ✅ Dashboard accessible from anywhere
- ✅ All data synced via Supabase
- ✅ Only $5/month (first month FREE!)

**Monitor your bot:** `https://yourapp.streamlit.app`
**Check logs:** [railway.app/dashboard](https://railway.app/dashboard)

**Pro Tips:**
- 💡 Check Railway logs daily for any errors
- 💡 Monitor Supabase usage (free tier = 500 MB)
- 💡 Set up Railway alerts for deployment failures
- 💡 Pin Streamlit dashboard for quick access

Happy Trading! 📈🚀

---

## 📚 **Additional Resources**

- [Railway Documentation](https://docs.railway.app)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Supabase Docs](https://supabase.com/docs)
- [Python Schedule Library](https://schedule.readthedocs.io)

---

## ❓ **FAQ**

**Q: What happens if Railway runs out of credit?**
A: Bot will stop. Add $5 credit to continue. You'll get email notification before it stops.

**Q: Can I see live trades in dashboard?**
A: Yes! Streamlit refreshes every few seconds. You'll see trades appear in real-time.

**Q: What if bot crashes?**
A: Railway auto-restarts failed services. Check logs to debug the issue.

**Q: Can I run multiple strategies?**
A: Yes! Deploy multiple Railway services, each with different config. All can use same Supabase.

**Q: How do I stop the bot temporarily?**
A: Railway Dashboard → Settings → Click "Remove Service" (or pause in settings)

**Q: Can I upgrade if I need more resources?**
A: Yes! Railway has Pro plan with more RAM/CPU. Upgrade anytime in billing settings.

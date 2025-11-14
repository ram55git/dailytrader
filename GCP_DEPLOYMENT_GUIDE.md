# 🚀 Google Cloud Platform Deployment Guide
## Deploy DailyTrader on GCP Compute Engine Free Tier + Streamlit Cloud

---

## 📋 **Overview**

This guide will help you deploy:
- **Google Compute Engine (e2-micro)** - Autonomous trading bot ($0/month with free tier)
- **Streamlit Cloud** - Monitoring dashboard (Free)
- **Supabase PostgreSQL** - Shared database (Free tier)

**Total Cost: $0/month** 🎉

---

## 🗄️ **Part 1: Setup Supabase Database** (15 minutes)

### Step 1: Create Supabase Project

1. Go to **[supabase.com](https://supabase.com)** → Sign in/Sign up
2. Click **"New Project"**
3. Fill in details:
   - **Organization**: Your organization
   - **Project Name**: `DailyTrader`
   - **Database Password**: Create a strong password (SAVE THIS!)
   - **Region**: Choose closest to India (Singapore recommended)
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

## ☁️ **Part 2: Create Google Cloud Compute Engine VM** (20 minutes)

### Step 1: Create Google Cloud Account

1. Go to **[cloud.google.com](https://cloud.google.com)**
2. Click **"Get started for free"**
3. Sign in with Google account
4. Complete billing setup (credit card required, but won't be charged for free tier)
5. $300 free credits for 90 days + Always Free tier

### Step 2: Create VM Instance

1. Go to **[console.cloud.google.com](https://console.cloud.google.com)**
2. Click **☰ Menu** → **Compute Engine** → **VM instances**
3. Click **"Create Instance"**

4. Configure instance:

   **Basic Configuration:**
   ```
   Name: trading-bot
   Region: us-west1 (Oregon) - FREE TIER REGION ⭐
     or us-central1 (Iowa)
     or us-east1 (South Carolina)
   Zone: Any zone in above regions (e.g., us-west1-b)
   ```

   **Machine Configuration:**
   ```
   Series: E2
   Machine type: e2-micro (2 vCPU, 1 GB memory) - FREE TIER ⭐
   ```

   **Boot Disk:**
   ```
   Click "Change"
   Operating System: Ubuntu
   Version: Ubuntu 22.04 LTS
   Boot disk type: Standard persistent disk - FREE TIER ⭐
   Size: 30 GB (maximum for free tier)
   Click "Select"
   ```

   **Firewall:**
   ```
   ☐ Allow HTTP traffic (NOT needed)
   ☐ Allow HTTPS traffic (NOT needed)
   ```

5. Click **"Create"**
6. Wait 1-2 minutes for VM to start

### Step 3: Connect to VM

1. In VM instances list, find your **trading-bot** VM
2. Click **"SSH"** button (opens web-based terminal)
3. Wait for connection to establish

✅ **VM created and connected!**

---

## 🔧 **Part 3: Setup Trading Bot on VM** (25 minutes)

### Step 1: Update System

```bash
# Update package list
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y
```

### Step 2: Install Python and Dependencies

```bash
# Install Python 3, pip, venv, and git
sudo apt install python3 python3-pip python3-venv git -y

# Verify installation
python3 --version  # Should show Python 3.10+
pip3 --version
```

### Step 3: Clone Your Repository

**Option A: Using Git (if code is on GitHub)**
```bash
# Clone repository
git clone https://github.com/yourusername/DailyTrader.git
cd DailyTrader
```

**Option B: Upload files manually**
```bash
# Create directory
mkdir -p ~/DailyTrader
cd ~/DailyTrader

# Upload files using GCP Console:
# 1. Click gear icon in SSH window → "Upload file"
# 2. Upload these files:
#    - autonomous_trader.py
#    - trading_engine.py
#    - config.py
#    - requirements.txt
#    - .env.example
```

### Step 4: Setup Python Environment

```bash
# Make sure you're in DailyTrader directory
cd ~/DailyTrader

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)

# Install dependencies
pip install -r requirements.txt

# This will take 2-3 minutes
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Paste this content (replace with your Supabase credentials):
```env
SUPABASE_HOST=db.xxxxxxxxxxxxx.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-supabase-password-here
SUPABASE_PORT=5432

# Trading configuration (optional)
CAPITAL_PER_TRADE=10000
PRICE_CHANGE_THRESHOLD=5.0
VOLUME_RATIO_THRESHOLD=5.0
```

**To save and exit nano:**
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

### Step 6: Test the Bot

```bash
# Still in virtual environment
# Test database connection
python3 trading_engine.py

# Should see:
# Testing database connection...
# Database initialized successfully
# ✅ Database connection successful!

# Test bot (run for 30 seconds then Ctrl+C)
python3 autonomous_trader.py

# Press Ctrl+C to stop

# Check if log file was created
ls -la trading_bot.log
```

✅ **Bot tested successfully!**

---

## 🔄 **Part 4: Run Bot as Background Service** (15 minutes)

### Step 1: Create Systemd Service File

```bash
# Create service file
sudo nano /etc/systemd/system/trading-bot.service
```

Paste this content:
```ini
[Unit]
Description=Autonomous Trading Bot for NSE Stocks
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/DailyTrader
Environment="PATH=/home/your-username/DailyTrader/venv/bin"
ExecStart=/home/your-username/DailyTrader/venv/bin/python autonomous_trader.py
Restart=always
RestartSec=10
StandardOutput=append:/home/your-username/DailyTrader/logs/service.log
StandardError=append:/home/your-username/DailyTrader/logs/service.error.log

[Install]
WantedBy=multi-user.target
```

**⚠️ Important: Replace `your-username` with your actual username!**

To find your username:
```bash
whoami
# Use this output to replace "your-username" above
```

**Save and exit:**
- `Ctrl + X` → `Y` → `Enter`

### Step 2: Create Logs Directory

```bash
# Create logs directory
mkdir -p ~/DailyTrader/logs
```

### Step 3: Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable trading-bot

# Start service now
sudo systemctl start trading-bot

# Check status
sudo systemctl status trading-bot

# Should show:
# ● trading-bot.service - Autonomous Trading Bot for NSE Stocks
#    Loaded: loaded
#    Active: active (running)
```

### Step 4: Monitor the Bot

```bash
# View application logs (live tail)
tail -f ~/DailyTrader/trading_bot.log

# View service logs
tail -f ~/DailyTrader/logs/service.log

# View system logs
sudo journalctl -u trading-bot -f

# Press Ctrl+C to stop tailing logs
```

### Service Management Commands

```bash
# Check status
sudo systemctl status trading-bot

# Stop service
sudo systemctl stop trading-bot

# Start service
sudo systemctl start trading-bot

# Restart service
sudo systemctl restart trading-bot

# View last 50 lines of logs
sudo journalctl -u trading-bot -n 50

# Follow logs in real-time
sudo journalctl -u trading-bot -f
```

✅ **Service running!**

---

## 📊 **Part 5: Deploy Streamlit Dashboard to Streamlit Cloud** (15 minutes)

### Step 1: Prepare Code for GitHub

On your local machine:

```powershell
# Navigate to project folder
cd "C:\Users\srira\Documents\ProjectDragon\python programs\DailyTrader"

# Make sure .gitignore exists and includes .env
# (Already created in previous steps)

# Initialize git (if not already)
git init

# Add files
git add .

# Commit
git commit -m "Add DailyTrader with Supabase integration"
```

### Step 2: Push to GitHub

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

### Step 3: Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **"New app"**
3. Fill in details:
   - **Repository**: Select `yourusername/DailyTrader`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Choose custom subdomain (e.g., `dailytrader`)

4. Click **"Advanced settings"**
5. In **"Secrets"** section, paste:

```toml
# .streamlit/secrets.toml format
SUPABASE_HOST = "db.xxxxxxxxxxxxx.supabase.co"
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "your-supabase-password"
SUPABASE_PORT = "5432"
```

6. Click **"Deploy!"**
7. Wait 3-5 minutes for deployment
8. Your app will be live at: `https://dailytrader.streamlit.app`

✅ **Streamlit dashboard deployed!**

---

## ✅ **Part 6: Verification & Testing** (10 minutes)

### Test Complete System

1. **Check GCP VM is running:**
   ```bash
   # SSH to VM
   sudo systemctl status trading-bot
   
   # Should show "active (running)"
   
   # Check logs
   tail -f ~/DailyTrader/trading_bot.log
   ```

2. **Verify Supabase has data:**
   - Go to Supabase dashboard
   - Click **"Table Editor"**
   - Check `trades` and `daily_pnl` tables
   - Should see data if bot ran during market hours

3. **Test Streamlit Dashboard:**
   - Open your Streamlit Cloud URL
   - Should load and show:
     - Connected to Supabase
     - Positions (if market hours)
     - Historical trades
     - P&L summaries

4. **Test End-to-End:**
   - Bot takes trade → Writes to Supabase
   - Streamlit refreshes → Shows trade from Supabase
   - Both see same data!

---

## 💰 **Cost Breakdown**

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| **Supabase** | Free Tier | $0 |
| **GCP Compute Engine** | e2-micro (Free Tier) | $0 |
| **Streamlit Cloud** | Community (Free) | $0 |
| **Total** | | **$0/month** 🎉 |

### Free Tier Limits:

**Google Cloud (Always Free):**
- 1 e2-micro VM instance/month
- 30 GB standard persistent disk
- 1 GB network egress/month (outbound data)

**Supabase (Free Tier):**
- 500 MB database space
- 2 GB bandwidth
- 50 MB file storage

**Streamlit Cloud (Community):**
- 1 GB resources per app
- Unlimited public apps

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
- Bot automatically closes all positions
- Calculates daily P&L
- Saves to Supabase

### Anytime:
```bash
# SSH to GCP VM
# Check bot status
sudo systemctl status trading-bot

# View logs
tail -f ~/DailyTrader/trading_bot.log

# Restart if needed
sudo systemctl restart trading-bot
```

---

## 🔧 **Maintenance**

### Update Code:

```bash
# SSH to VM
cd ~/DailyTrader

# Pull latest code
git pull

# Restart service
sudo systemctl restart trading-bot

# Check status
sudo systemctl status trading-bot
```

### Check Disk Usage:

```bash
# Check disk space (should be under 30GB for free tier)
df -h

# Check log file sizes
du -h ~/DailyTrader/logs/
du -h ~/DailyTrader/trading_bot.log

# Rotate logs if needed
sudo systemctl restart trading-bot
```

### Monitor VM Resources:

```bash
# Check memory usage
free -h

# Check CPU usage
top

# Press 'q' to exit top
```

---

## 🐛 **Troubleshooting**

### Bot not starting:

```bash
# Check service status
sudo systemctl status trading-bot

# View detailed logs
sudo journalctl -u trading-bot -n 100 --no-pager

# Check Python errors
tail -50 ~/DailyTrader/logs/service.error.log

# Test manually
cd ~/DailyTrader
source venv/bin/activate
python3 autonomous_trader.py
```

### Database connection errors:

```bash
# Test database connection
cd ~/DailyTrader
source venv/bin/activate
python3 trading_engine.py

# Verify .env file
cat .env  # Should show correct credentials

# Test Supabase from VM
python3 -c "from config import DB_CONFIG; print(DB_CONFIG)"
```

### Streamlit not showing data:

1. Check Secrets are set correctly in Streamlit Cloud
2. Check Supabase has data: Table Editor → trades
3. Restart Streamlit app: Settings → Reboot app
4. Check app logs in Streamlit Cloud

### VM exceeded free tier:

- Check region is `us-west1`, `us-central1`, or `us-east1`
- Check machine type is `e2-micro`
- Check disk size is ≤ 30 GB
- Only 1 VM allowed in free tier

---

## 📚 **Architecture Summary**

```
┌──────────────────────────────────────────┐
│     Supabase PostgreSQL (Free)           │
│     - trades table                       │
│     - daily_pnl table                    │
└────────────┬─────────────────────────────┘
             │
             │ Both connect via .env/secrets
             │
  ┌──────────┴──────────┐
  │                     │
  ▼                     ▼
┌──────────────┐  ┌──────────────────┐
│ GCP Compute  │  │ Streamlit Cloud  │
│ Engine       │  │                  │
│ (e2-micro)   │  │   app.py         │
│              │  │                  │
│ autonomous_  │  │ - Monitor trades │
│ trader.py    │  │ - View P&L       │
│              │  │ - Analytics      │
│ Runs 24/7    │  │                  │
│ as systemd   │  │ Public URL:      │
│ service      │  │ *.streamlit.app  │
└──────────────┘  └──────────────────┘
   $0/month          $0/month
```

---

## 🎯 **Success Checklist**

- [ ] Supabase project created
- [ ] Database tables created
- [ ] GCP account created
- [ ] e2-micro VM created in free tier region
- [ ] Bot code uploaded to VM
- [ ] Python environment setup
- [ ] .env configured with Supabase credentials
- [ ] Bot tested successfully
- [ ] Systemd service created and enabled
- [ ] Service running (`sudo systemctl status trading-bot`)
- [ ] Logs showing activity
- [ ] Code pushed to GitHub
- [ ] Streamlit app deployed to Streamlit Cloud
- [ ] Secrets configured in Streamlit Cloud
- [ ] Dashboard accessible via public URL
- [ ] Dashboard showing data from Supabase
- [ ] End-to-end test successful

---

## 🚀 **You're Live!**

Your autonomous trading system is now running:
- ✅ Bot runs 24/7 on Google Cloud (FREE)
- ✅ Dashboard accessible from anywhere
- ✅ All data synced via Supabase
- ✅ $0/month operational cost

**Monitor your bot:** `https://yourapp.streamlit.app`

**Questions or issues?**
- Check logs: `tail -f ~/DailyTrader/trading_bot.log`
- Check service: `sudo systemctl status trading-bot`
- Check Supabase: Table Editor in dashboard

Happy Trading! 📈🚀

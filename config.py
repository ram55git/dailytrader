"""
Configuration loader - Load environment variables from .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('SUPABASE_HOST'),
    'database': os.getenv('SUPABASE_DB', 'postgres'),
    'user': os.getenv('SUPABASE_USER', 'postgres'),
    'password': os.getenv('SUPABASE_PASSWORD'),
    'port': os.getenv('SUPABASE_PORT', '5432')
}

# Trading configuration
CAPITAL_PER_TRADE = float(os.getenv('CAPITAL_PER_TRADE', '10000'))
PRICE_CHANGE_THRESHOLD = float(os.getenv('PRICE_CHANGE_THRESHOLD', '5.0'))
VOLUME_RATIO_THRESHOLD = float(os.getenv('VOLUME_RATIO_THRESHOLD', '5.0'))


def validate_config():
    """Validate that all required configuration is present"""
    required_vars = ['SUPABASE_HOST', 'SUPABASE_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True


if __name__ == "__main__":
    print("Configuration loaded:")
    print(f"Database Host: {DB_CONFIG['host']}")
    print(f"Database Name: {DB_CONFIG['database']}")
    print(f"Database User: {DB_CONFIG['user']}")
    print(f"Database Port: {DB_CONFIG['port']}")
    print(f"\nTrading Config:")
    print(f"Capital per trade: ₹{CAPITAL_PER_TRADE:,.2f}")
    print(f"Price change threshold: {PRICE_CHANGE_THRESHOLD}%")
    print(f"Volume ratio threshold: {VOLUME_RATIO_THRESHOLD}x")
    
    try:
        validate_config()
        print("\n✅ Configuration is valid!")
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")

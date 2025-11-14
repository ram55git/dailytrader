"""
Configuration loader - Load environment variables from .env file or Streamlit secrets
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Try to load from Streamlit secrets first (when deployed on Streamlit Cloud)
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        # Running on Streamlit Cloud - use secrets
        DB_CONFIG = {
            'host': st.secrets.get('SUPABASE_HOST'),
            'database': st.secrets.get('SUPABASE_DB', 'postgres'),
            'user': st.secrets.get('SUPABASE_USER', 'postgres.lmthbkyiwtfbvjvtedjs'),
            'password': st.secrets.get('SUPABASE_PASSWORD'),
            'port': st.secrets.get('SUPABASE_PORT', '6543')
        }
        CAPITAL_PER_TRADE = float(st.secrets.get('CAPITAL_PER_TRADE', '10000'))
        PRICE_CHANGE_THRESHOLD = float(st.secrets.get('PRICE_CHANGE_THRESHOLD', '5.0'))
        VOLUME_RATIO_THRESHOLD = float(st.secrets.get('VOLUME_RATIO_THRESHOLD', '5.0'))
    else:
        raise ImportError("Streamlit secrets not available")
except (ImportError, FileNotFoundError):
    # Not running on Streamlit or secrets not configured - use .env file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    DB_CONFIG = {
        'host': os.getenv('SUPABASE_HOST'),
        'database': os.getenv('SUPABASE_DB', 'postgres'),
        'user': os.getenv('SUPABASE_USER', 'postgres'),
        'password': os.getenv('SUPABASE_PASSWORD'),
        'port': os.getenv('SUPABASE_PORT', '5432')
    }
    
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

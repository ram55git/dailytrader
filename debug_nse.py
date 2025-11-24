from nsepython import get_bhavcopy
import pandas as pd
from datetime import datetime, timedelta
import nselib

def last_two_trading_days(start_date):
    """Find the most recent previous trading day excluding weekends and holidays"""
    holiday_data = pd.DataFrame(nselib.trading_holiday_calendar())
    fil_holiday_data = holiday_data[holiday_data['Product'] == 'Equities']
    holidays_set = set(pd.to_datetime(fil_holiday_data['tradingDate'], format='%d-%b-%Y').dt.date)

    current_date = start_date - timedelta(days=1)
    while current_date.weekday() >= 5 or current_date in holidays_set:
        current_date -= timedelta(days=1)
    return current_date

trade_date_last = last_two_trading_days(datetime.now().date())
print(f"Fetching for {trade_date_last}")

data = get_bhavcopy(trade_date_last.strftime('%d-%m-%Y'))
df = pd.DataFrame(data)
print("Columns:", df.columns.tolist())
print("Dtypes:")
print(df.dtypes)

cols_to_check = [' CLOSE_PRICE', ' OPEN_PRICE', ' TTL_TRD_QNTY']
for col in cols_to_check:
    if col in df.columns:
        print(f"\nSample {col}:")
        print(df[col].head())
        print(f"Type of first element: {type(df[col].iloc[0])}")

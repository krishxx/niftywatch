from breeze_connect import BreezeConnect
import pandas as pd
import json
import pytz
import datetime as dt
import os, math, time
import re
import sys
import pickle
from datetime import datetime, timedelta

get_idx_for_date = '2025-07-07'
# get_idx_for_date = ''
symbol = 'NIFTY'
use_saved_session = False

# Accept command line arguments for date and symbol
if len(sys.argv) > 1:
    get_idx_for_date = sys.argv[1]
    print(f"Using date from command line: {get_idx_for_date}")
if len(sys.argv) > 2:
    symbol = sys.argv[2]
    print(f"Using symbol from command line: {symbol}")
if len(sys.argv) > 3 and sys.argv[3] == '--use-saved-session':
    use_saved_session = True
    print("Using saved session from server")

def load_session_from_file():
    """Load session object from file"""
    try:
        with open('session.pkl', 'rb') as f:
            isec = pickle.load(f)
        print("Session loaded from session.pkl")
        return isec
    except Exception as e:
        print(f"Failed to load session: {str(e)}")
        return None

session_key_inv = 0
session_key_raju = 52120565
session_key_swaran = 0
session_key_moses = 0
session_key_hada = 0


moses_account = '{"appKey" : "396C!u2213c1a3z2x743467h*G8^y&+7","apiSecret" : "77911&198C6!86bt72Io8tid27222789"}'
raju_account = '{"appKey" : "i87W5a354o436C172$1954914Uj1s54m","apiSecret" : "5B2M47139O29953437a)O37`91h6f3l2"}'
swaran_account = '{"appKey" : "F005#727V890J99965G632z9h9285q23","apiSecret" : "z26A3(w9C635&2F89402L24k420b6209"}'
hada_account = '{"appKey" : "054222`234~4mzP58=E1&X885V8C1624","apiSecret" : "9193^72G6R2a8~3897jbR2X9UH3C8568"}'

# login_dtls_dict = {"appKey" : config_icici.appKey,"apiSecret" :config_icici.apiSecret}
# inv_account = json.dumps(login_dtls_dict)

# use_account = json.loads(moses_account)
# session_key = session_key_moses

use_account = json.loads(raju_account)
session_key = session_key_raju

# use_account = json.loads(swaran_account)
# session_key = session_key_swaran

# use_account = json.loads(hada_account)
# session_key = session_key_hada

# use_account = json.loads(inv_account)
# session_key = session_key_inv

holidays_df =  pd.DataFrame({'holiday': 
                                ['26-01-2024','08-03-2024',
                                '25-03-2024','29-03-2024',
                                '11-04-2024','17-04-2024',
                                '01-05-2024','17-06-2024',
                                '17-07-2024','15-08-2024',
                                '02-10-2024','01-11-2024',
                                '15-11-2024','20-11-2024',
                                '25-12-2024','26-02-2025',
                                '14-03-2025','31-03-2025',
                                '10-04-2025','14-04-2025',
                                '18-04-2025','01-05-2025',
                                '15-08-2025','27-08-2025',
                                '02-10-2025','21-10-2025',
                                '22-10-2025','05-11-2025',
                                '25-12-2025'
                                ]})


def find_monthly_expiry(date_obj):
    year = date_obj.year
    month = date_obj.month
    day = date_obj.day

    last_day_of_month = dt.datetime(year, month, 1) + dt.timedelta(days=32)
    # print(f"\t1 - {last_day_of_month}, given-day={day}")
    # print(f"\tgiven-day={day}")
    last_day_of_month = last_day_of_month.replace(day=1) - dt.timedelta(days=1)
    # print(f"\t\tlast_day_of_month={last_day_of_month}")
    last_thursday = last_day_of_month - dt.timedelta(days=(last_day_of_month.weekday() -3) % 7)
    date_str = last_thursday.strftime('%d-%m-%Y')
    result = date_str in holidays_df['holiday'].values
    if result:
        last_thursday = last_thursday + dt.timedelta(days=-1)
        print(f"\t\t***Monthly expiry_date after considering Holiday = {last_thursday}")
        # logging.info(f"\t\t***Monthly expiry_date after considering Holiday = {last_thursday}")
    # print(f"\tlast_thursday={last_thursday}")
    if (last_thursday.day < day) :
        tmp_date =  last_day_of_month + dt.timedelta(days=1) 
        # last_thursday = find_monthly_expiry(tmp_date.year, tmp_date.month, tmp_date.day)
        last_thursday = find_monthly_expiry(tmp_date)
    return last_thursday

def find_monthly_expiry(date_obj, symbol = ''):
    year = date_obj.year
    month = date_obj.month
    day = date_obj.day

    last_day_of_month = dt.datetime(year, month, 1) + dt.timedelta(days=32)
    # print(f"\t1 - {last_day_of_month}, given-day={day}")
    # print(f"\tgiven-day={day}")
    last_day_of_month = last_day_of_month.replace(day=1) - dt.timedelta(days=1)
    # print(f"\t\tlast_day_of_month={last_day_of_month}")
    # last_thursday = last_day_of_month - dt.timedelta(days=(last_day_of_month.weekday() -3) % 7)
    month_exp_day = last_day_of_month - dt.timedelta(days=(last_day_of_month.weekday() -3) % 7)
    ## RAJU - commented after 2025
    # if symbol == 'CNXBAN': 
    #     last_thursday = last_day_of_month - dt.timedelta(days=(last_day_of_month.weekday() -2) % 7)
    ## RAJU - handle SENSEX
    if symbol == 'SENSEX': 
        # days_to_expiry = 1 - date.weekday() # tuesday
        month_exp_day = last_day_of_month - dt.timedelta(days=(last_day_of_month.weekday() -1) % 7)
    date_str = month_exp_day.strftime('%d-%m-%Y')
    result = date_str in holidays_df['holiday'].values
    if result:
        month_exp_day = month_exp_day + dt.timedelta(days=-1)
        print(f"\t\t***Monthly expiry_date after considering Holiday = {month_exp_day}")
        # logging.info(f"\t\t***Monthly expiry_date after considering Holiday = {month_exp_day}")
    # print(f"\tlast_thursday={last_thursday}")
    if (month_exp_day.day < day) :
        tmp_date =  last_day_of_month + dt.timedelta(days=1) 
        # last_thursday = find_monthly_expiry(tmp_date.year, tmp_date.month, tmp_date.day)
        month_exp_day = find_monthly_expiry(tmp_date, symbol)
    return month_exp_day

def is_nse_trading(in_date_str = ''):    
    """
    Returns True if the current time is within the Nifty trading hours on a weekday (Monday to Friday)
    and not a holiday, otherwise False.
    """
    global holidays_df

    if not (in_date_str == ''):        
        print(f"considering input-date={in_date_str}")
        date_obj = dt.datetime.strptime(in_date_str, '%Y-%m-%d')
        date_str = date_obj.strftime('%d-%m-%Y')
        if (date_str in holidays_df['holiday'].values):
            print(f"returning False as daet={in_date_str} is Holiday")
            return False
        
        dt_weekday = date_obj.weekday()
        if dt_weekday > 4:
            print(f"returning False as daet={in_date_str} is Week-end")
            return False
        else:
            return True

    timezone = pytz.timezone('Asia/Kolkata')
    current_time = dt.datetime.now(timezone).time()
    current_weekday = dt.datetime.now(timezone).weekday()
    nifty_start_time = dt.time(9, 15)
    nifty_end_time = dt.time(15, 30)

    current_date_obj = dt.datetime.today()
    current_date_str = current_date_obj.strftime('%d-%m-%Y')

    if current_date_str in holidays_df['holiday'].values:
        # print("you are here")
        # print(f"Its a holiday date={current_date_str}")
        return False

    if current_weekday < 5 and current_time >= nifty_start_time and current_time <= nifty_end_time:
        # current_date = dt.datetime.now(timezone).date().strftime()
        current_date = dt.datetime.now(timezone).date()
        current_date_str = current_date.strftime('%d-%m-%Y')

        # if current_date_str not in holidays['holiday']:
        if current_date_str not in holidays_df['holiday'].values:
            return True
    return False


def get_hist_data_breeze(isec, symbol, call_or_put , strike , date_str, exp_date_str, interval = '1minute'):

    # if can_use_yf and symbol != 'SENSEX':
    # idx = 'BNF'
    # if symbol != 'CNXBAN' :
    #     idx = 'NIF'
    # idx = config_live.indices[symbol]['idx']

    exp_date = ''
    # data_dir = 'data_' + idx
    # data_dir = idx + '/data'
    data_dir = ''
    data_dir = os.path.join(os.getcwd(), data_dir)
    max_retries = 3
    retry_interval = 5
    hist_data = None

    for i in range(max_retries):
        try:
            # if call_or_put == '':
            if call_or_put == 'futures':
                strike = ''
                product_type = 'futures'
                call_or_put = 'others'
                exch_code = "NFO"
            else :
                product_type = 'options'
                exch_code = "NSE"

            exp_date = exp_date_str + "T07:00:00.000Z"
            
            # exch_code = config_live.indices[symbol]["exchg_fno"]
            if exp_date_str == '':
                exch_code = "NSE"
                # exch_code = config_live.indices[symbol]["exchg_spot"]
            if symbol == 'SENSEX':
                product_type = "others"
            print(f"using the exch_code= {exch_code}")

            # hist_data = isec.get_historical_data(interval=interval,
            hist_data = isec.get_historical_data_v2(interval=interval,
                                    from_date= date_str + "T09:15:00.000Z",
                                    to_date= date_str + "T17:00:00.000Z", 
                                    stock_code=symbol,
                                    # exchange_code="NFO",
                                    exchange_code=exch_code,
                                    product_type = product_type,
                                    expiry_date=exp_date,
                                    right=call_or_put,
                                    strike_price=strike)

            # If the API call is successful, break out of the loop
            if hist_data['Status'] == 200:
                df = pd.json_normalize(hist_data['Success']) 
                # if strike == '':
                if exp_date_str == '':
                    df.to_csv(data_dir + f'/idx_spot_{date_str}.csv')

                if exp_date_str != '':
                    print(f"storing the futures data for date={date_str}::symbol={symbol}")
                    df.to_csv(data_dir + f'/idx_futures_{date_str}.csv')
                    return df
                
                # if True:
                if symbol != 'SENSEX':
                    # Get the Futures data with 5minute interval
                    hist_5m_data = isec.get_historical_data(interval='1minute',
                                            from_date= date_str + "T07:00:00.000Z",
                                            # from_date= '2023-03-17' + "T18:25:00.000Z",
                                            to_date= date_str + "T17:00:00.000Z", 
                                            stock_code=symbol,
                                            exchange_code="NFO",
                                            product_type = product_type,
                                            expiry_date=exp_date,
                                            right=call_or_put,
                                            strike_price=strike)
                    if hist_5m_data['Status'] == 200:
                        df_5m = pd.json_normalize(hist_5m_data['Success']) 

                        df_5m.to_csv(data_dir + '/idx_futures_1m.csv')                        
                else:
                    # df.to_csv(data_dir + '/dup_' + str(strike)+'-'+call_or_put+'.csv')
                    # remove duplicate rows based on col1
                    df_no_duplicates = df.drop_duplicates(['datetime'])
                    rec_last_time = df_no_duplicates.iloc[-1]['datetime']
                    
                    # Convert the given datetime string to a datetime object
                    rec_last_time_obj = datetime.strptime(rec_last_time, '%Y-%m-%d %H:%M:%S')
                    # Get the current datetime
                    current_datetime = dt.datetime.now()

                    # Define a timedelta for 1 minutes
                    timedelta_1min = dt.timedelta(minutes=1)

                    # Add 1 minutes to the given datetime
                    rec_last_time_obj_1min_later = rec_last_time_obj + timedelta_1min

                    # Compare the current datetime with the given datetime + 1 minutes
                    if current_datetime <= rec_last_time_obj_1min_later:
                        # print("The current datetime is more than 1 minutes ahead of the last rec datetime.")
                    # else:
                        # print("The current datetime is not more than 1 minutes ahead of the last rec datetime.")
                        # print(f"last row datetime={df_no_duplicates.iloc[-1]['datetime']}")
                        # drop the last row
                        df_no_duplicates = df_no_duplicates.drop(df_no_duplicates.index[-1])

                    # df.to_csv(data_dir + '/' + str(strike)+'-'+call_or_put+'.csv')
                    df_no_duplicates.to_csv(data_dir + '/' + str(strike)+'-'+call_or_put+'.csv')
                break
            else:
                print(f"ERROR!! API call get_hist failed: Status={hist_data['Status']} Error={hist_data['Error']}")
                # if (hist_data['Error'] == 'Limit exceed: API call per day:') :
                if re.search("Limit exceed: API call per day:", hist_data['Error']) :
                    print(f"ERROR!! API daily limit exceed, Status={hist_data['Status']} Error={hist_data['Error']}")

                    raise ValueError("API daily limit hit. Loing with another a/c ")
        except Exception as e:
            # Print an error message
            print(f"ERROR!! API call get_hist failed: Exception={e}")
        # Sleep for the retry interval before trying again
        time.sleep(retry_interval)

    # Check the status code of the final API call
    if i == 3 or ('status' in hist_data and  hist_data['Status']  != 200):
        print(f"ERROR!! max_retries={i} and Status={hist_data['Status']} ")
        print("ERROR!! API call failed after maximum number of retries")

    # return hist_data
    # for handler in logging.handlers:
    #     handler.flush()
    #     if hasattr(handler, "stream"):
    #         handler.stream.flush()

    hist_resp_df = pd.json_normalize(hist_data['Success']) 
    hist_resp_df['datetime'] = pd.to_datetime(hist_resp_df['datetime'])
    hist_resp_df['open'] = pd.to_numeric(hist_resp_df['open'])
    hist_resp_df['high'] = pd.to_numeric(hist_resp_df['high'])
    hist_resp_df['low'] = pd.to_numeric(hist_resp_df['low'])
    hist_resp_df['close'] = pd.to_numeric(hist_resp_df['close'])
    
    hist_resp_df = hist_resp_df.rename(columns={'open': 'Open'})
    hist_resp_df = hist_resp_df.rename(columns={'high': 'High'})
    hist_resp_df = hist_resp_df.rename(columns={'low': 'Low'})
    hist_resp_df = hist_resp_df.rename(columns={'close': 'Close'})
    n_per = 5
    # hist_resp_df['idx_chg'] = hist_resp_df['yf_open'].diff(periods=n_per).round(2)

    # hist_resp_df['till_low'] = hist_resp_df['Low'].rolling(min_periods=1, window=len(hist_resp_df)).apply(lambda x: x.min(), raw=True).shift(1)
    # hist_resp_df['till_high'] = hist_resp_df['High'].rolling(min_periods=1, window=len(hist_resp_df)).apply(lambda x: x.max(), raw=True).shift(1)    

    # return hist_resp_df.loc[:,['datetime', 'yf_open', 'High', 'Low', 'Close', 'idx_chg', 'till_low', 'till_high']]
    return hist_resp_df.loc[:,['datetime', 'Open', 'High', 'Low', 'Close']]





def breeze_login_new(appKey, apiSecret, session_key):
    print(f'appKey=[{appKey}] :: apiSecret=[{apiSecret}] :: session_key=[{session_key}]')
    # Initialize SDK
    isec = BreezeConnect(api_key=appKey)    
    isec.generate_session(api_secret=apiSecret, session_token=session_key)

    # print(f"\t{dt.datetime.now()} Login successful!!! isec={isec}")
    print(f"\t{dt.datetime.now()} Login successful!!! ")    
    return isec

print(f"{dt.datetime.now()}\tstarting ...")
print(f"Command line arguments: {sys.argv}")

# Accept command line arguments for date and symbol
if len(sys.argv) > 1:
    get_idx_for_date = sys.argv[1]
    print(f"Using date from command line: {get_idx_for_date}")
if len(sys.argv) > 2:
    symbol = sys.argv[2]
    print(f"Using symbol from command line: {symbol}")

# Check if we should use saved session or create new login
if use_saved_session:
    print("Loading session from server...")
    isec = load_session_from_file()
    if not isec:
        print("Failed to load saved session, falling back to login")
        isec = breeze_login_new(use_account['appKey'], use_account['apiSecret'], session_key)
else:
    print("Creating new login session...")
    isec = breeze_login_new(use_account['appKey'], use_account['apiSecret'], session_key)
date_str = datetime.now().strftime('%Y-%m-%d')
if get_idx_for_date != '':
    date_str = get_idx_for_date
    print(f"Using input date_str={date_str} for processing")
    
print(f"***************************\n\t processing for the date:{date_str}\n***************************")
date_obj = datetime.strptime(date_str, '%Y-%m-%d') 
month_exp = find_monthly_expiry(date_obj, symbol)
month_exp_str = month_exp.strftime('%Y-%m-%d')
print(f"\t==>Monthly-expiry = {month_exp_str}")   

fut_df = get_hist_data_breeze(isec, symbol, 'futures' , '' , date_str, month_exp_str, interval = '1minute')
fut_df['datetime'] = pd.to_datetime(fut_df['datetime'])
print(f"\t==>Futures data for {symbol} on {date_str} is fetched successfully -- length={len(fut_df)}")
spot_df = get_hist_data_breeze(isec, symbol, '' , '' , date_str, '', interval = '1minute')
print(f"\t==>Spot data for {symbol} on {date_str} is fetched successfully -- length={len(spot_df)}")
spot_df['datetime'] = pd.to_datetime(spot_df['datetime'])
merged_df = pd.merge( spot_df, fut_df, on='datetime', how= 'left')

# Filter out lowercase duplicate columns to avoid confusion in the HTML dashboard
# Keep only uppercase OHLC columns (Open, High, Low, Close) and remove lowercase ones (open, high, low, close)
columns_to_drop = []
for col in merged_df.columns:
    if col.lower() in ['open', 'high', 'low', 'close'] and col.islower():
        columns_to_drop.append(col)

if columns_to_drop:
    print(f"\t==>Dropping lowercase duplicate columns: {columns_to_drop}")
    merged_df = merged_df.drop(columns=columns_to_drop)
    print(f"\t==>Cleaned dataframe now has {len(merged_df.columns)} columns")
else:
    print(f"\t==>No lowercase OHLC columns found to drop")

# Map symbol to appropriate file prefix
symbol_prefix_mapping = {
    'NIFTY': 'NIF',
    'CNXBAN': 'BNF'
}

# Get the appropriate prefix for the symbol, default to the symbol itself if not found
file_prefix = symbol_prefix_mapping.get(symbol, symbol)

merged_df.to_csv(f'idx_data_{symbol}_{date_str}.csv', index=False)
merged_df.to_csv(f'{file_prefix}_deep_analysis_{date_str}.csv', index=False)

print(f"\t==>Files generated: idx_data_{symbol}_{date_str}.csv and {file_prefix}_deep_analysis_{date_str}.csv")
print(f"{dt.datetime.now()}\tEnd !!!")
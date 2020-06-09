from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta

# Check URLs !!!
# Declare TASE stock DB URLs
HEB_TASE_HISTORICAL_DATA_URL = "https://info.tase.co.il/_layouts/Tase/ManagementPages/Export.aspx?sn=none&action=1&SubAction=2&date={0}&GridId=94&CurGuid={{D3BCD81A-8C9F-4D16-848A-FF76429D70E7}}&ExportType=3"
HEB_TASE_HISTORICAL_EXTENDED_STOCKS_DATA_URL = "https://info.tase.co.il/_layouts/Tase/ManagementPages/Export.aspx?sn=none&GridId=33&AddCol=1&Lang=he-IL&CurGuid={{26F9CCE6-D184-43C6-BAB9-CF7848987BFF}}&action=1&dualTab=&SubAction=2&date={0}&ExportType=3"
ENG_TASE_HISTORICAL_EXTENDED_STOCKS_DATA_URL = "https://info.tase.co.il/_layouts/Tase/ManagementPages/Export.aspx?sn=none&GridId=33&AddCol=1&Lang=en-US&CurGuid={85603D39-703A-4619-97D9-CE9F16E27615}&action=1&dualTab=&SubAction=1&date={0}&ExportType=3"


HEB_TASE_STOCKS_URL = "https://info.tase.co.il/_layouts/15/Tase/ManagementPages/Export.aspx?sn=none&action=1&SubAction=0&GridId=33&CurGuid=%7B26F9CCE6-D184-43C6-BAB9-CF7848987BFF%7D&ExportType=3"
ENG_TASE_STOCKS_URL = "https://info.tase.co.il/_layouts/15/Tase/ManagementPages/Export.aspx?sn=none&action=1&SubAction=0&GridId=33&CurGuid=%7B85603D39-703A-4619-97D9-CE9F16E27615%7D&ExportType=3"

GLOBES_ALL_STOCKS_URL = "https://www.globes.co.il/portal/quotes/?showAll=true"
GLOBES_STOCK_URL_FORMAT = "https://www.globes.co.il/portal/instrument.aspx?instrumentid={}"
# TASE_STOCK_INFO_URL_FORMAT = "https://www.tase.co.il/{0}/market_data/security/{1}/major_data"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'


def __init__(self, maya_msg_url):
    self.msg_url = maya_msg_url


def get_stocks_df_from_tase(url, prefix_name=""):
    i = 0
    max_tries = 5
    while (i<max_tries):
        try:
            response = requests.get(url)
            break
        except:
            i = i+1
            print("get_stocks_df_from_tase network Error. Strike " + str(i) + " out of " + str(max_tries))
    if len(response.content) == 0:
        return None
    dateTimeObj = str(datetime.now())
    filename = prefix_name + "tase_stocks.csv"
    file = open(filename, "w")
    file.write(response.text)
    file.close()
    df = pd.read_csv(filename, skiprows=3)
    return df


def fetch_tickers_one_by_one(stocks_df):
    # in: globes instrument id
    # out: stock ticker from Globes stock webpage
    tickers_list = []
    for id in stocks_df['Globes ID']:
        url = GLOBES_STOCK_URL_FORMAT.format(id)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        ticker = soup.find('div', class_="enName secName").get_text()
        tickers_list.append(ticker)
    return tickers_list


def load_stored_stock_df_from_csv():
    # debug_print(func_name="load_stored_stock_df_from_csv", state="Start")
    stocks_df = pd.read_csv("stocks_df.csv")
    # debug_print(func_name="load_stored_stock_df_from_csv", state="Done")
    return


def find_ISIN(heb_number, df):
    ISIN = df[df.ISIN.str.extract("(" + heb_number + ')', expand=False).notnull()]['ISIN']
    if ISIN.size > 0:
        return ISIN.values[0]
    return 'None'


# --------- Main functions ---------
def build_master_stock_df():
    # debug_print(func_name="build_master_stock_df", state="Start")
    # Build Hebrew and English stock df
    tlv_stocks_heb = get_stocks_df_from_tase(HEB_TASE_STOCKS_URL, prefix_name="heb")
    tlv_stocks_heb = tlv_stocks_heb.iloc[:, :3]
    tlv_stocks_heb.columns = ['heb_name', 'heb_symbol', 'number']
    tlv_stocks_eng = get_stocks_df_from_tase(ENG_TASE_STOCKS_URL, prefix_name="eng")
    tlv_stocks_eng = tlv_stocks_eng.iloc[:, :3]
    tlv_stocks_eng.columns = ['eng_name', 'ticker', 'ISIN']
    tlv_stocks_heb['number'] = tlv_stocks_heb['number'].astype(str)

    # add ISIN column to Hebrew df
    tlv_stocks_heb['ISIN'] = 'None'
    for index, row in tlv_stocks_heb.iterrows():
        tlv_stocks_heb.at[index, 'ISIN'] = find_ISIN(row['number'], tlv_stocks_eng)

    # # check
    # stocks_with_common_ISIN = tlv_stocks_heb[tlv_stocks_heb['ISIN'] != 'None']
    # stocks_with_NO_common_ISIN = tlv_stocks_heb[tlv_stocks_heb['ISIN'] == 'None']

    stocks_lookup_df = pd.merge(tlv_stocks_eng, tlv_stocks_heb, how='inner', on='ISIN', left_on=None, right_on=None,
                                left_index=False, right_index=False, sort=True, suffixes=('', ''), copy=True,
                                indicator=False, validate=None)
    stocks_lookup_df.set_index('ticker')
    # debug_print(func_name="build_master_stock_df", state="Done")
    return stocks_lookup_df


# USED
def fetch_intraday_data(stock_number, stock_ticker):
    import requests

    headers = {
        'Connection': 'keep-alive',
        'Accept': 'text/csv',
        'Accept-Language': 'en-US',
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://www.tase.co.il',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.tase.co.il/en/market_data/security/' + stock_number + '/major_data',
    }

    data = '{"FilterData":{"lang":1,"ct":0,"ot":1,"oid":"' + stock_number + '","cf":0,"cp":0,"cv":0,"cl":0,"objName":"' + stock_ticker + '"}}'
    i=0
    while (i<3):
        try:
            response = requests.post('https://api.tase.co.il/api/export/chartdata', headers=headers, data=data)
            break
        except:
            i = i+1
            print("fetch_intraday_data Error")
            print(stock_ticker + " Network Error. Strike " + str(i))
    return response


# USED
def get_all_todays_intraday_to_files(stocks_df, dir_path):
    """
    Retrieves intraday market data for all stocks in DataFrame
    Creates a CSV file for each stock
    :param stocks_df: stocks DataFrame
    :return:
    """
    import os
    # debug_print(func_name="get_all_todays_intraday_to_files", state="Start")
    today_str = str(datetime.now().date())
    for i, row in stocks_df.iterrows():
        intra_day = fetch_intraday_data(row['number'], row['ticker'])
        if (intra_day.status_code == 200):
            #filename = row['ticker'] + "_" + row['number'] + "_" + today_str + ".csv"
            filename = row['ticker'] + "_" + row['number'] + ".csv"
            path = os.path.join(dir_path, filename)
            append_response_data_to_csv(intra_day, stock_filename=path)
        else:
            print("Failed fetching " + row['ticker'])
    # debug_print(func_name="get_all_todays_intraday_to_files", state="Done")
    return


# USED
def append_response_data_to_csv(response, stock_filename, temp_filename='temp'):
    """
    Sorts and appends HTTP response market data to stock's csv
    """

    # Write data to a temporary file
    temp_file = open(temp_filename, 'wb')
    temp_file.write(response.content)
    temp_file.close()

    # Append today's sorted data to stock's file
    dff = pd.read_csv(temp_filename, skiprows=2)
    dff = dff.sort_values(by='Date')
    dff.to_csv(stock_filename, mode='a', header=False, index=False)

    return


def get_historical_data(start_date,end_date):
    # debug_print(func_name="build_master_stock_df", state="Start")
    debug_print(func_name="get_historical_data", state="Start")
    str_dbg_print("Start getting historical date from " + start_date.strftime("%Y-%m-%d") + " to " + end_date.strftime("%Y-%m-%d"))
    date = end_date
    history_filename =  start_date.strftime("%Y-%m-%d") + "_to_" + end_date.strftime("%Y-%m-%d") + "_EOD_data.csv"
    temp_filename_prefix = "historical_heb_"

    while (date >= start_date):
        # Convert date to .net format
        dotnet_date = utc_to_dotnet(date)
        url = HEB_TASE_HISTORICAL_EXTENDED_STOCKS_DATA_URL.format(dotnet_date)

        # Save date's table to a dataframe
        # daily_stocks_heb_df
        df = get_stocks_df_from_tase(url, prefix_name=temp_filename_prefix)
        if df is None:
            # Get next date...
            date -= timedelta(days=1)
            continue
        df = df.drop(df.index[-1])

        # Append df to history file
        df['date'] = date
        if date == end_date:
            df.to_csv(history_filename, mode='a', header=True, index=False)
        else:
            df.to_csv(history_filename, mode='a', header=False, index=False)

        # Get next date...
        date -= timedelta(days=1)
    debug_print(func_name="get_historical_data", state="Done")
    return


# ------------ AUX ------------

def debug_print(func_name, state):
    print(state + " " + func_name + " :" + str(datetime.now()))


def str_dbg_print(str_to_print):
    print(str(datetime.now()) + ": " + str_to_print)


def sort_all_stock_files_in_dir(dir_path):
    import os
    directory = os.fsencode(dir_path)

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".csv"):
            path = os.path.join(dir_path, filename)
            sort_file(path)


def sort_file(filename):
    # OVERWRITES stock file with a sorted version
    df = pd.read_csv(filename, skiprows=2)
    df = df.sort_values(by='Date')
    df.to_csv(filename, mode='w', header=True, index=False)

def posix_to_utc(posix_timestamp):
    posix_epoch = datetime(1970, 1, 1)
    utc_time = posix_epoch + timedelta(seconds=posix_timestamp)
    return utc_time

def dotnet_to_utc(dotnet_timestamp):
    dotnet_epoch = datetime(1, 1, 1)
    utc_time = dotnet_epoch + timedelta(microseconds=dotnet_timestamp // 10)
    return utc_time

def utc_to_dotnet(utc_time):
    dotnet_epoch = datetime(1, 1, 1)
    dotnet_timestamp = 10 * (utc_time - dotnet_epoch) // timedelta(microseconds=1)
    return dotnet_timestamp

def utc_to_posix(utc_time):
    posix_epoch = datetime(1970, 1, 1)
    posix_timestamp = (utc_time - posix_epoch) // timedelta(seconds=1)
    return posix_timestamp


def to_timestamp(timestamp):
    timestamp = float(timestamp[0])
    seconds_since_epoch = timestamp/10**7
    loc_dt = datetime.fromtimestamp(seconds_since_epoch)
    loc_dt -= timedelta(days=(1970 - 1601) * 365 + 89)
    return loc_dt


# def rename_files_in_dir(dir_path):
#     import os
#     directory = os.fsencode(dir_path)
#
#     for file in os.listdir(directory):
#         filename = os.fsdecode(file)
#         if filename.endswith(".csv"):
#             old_path = os.path.join(dir_path,filename)
#             new_path = "_".join(old_path.split("_")[:-1])+".csv"
#             # new_path = os.path.join(dir_path,new_name)
#             os.rename(old_path, new_path)


# ------------------ Not Used ------------------
def fetch_ticker(globes_id):
    # in: globes instrument id
    # out: stock ticker from Globes stock webpage
    url = GLOBES_STOCK_URL_FORMAT.format(globes_id)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    ticker = soup.find('div', class_="enName secName").get_text()
    return ticker


# Not used
def get_xls_intraday_data(globes_id):
    # debug_print(func_name="get_xls_intraday_data", state="Start")
    print("get_xls_intraday_data for instrument " + globes_id)
    xlsurl = "https://www.globes.co.il/portal/instrument/instrumentgraph_toexcel.aspx?instrumentid=" + globes_id + "&feeder=0"
    res = requests.get(xlsurl)
    out = open('test1.xls', 'wb')
    out.write(res.content)
    out.close()
    data = pd.read_html('test1.xls', skiprows=1)
    data.info()
    # TODO: Change headers and convert to DataFrame

    # debug_print(func_name="get_xls_intraday_data", state="Done")


# Not used
# def build_stock_df_from_web():
#     stocks_list = fetch_tase_stocks_list()
#     stocks_dict  =  {'Heb Name' : stocks_list[0], 'Stock Num' : stocks_list[1], 'Globes ID' : stocks_list[2]}
#     stocks_df = pd.DataFrame(stocks_dict)
#     #tickers = stocks_df['Globes ID'].apply(fetch_ticker)   # doesn't work
#     tickers_list = fetch_tickers_one_by_one(stocks_df)
#     stocks_df['Ticker'] = tickers_list
#     stocks_df.to_csv("stocks_df.csv", index=False, header=True)
#
#     return stocks_df

# Not used
def fetch_tase_stocks_list():
    url = GLOBES_ALL_STOCKS_URL
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    stock_heb_names_list = []
    stock_number_list = []
    stock_globes_instrument_id_list = []
    trs = soup.find_all('tr')
    trs = trs[2:]
    for tr in trs:
        stock_name = tr.find_all('td')[1].a.get_text()
        # stock_name = tr.find_all('td')[1].get_text()
        stock_number = tr.find_all('td')[2].get_text()
        stock_globes_instrument_id = tr.find_all('td')[1].a.get('href').split('=')[1]
        stock_heb_names_list.append(stock_name)
        stock_number_list.append(stock_number)
        stock_globes_instrument_id_list.append(stock_globes_instrument_id)
    return [stock_heb_names_list, stock_number_list, stock_globes_instrument_id_list]
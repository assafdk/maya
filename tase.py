from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime

# Check URLs !!!
# Declare TASE stock DB URLs
HEB_TASE_STOCKS_URL = "https://info.tase.co.il/_layouts/15/Tase/ManagementPages/Export.aspx?sn=none&action=1&SubAction=0&GridId=33&CurGuid=%7B26F9CCE6-D184-43C6-BAB9-CF7848987BFF%7D&ExportType=3"
ENG_TASE_STOCKS_URL = "https://info.tase.co.il/_layouts/15/Tase/ManagementPages/Export.aspx?sn=none&action=1&SubAction=0&GridId=33&CurGuid=%7B85603D39-703A-4619-97D9-CE9F16E27615%7D&ExportType=3"

GLOBES_ALL_STOCKS_URL = "https://www.globes.co.il/portal/quotes/?showAll=true"
GLOBES_STOCK_URL_FORMAT = "https://www.globes.co.il/portal/instrument.aspx?instrumentid={}"
#TASE_STOCK_INFO_URL_FORMAT = "https://www.tase.co.il/{0}/market_data/security/{1}/major_data"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'


def __init__(self, maya_msg_url):
    self.msg_url = maya_msg_url


def get_stocks_df_from_tase(url, prefix_name=""):
    response = requests.get(url)
    dateTimeObj = str(datetime.now())
    filename = prefix_name+"tase_stocks_"+dateTimeObj+".csv"
    file = open(filename,"w")
    file.write(response.text)
    df = pd.read_csv(filename,skiprows=3)
    return df


def get_stocks_df_from_csv(csv_file):
    return pd.read_csv(csv_file)


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
        #stock_name = tr.find_all('td')[1].get_text()
        stock_number = tr.find_all('td')[2].get_text()
        stock_globes_instrument_id = tr.find_all('td')[1].a.get('href').split('=')[1]
        stock_heb_names_list.append(stock_name)
        stock_number_list.append(stock_number)
        stock_globes_instrument_id_list.append(stock_globes_instrument_id)
    return [stock_heb_names_list, stock_number_list, stock_globes_instrument_id_list]


def fetch_ticker(globes_id):
    # in: globes instrument id
    # out: stock ticker from Globes stock webpage
    url = GLOBES_STOCK_URL_FORMAT.format(globes_id)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    ticker = soup.find('div',class_="enName secName").get_text()
    return ticker


def fetch_tickers_one_by_one(stocks_df):
    # in: globes instrument id
    # out: stock ticker from Globes stock webpage
    tickers_list = []
    for id in stocks_df['Globes ID']:
        url = GLOBES_STOCK_URL_FORMAT.format(id)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        ticker = soup.find('div',class_="enName secName").get_text()
        tickers_list.append(ticker)
    return tickers_list


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
        'Referer': 'https://www.tase.co.il/en/market_data/security/'+stock_number+'/major_data',
    }

    data = '{"FilterData":{"lang":1,"ct":0,"ot":1,"oid":"'+stock_number+'","cf":0,"cp":0,"cv":0,"cl":0,"objName":"'+stock_ticker+'"}}'

    response = requests.post('https://api.tase.co.il/api/export/chartdata', headers=headers, data=data)
    return response


def fetch_maya_msgs(self):
    # TODO: read RSS
    return


def fetch_stock_details(self):
    # TODO: get ticker...
    html_file = requests.get(self.msg_url)
    soup = BeautifulSoup(self.msg_url, 'html.parser')
    return

# # Not used
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


def load_stored_stock_df_from_csv():
    stocks_df = get_stocks_df_from_csv("stocks_df.csv")


def find_ISIN(heb_number,df):
    ISIN = df[df.ISIN.str.extract("(" + heb_number + ')', expand=False).notnull()]['ISIN']
    if ISIN.size > 0:
        return ISIN.values[0]
    return 'None'


def get_xls_intraday_data(globes_id):
    print("get_xls_intraday_data for instrument "+globes_id)
    xlsurl  = "https://www.globes.co.il/portal/instrument/instrumentgraph_toexcel.aspx?instrumentid="+globes_id+"&feeder=0"
    res = requests.get(xlsurl)
    out = open('test1.xls','wb')
    out.write(res.content)
    out.close()
    data = pd.read_html('test1.xls',skiprows=1)
    data.info()
    # TODO: Change headers and convert to DataFrame

# Main
def build_master_stock_df():
    # Build Hebrew and English stock df
    tlv_stocks_heb = get_stocks_df_from_tase(HEB_TASE_STOCKS_URL, prefix_name="heb")
    tlv_stocks_heb = tlv_stocks_heb.iloc[:, :3]
    tlv_stocks_heb.columns = ['heb_name','heb_symbol','number']
    tlv_stocks_eng = get_stocks_df_from_tase(ENG_TASE_STOCKS_URL, prefix_name="eng")
    tlv_stocks_eng = tlv_stocks_eng.iloc[:, :3]
    tlv_stocks_eng.columns = ['eng_name','ticker','ISIN']
    tlv_stocks_heb['number'] = tlv_stocks_heb['number'].astype(str)

    # add ISIN column to Hebrew df
    tlv_stocks_heb['ISIN'] = 'None'
    for index,row in tlv_stocks_heb.iterrows():
        tlv_stocks_heb.at[index, 'ISIN'] = find_ISIN(row['number'], tlv_stocks_eng)

    # # check
    # stocks_with_common_ISIN = tlv_stocks_heb[tlv_stocks_heb['ISIN'] != 'None']
    # stocks_with_NO_common_ISIN = tlv_stocks_heb[tlv_stocks_heb['ISIN'] == 'None']

    stocks_lookup_df = pd.merge(tlv_stocks_eng, tlv_stocks_heb, how='inner', on='ISIN', left_on=None, right_on=None,left_index=False, right_index=False, sort=True, suffixes=('', ''), copy=True, indicator=False,validate=None)
    stocks_lookup_df.set_index('ticker')
    print('Done - build_master_stock_df()')

    return stocks_lookup_df

#intra_day = fetch_intraday_data('373019', 'AURA')
#print(intra_day.text)

#
# import requests
# from bs4 import BeautifulSoup
#
#
# # Collect and parse first page
# page = requests.get('http://maya.tase.co.il/reports/details/1293201')
# soup = BeautifulSoup(page.text, 'html.parser')
#
# # Pull all text from the BodyText div
# artist_name_list = soup.find(class_='BodyText')
#
# # Pull text from all instances of <a> tag within BodyText div
# artist_name_list_items = artist_name_list.find_all('a')
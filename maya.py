import pandas as pd
import feedparser
from datetime import datetime

MAYA_URL = "https://maya.tase.co.il/rss/maya.xml"


# def __init__(self, stocks_df = None, rssurl = MAYA_URL):
#     self.feedurl = rssurl
#     self.stocks_df = stocks_df


def create_msgs_dataframe(stocks_df, feedurl = MAYA_URL):
    # Parse Maya RSS feed
    thefeed = feedparser.parse(feedurl)
    pub_times_list = []
    titles_list = []
    links_list = []
    for entry in thefeed.entries:
        pub_times_list.append(entry.get("published"))
        titles_list.append(entry.get("title"))
        links_list.append(entry.get("link"))

    maya_msgs_df = pd.DataFrame({'time': pub_times_list, 'title': titles_list, 'link': links_list})

    # Extract stock name for each message and add english ticker
    maya_msgs_df['heb_name'] = maya_msgs_df['title'].apply(get_stock_name)
    maya_msgs_df = add_tickers(maya_msgs_df, stocks_df)
    return maya_msgs_df

def analyze(msgs_df):
    # TODO: Analyze sentiment
    # sentiment = []
    # magnitude = []
    # for msg in msgs_df:
    #     (sent,mag) =  get_google_sentiment(msg['title'])
    #     sentiment.append(sent)
    #     magnitude.append(mag)
    return


# AUX - internal
def get_stock_name(x):
    return x.split('  - ')[0]


def add_tickers(msgs_df, stocks_df):
    df = pd.merge(msgs_df, stocks_df, how='inner', on='heb_name', left_on=None, right_on=None, left_index=False,
                 right_index=False, sort=False, suffixes=('', ''), copy=True, indicator=False, validate=None)
    df = df[['time', 'ticker', 'heb_name', 'heb_symbol', 'title', 'link']]

    return df


def get_historical_bulletin_msgs(from_date="1999-12-31T22:00:00.000Z",to_date="2020-05-24T21:00:00.000Z"):

    import requests, json, csv, time
    print("Start get_historical_bulletin_msgs() :" + str(datetime.now()))
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'he-IL',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'X-Maya-With': 'allow',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://maya.tase.co.il',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://maya.tase.co.il/reports/company?q=%7B%22DateFrom%22:%22{0}%22,%22DateTo%22:%22{1}%22,%22Page%22:1,%22events%22:%5B%5D,%22subevents%22:%5B%5D,%22IsBreakingAnnouncement%22:true%7D'.format(from_date,to_date),
    }
    # data = '{"Page":1,"GroupData":[],"DateFrom":"1999-12-31T22:00:00.000Z","DateTo":"2020-05-22T21:00:00.000Z","IsBreakingAnnouncement":true,"IsForTaseMember":false,"IsSpecificFund":false,"Form":null,"QOpt":1,"ViewPage":2}'
    data_fmt = '{{"Page":{0},"GroupData":[],"DateFrom":"{1}","DateTo":"{2}","IsBreakingAnnouncement":true,"IsForTaseMember":false,"IsSpecificFund":false,"Form":null,"QOpt":1,"ViewPage":2}}'

    # First page - just to get number of pages
    page = 1
    response = requests.post('https://mayaapi.tase.co.il/api/report/filter', headers=headers, data=data_fmt.format(page,from_date,to_date))
    res_dict = json.loads(response.text)
    last_page = res_dict['TotalPages']
    # print("got bulletin messages from {0} to {1}".format(res_dict['DateFrom'],res_dict['DateTo']))

    strike = 0
    max_strikes = 10
    msg_counter = 0
    msgs_list = []
    filename = 'all_msgs.csv'
    headers_list = ['Date', 'CompanyName', 'Subject', 'CompanyId', 'CompanyURL']

    try:
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers_list)
            writer.writeheader()

            while page <= last_page:
                i = 0
                while i < 5:
                    try:
                        response = requests.post('https://mayaapi.tase.co.il/api/report/filter', headers=headers,
                                                 data=data_fmt.format(page,from_date,to_date))
                        if response.status_code != 200:
                            print("Response {0} - on page {1}. Trying again {2}...".format(response.status_code,
                                                                                                   page, i))
                            time.sleep(3 + i)
                            i += 1
                            continue
                        break
                    except:
                        print("Network error on page {0}. Trying again {1}...".format(page,i))
                        time.sleep(3 + i)
                        i += 1
                        continue
                if i == 5 or response.status_code != 200:
                    print("Response {0} - on msg_couner = {1}. Trying again {2}...".format(response.status_code,page, i))
                    page += 1
                    continue

                res_dict = json.loads(response.text)
                if res_dict['Reports'].__len__() == 0:
                    print("Response contains no reports - page {0}, msg_count {1}".format(page,msg_counter))
                    strike += 1
                    if strike > max_strikes:
                        csvfile.close()
                        return
                for msg in res_dict['Reports']:
                    msg_counter += 1
                    msg_dict = {'Date': msg['PubDate'], 'CompanyName': msg['FormalCompanyData']['CompanyName'],
                                'Subject': msg['Subject'],
                                'CompanyId': msg['FormalCompanyData']['CompanyId'],
                                'CompanyURL': msg['FormalCompanyData']['URL']}
                    msgs_list.append(msg_dict)

                for msg in msgs_list:
                    writer.writerow(msg)

                msgs_list = []
                page += 1
    except IOError:
        print("I/O error")

    print("Done get_historical_bulletin_msgs() :" + str(datetime.now()))

def check_trigger():
    msgs_df = create_msgs_dataframe(MAYA_URL)


# Maya Main

# get_historical_bulletin_msgs(from_date="1999-12-31T22:00:00.000Z",to_date="2000-11-23T21:00:00.000Z")
#
# print("Maya - Done")
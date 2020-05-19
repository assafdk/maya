import pandas as pd
import feedparser

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


# Maya Main
def check_trigger():
    msgs_df = create_msgs_dataframe(MAYA_URL)
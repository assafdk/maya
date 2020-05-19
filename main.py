from email_module import emailsender
import rss
import requests
from datetime import datetime
import maya
import tase


def get_triggers():
    # TODO: Define trigger
    ticker = False
    ticker = maya.check_trigger()
    return ticker


# Main
#---DEBUG----
# dir_path = "/Users/assafdekel/other_projects/maya/temp"
#tase.sort_all_stock_files_in_dir(dir_path)
# tase.rename_files_in_dir(dir_path)
#------------

# Build TASE stocks lookup table
stocks_df = tase.build_master_stock_df()
# Get & append new intra_day data
# intraday_dir_path = '/Users/assafdekel/other_projects/maya/intraday'
# tase.get_all_todays_intraday_to_files(stocks_df,dir_path=intraday_dir_path)

# Retrieve MAYA messages
maya_msgs = maya.create_msgs_dataframe(stocks_df)
# Get sentiment for each message
maya_msgs = maya.analyze(maya_msgs)

while (1):
    triggers = get_triggers()
    if triggers:
        #open_position(triggered_ticker)
        # Returns a datetime object containing the local date and time
        dateTimeObj = datetime.now()
        print("Position opened at " + dateTimeObj)
        #track_stock_and_close_position()
        dateTimeObj = datetime.now()
        print("Position closed at " + dateTimeObj)




# While (1):
#     msgs = fetch_maya_messages()
#     for msg in msgs:
#         sentiment = get_msg_sentiment(msg)
#
#
# get_
# msgs_parsed = parse_msgs(msgs)
# msgs_english = google_translate(msgs_parsed)
# sentiment = google_nlp(msgs_english)
#
#


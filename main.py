import datetime as dt
import maya
import tase
<<<<<<< HEAD


# ---DEBUG----
=======
import time
>>>>>>> 881346485972974d90113919a93ec34d1567ff8c

# tase.get_historical_data(start_date=datetime(2020,4,1),end_date=datetime(2020,5,27))
# print("DEBUG")
# dir_path = "/Users/assafdekel/other_projects/maya/temp"
#tase.sort_all_stock_files_in_dir(dir_path)
# tase.rename_files_in_dir(dir_path)
<<<<<<< HEAD
# ------------

# ------------------ Main ------------------
# Build TASE stocks lookup table
stocks_df = tase.build_master_stock_df()
=======

>>>>>>> 881346485972974d90113919a93ec34d1567ff8c
# Get & append new intra_day data
# intraday_dir_path l= '/Users/assafdekel/other_projects/maya/intraday'
# tase.get_all_todays_intraday_to_files(stocks_df,dir_path=intraday_dir_path)
#------------

# ------------ init ------------
# Build TASE stocks lookup table
stocks_df = tase.build_master_stock_df()
SLEEP_SECONDS = 30
POSITION_MAX_TIME = dt.timedelta(minutes=120)
# ------------------------------

# ------------ Main ------------
while(True):
    maya_msgs = maya.create_msgs_dataframe(stocks_df)       # retrieve MAYA messages
    maya_msgs = maya.analyze_msgs(maya_msgs)                # get sentiment/score for each message
    relevant_msgs = maya.filter_relevant_msgs(maya_msgs)    # filter by relevant msgs only
    if relevant_msgs.count()['ticker'] > 0:
        for ticker in relevant_msgs['ticker'].unique():     # buy position for each ticker
            #TODO: check if position is already open for ticker
            if not restrictions:
                position_id = ib.buy(ticker)
                ib.set_stop_loss(position_id)
                ib.set_take_profit(position_id)
                restrictions = update_restrictions()

    for position in ib.get_open_positions():
        if (dt.datetime.now() - position.time > POSITION_MAX_TIME):
            ib.close_position(position.id)

    time.sleep(SLEEP_SECONDS)

# ------------------------------


<<<<<<< HEAD
while (1):
    triggers = None
    if triggers:
        #open_position(triggered_ticker)
        # Returns a datetime object containing the local date and time
        dateTimeObj = datetime.now()
        print("Position opened at " + dateTimeObj)
        #track_stock_and_close_position()
        dateTimeObj = datetime.now()
        print("Position closed at " + dateTimeObj)
=======
>>>>>>> 881346485972974d90113919a93ec34d1567ff8c


# while (1):
#     triggers = 1
#     if triggers:
#         #open_position(triggered_ticker)
#         # Returns a datetime object containing the local date and time
#         dateTimeObj = dt.datetime.now()
#         print("Position opened at " + dateTimeObj)
#         #track_stock_and_close_position()
#         dateTimeObj = dt.datetime.now()
#         print("Position closed at " + dateTimeObj)


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


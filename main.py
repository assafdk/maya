import datetime as dt
import maya
import tase
import time
import IB_tutorial as ib

# Global variables
SLEEP_SECONDS = 30
POSITION_MAX_TIME = dt.timedelta(minutes=120)
TWS_IP_ADDR = "127.0.0.1"
TWS_PORT = 7497     # 7497 - paper account
TWS_CLIENT_ID = 0

MAX_PORTFOLIO_VALUE = 10000         # Max total value of positions - Don't invest more then this
FIRST_TRADING_TIME = dt.time(11,00) # Don't buy before this hour
LAST_TRADING_TIME = dt.time(15,00)  # Don't after before this hour


# Trading strategy functions
def strategy_restrictions(ticker):
    if ib.position_exists(ticker):                              # if position exists don't buy more
        return True
    if ib.open_positions_total_value() >= MAX_PORTFOLIO_VALUE:  # Max funds invested - don't invest more
        return True
    if dt.datetime.now().time() < FIRST_TRADING_TIME:           # Too early in the day - don't buy yet
        return True
    if dt.datetime.now().time() > LAST_TRADING_TIME:            # Too late in the day - don't buy anymore today
        return True
    # TODO: price too high? (can't buy Google for 2,500$)
    # TODO: add more filters: Volume? other indicators (RSI? over-bought?) Volatility? Sudden high price increase?
    # TODO: think about ticker reputation - aggregate our history and experince with this ticker
    # TODO: too many positions in the same industry?
    # TODO: What time is it? Market almost closed? Do we want to buy late in the day?
    return False


def time_to_close(position):
    if dt.datetime.now()-position.time > POSITION_MAX_TIME:
        return True
    return False


# Main
#---DEBUG----
# tase.get_historical_data(start_date=datetime(2020,4,1),end_date=datetime(2020,5,27))
# print("DEBUG")
# dir_path = "/Users/assafdekel/other_projects/maya/temp"
#tase.sort_all_stock_files_in_dir(dir_path)
# tase.rename_files_in_dir(dir_path)

# Get & append new intra_day data
# intraday_dir_path l= '/Users/assafdekel/other_projects/maya/intraday'
# tase.get_all_todays_intraday_to_files(stocks_df,dir_path=intraday_dir_path)
#------------

# ------------ init ------------
# Build TASE stocks lookup table
stocks_df = tase.build_master_stock_df()
# OTHER CONSTANTS AND CONSTRAINTS?

ib_app = ib.IB_App()
ib_app.connect(TWS_IP_ADDR, TWS_PORT, TWS_CLIENT_ID)
ib_app.run()
# ------------------------------

# ------------------------------ Main ------------------------------

while(True):
    maya_msgs = maya.create_msgs_dataframe(stocks_df)       # retrieve MAYA messages
    maya_msgs = maya.analyze_msgs(maya_msgs)                # get sentiment/score for each message
    relevant_msgs = maya.filter_relevant_msgs(maya_msgs)    # filter by relevant msgs only (
    if relevant_msgs.count()['ticker'] > 0:                 # if there are relevant messages:
        for ticker in relevant_msgs['ticker'].unique():         # (buy position for each ticker)
            if strategy_restrictions(ticker):
                # strategy restrictions prevent buying this ticker
                continue

            position_id = ib.buy(ticker)
            ib.set_stop_loss(position_id)
            ib.set_take_profit(position_id)
            restrictions = update_restrictions()

    for position in ib.get_open_positions():                # for each open position:
        if time_to_close(position):
            ib.close_position(position.id)

    time.sleep(SLEEP_SECONDS)

# ------------------------------------------------------------------

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


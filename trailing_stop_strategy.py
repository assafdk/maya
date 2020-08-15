import datetime as dt
import time
import pandas as pd
import random as rand
import math
import numpy as np
from threading import Thread, Lock

# from multiprocessing import Process, Lock

# Global variables
DEBUG = True

IB_ACCOUNT_NUMBER = "DU2185370"
TWS_IP_ADDR = "127.0.0.1"
TWS_PORT = 7497  # 7497 - paper account
TWS_CLIENT_ID = 0

tickers_list = ['AAPL', 'TSLA', 'CL', 'JETS', 'FB', 'INTC', 'BA', 'T']  # tickers to trade on
trigger_flag = False
if DEBUG:
    TRIGGER_TIME_WINDOW = dt.timedelta(days=3)
else:
    TRIGGER_TIME_WINDOW = dt.timedelta(minutes=5)
SLEEP_SECONDS = 30
POSITION_MAX_TIME = dt.timedelta(days=365)

ALLOCATION_PERCENT = 0.1  # How much stocks to buy - 10% of total portfolio
MAX_TRADING_FUNDS = 10000  # Total value of positions - Don't invest more then this
DEFAULT_POSITION_VALUE = ALLOCATION_PERCENT * MAX_TRADING_FUNDS  # 10% * 10,000$ = 1,000$
MAX_POSITION_DOLLARS = 3000  # Max dollars per position
FIRST_TRADING_TIME = dt.time(11, 00)  # Don't buy before this hour
LAST_TRADING_TIME = dt.time(15, 00)  # Don't after before this hour


class Funds:
     def __init__(self):
         self.ILS = 0
         self.USD = 0
         self.EUR = 0

# =================== Functions ===================
def run_ib_app(app):
    app.run()


# # Check if the API is connected via orderid. Assumes orderid was set to None before connect
# def wait_for_connection():
#     global ib_app
#     time.sleep(3)
#     while True:
#         if isinstance(ib_app.nextOrderId, int):
#             print('connected')
#             break
#         else:
#             print('waiting for connection')
#             time.sleep(1)


def get_stock_price(ticker):
    if ticker is None:
        return None
    last_price = tickers_df[tickers_df['ticker'] == ticker]['last_price'].iloc[0]
    return last_price


def dbg_get_stock_price(ticker):
    return 1000


def get_ticker_id(ticker):
    if ticker is None:
        return None
    ticker_id = tickers_df[tickers_df['ticker'] == ticker].index[0]
    return ticker_id


def update_price(ticker_index, price_type, price):
    global tickers_df
    tickers_df.iloc[ticker_index, tickers_df.columns.get_loc(price_type)] = price


# ======================== IB App ========================
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
from ibapi.ticktype import TickTypeEnum
from threading import Timer


# Callback overrides
class IB_App(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    # ------------------- AUX & Shortcuts -------------------
    def create_nasdaq_contract(self, ticker):
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"
        return contract

    def send_order(self, ticker, order_action, quantity, sec_type="STK", order_type="MKT", limit_price=None,
                   trail_percent=None, trail_stop_price=None):
        contract = Contract()  # Creates a contract object from the import
        contract.symbol = ticker  # Sets the ticker symbol
        contract.secType = sec_type  # Defines the security type as stock
        contract.currency = "USD"  # Currency is US dollars
        # In the API side, NASDAQ is always defined as ISLAND in the exchange field
        contract.exchange = "SMART"
        # contract.PrimaryExch = "NYSE"
        contract.PrimaryExch = "NASDAQ"

        order = Order()
        order.action = order_action
        order.orderType = order_type
        order.totalQuantity = quantity

        if order_type == 'TRAIL':
            order.tif = "GTC"  # Good 'Till Canceled
            if trail_percent is not None:
                order.trailingPercent = trail_percent
            if trail_stop_price is not None:
                order.trailStopPrice = trail_stop_price

        if order_type == 'LMT':
            order.tif = "IOC"  # Immediate or Cancel
            if limit_price is not None:
                order.lmtPrice = limit_price

        self.placeOrder(self.nextOrderId, contract, order)
        return self.nextOrderId

    # --------------------------------------------------------

    # EWrapper callback
    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    # EWrapper callback
    def nextValidId(self, orderId):
        self.nextOrderId = orderId

    """ <summary>
    #/ A Market order is an order to buy or sell at the market bid or offer price. A market order may increase the likelihood of a fill 
    #/ and the speed of execution, but unlike the Limit order a Market order provides no price protection and may fill at a price far 
    #/ lower/higher than the current displayed bid/ask.
    #/ Products: BOND, CFD, EFP, CASH, FUND, FUT, FOP, OPT, STK, WAR
    </summary>"""

    @staticmethod
    def MarketOrder(action: str, quantity: float):
        # ! [market]
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity
        # ! [market]
        return order

    """ <summary>
    #/ A sell trailing stop order sets the stop price at a fixed amount below the market price with an attached "trailing" amount. As the 
    #/ market price rises, the stop price rises by the trail amount, but if the stock price falls, the stop loss price doesn't change, 
    #/ and a market order is submitted when the stop price is hit. This technique is designed to allow an investor to specify a limit on the 
    #/ maximum possible loss, without setting a limit on the maximum possible gain. "Buy" trailing stop orders are the mirror image of sell 
    #/ trailing stop orders, and are most appropriate for use in falling markets.
    #/ Products: CFD, CASH, FOP, FUT, OPT, STK, WAR
    </summary>"""

    @staticmethod
    def TrailingStop(action: str, quantity: float, trailingPercent: float,
                     trailStopPrice: float):
        order = Order()
        order.action = action
        order.orderType = "TRAIL"
        order.totalQuantity = quantity
        order.trailingPercent = trailingPercent
        order.trailStopPrice = trailStopPrice
        return order

    # ---------------- stock price data ----------------
    def tickPrice(self, reqId, tickType, price, attrib):
        # print("TickPrice. TickerId:", reqId, "tickType:", TickTypeEnum.to_str(tickType),
        #       "Price:", price, "CanAutoExecute:", attrib.canAutoExecute,
        #       "PastLimit:", attrib.pastLimit, end=' ')

        # update stocks tracking table
        if TickTypeEnum.BID == tickType or TickTypeEnum.DELAYED_BID == tickType:
            update_price(reqId, 'bid', price)
        if TickTypeEnum.ASK == tickType or TickTypeEnum.DELAYED_ASK == tickType:
            update_price(reqId, 'ask', price)
        if TickTypeEnum.LAST == tickType or TickTypeEnum.DELAYED_LAST == tickType:
            update_price(reqId, 'last_price', price)

        if tickType == TickTypeEnum.BID or tickType == TickTypeEnum.ASK:
            print("PreOpen:", attrib.preOpen)
        # else:
        #     print()
        return

    # def tickSize(self, reqId, tickType, size):
    #     print("TickSize. TickerId:", reqId, "TickType:", TickTypeEnum.to_str(tickType), "Size:", size)

    # EWrapper callback
    def updateAccountValue(self, key: str, val: str, currency: str,
                           accountName: str):
        global available_funds

        super().updateAccountValue(key, val, currency, accountName)
        print("UpdateAccountValue. Key:", key, "Value:", val,
              "Currency:", currency, "AccountName:", accountName)
        if key == "AvailableFunds":
            if currency == "ILS":
                available_funds.ILS = val
            if currency == "USD":
                available_funds.USD = val
            if currency == "EUR":
                available_funds.EUR = val
            # print("UpdateAccountValue. Key:", key, "Value:", val,
            #       "Currency:", currency, "AccountName:", accountName)
        return

    def updatePortfolio(self, contract: Contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        super().updatePortfolio(contract, position, marketPrice, marketValue,
                                averageCost, unrealizedPNL, realizedPNL, accountName)
        print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType,
              "Exchange:", contract.exchange, "Position:", position, "MarketPrice:", marketPrice,
              "MarketValue:", marketValue, "AverageCost:", averageCost,
              "UnrealizedPNL:", unrealizedPNL, "RealizedPNL:", realizedPNL,
              "AccountName:", accountName)

        dict = {'Symbol': contract.symbol, 'SecType': contract.secType, 'Position': position,
                'MarketPrice': marketPrice, 'MarketValue': marketValue, 'AverageCost': averageCost,
                "UnrealizedPNL": unrealizedPNL, "RealizedPNL": realizedPNL}

        # positions_df = pd.append(dict,ignore_index=True)

    # TODO: add support for options
    def position(self, account: str, contract: Contract, position: float,
                 avgCost: float):
        global initial_position_update_done
        global stock_positions_df
        super().position(account, contract, position, avgCost)
        print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:",
              contract.secType, "Currency:", contract.currency,
              "Position:", position, "Avg cost:", avgCost)
        dict = {'Symbol': contract.symbol, 'SecType': contract.secType, 'Currency': contract.currency,
                'Position': position, 'Avg_cost': avgCost}

        # first time - getting portfolio
        if not initial_position_update_done:
            stock_positions_df = stock_positions_df.append(dict, ignore_index=True)
            return

        if position == 0:
            stock_positions_df.drop(index=contract.symbol)

        # TODO: add support for options
        # if symbol exists, check if this is the same SecType (STK or option) so position exists

        # if there is already a position for this stock - update it
        if contract.symbol in stock_positions_df.index:
            stock_positions_df.at[contract.symbol, 'Currency'] = contract.currency
            stock_positions_df.at[contract.symbol, 'Position'] = position
            stock_positions_df.at[contract.symbol, 'Avg_cost'] = avgCost
        else:
            # add new row
            stock_positions_df = stock_positions_df.append(dict, ignore_index=True)
        return

    def positionEnd(self):
        super().positionEnd()
        global initial_position_update_done
        initial_position_update_done = True
        print("PositionEnd")
        return

    # def updateAccountTime(self, timeStamp: str):
    #     super().updateAccountTime(timeStamp)
    #     print("UpdateAccountTime. Time:", timeStamp)
    # --------------------------------------------------

    # ----- Order Management -----
    def orderStatus(self, orderId, status, filled, remaining,
                    avgFillPrice, permId, parentId, lastFillPrice,
                    clientId, whyHeld, mktCapPrice):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId,
                            parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:", lastFillPrice,
              "ClientId:", clientId, "WhyHeld:", whyHeld, "MktCapPrice:", mktCapPrice)

    def openOrder(self, orderId, contract, order, orderState):
        super().openOrder(orderId, contract, order, orderState)
        print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId,
              " OrderId:", orderId, "Account:", order.account, "Symbol:", contract.symbol,
              "SecType:", contract.secType, "Exchange:", contract.exchange,
              "Action:", order.action, "OrderType:", order.orderType,
              "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice,
              "Status:", orderState.status)

    # ----------------------------

    # ------ Historical Data ------
    def historicalData(self, reqId, bar):
        global historical_data_df
        symbol = tickers_df.loc[reqId, 'ticker']
        dict = {'Symbol': symbol, 'time': dt.datetime.strptime(bar.date, "%Y%m%d %H:%M:%S"), 'Open': bar.open,
                'High': bar.high, 'Low': bar.low,
                'Close': bar.close, 'Volume': bar.volume, 'Average': bar.average}
        historical_data_df = historical_data_df.append(dict, ignore_index=True)
        print("HistoricalData. ReqId:", reqId, "BarData.", bar)

    # def historicalData(self, reqId, bar):
    #     global historical_data_dict
    #     symbol = tickers_df.loc[reqId, 'ticker']
    #     dict = {'Symbol': symbol, 'time': dt.datetime.strptime(bar.date, "%Y%m%d %H:%M:%S"), 'Open': bar.open,
    #             'High': bar.high, 'Low': bar.low,
    #             'Close': bar.close, 'Volume': bar.volume, 'Average': bar.average}
    #     historical_data_dict[symbol] = historical_data_dict[symbol].append(dict, ignore_index=True)
    #     print("HistoricalData. ReqId:", reqId, "BarData.", bar)

    # def historicalDataEnd(self, reqId: int, start: str, end: str):
    #     super().historicalDataEnd(reqId, start, end)
    #     global historical_data_dict
    #     symbol = tickers_df.loc[reqId, 'ticker']
    #     # historical_data_dict[symbol]['Symbol'].replace(reqId, symbol, inplace=True)
    #     print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
    #
    # def historicalDataUpdate(self, reqId, bar):
    #     global historical_data_dict
    #     symbol = tickers_df.loc[reqId, 'ticker']
    #     dict = {'Symbol': symbol, 'time': dt.datetime.strptime(bar.date, "%Y%m%d %H:%M:%S"), 'Open': bar.open,
    #             'High': bar.high, 'Low': bar.low,
    #             'Close': bar.close, 'Volume': bar.volume, 'Average': bar.average}
    #     # all_cols = ['ReqId', 'time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'SMA9', 'SMA20', 'SMA50', 'SMA200']
    #     cols = ['Symbol', 'time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average']
    #     df = historical_data_dict[symbol][cols] # get ticker's df from dict
    #     df = df.append(dict, ignore_index=True)
    #     # df = calc_SMAs(df) - Calc only in triggers functions
    #     historical_data_dict[symbol] = df
    #     print("HistoricalDataUpdate. ReqId:", reqId, "BarData.", bar)


    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        global historical_data_df
        global last_historical_reqId
        symbol = tickers_df.loc[reqId, 'ticker']
        historical_data_df['Symbol'].replace(reqId, symbol, inplace=True)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        last_historical_reqId = reqId

    def historicalDataUpdate(self, reqId, bar):
        global historical_data_df
        symbol = tickers_df.loc[reqId, 'ticker']
        dict = {'Symbol': symbol, 'time': dt.datetime.strptime(bar.date, "%Y%m%d %H:%M:%S"), 'Open': bar.open,
                'High': bar.high, 'Low': bar.low,
                'Close': bar.close, 'Volume': bar.volume, 'Average': bar.average}
        # all_cols = ['ReqId', 'time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'SMA9', 'SMA20', 'SMA50', 'SMA200']
        cols = ['Symbol', 'time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average']
        df = historical_data_df[historical_data_df['Symbol'] == symbol][cols]
        df = df.append(dict, ignore_index=True)
        # df = calc_SMAs(df) - Calc only in triggers functions
        historical_data_df = df
        print("HistoricalDataUpdate. ReqId:", reqId, "BarData.", bar)

    def historicalTicks(self, reqId, ticks, done):
        for tick in ticks:
            print("HistoricalTick. ReqId:", reqId, tick)

    def historicalTicksBidAsk(self, reqId, ticks, done):
        for tick in ticks:
            print("HistoricalTickBidAsk. ReqId:", reqId, tick)

    def historicalTicksLast(self, reqId, ticks, done):
        for tick in ticks:
            print("HistoricalTickLast. ReqId:", reqId, tick)
    # ----------------------------


# ====================================================================
# --------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# ------ Trading strategy functions ------

def calc_SMAs(df):
    df['SMA9'] = df['Close'].rolling(9).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['SMA200'] = df['Close'].rolling(200).mean()
    df.dropna(inplace=True)
    return df

# Random triggers for now
def dbg_get_triggers_df(stock_historical_df, trig_df):
    # ---- debug ----
    dict = {'Symbol': 'T', 'time': dt.datetime.now(), 'signal_type': 'SMA9xSMA50', 'handled': False}
    trig_df = trig_df.append(dict, ignore_index=True)
    return trig_df
    # ---------------
    # debug
    # rnd = rand.randint(0, 10 * stocks_df.__len__())
    # rnd = rand.randint(0, 1 * stocks_df.__len__())
    # if rnd >= stocks_df.__len__():
    #     return None
    #
    # # debug
    # trigger_flag = True
    # return stocks_df.iloc[[rnd]]

def get_new_triggers(stock_historical_df, trig_df):
    # buy signal when FAST crosses up the SLOW
    # TODO: sell when FAST crosses down the MID
    symbol = stock_historical_df['Symbol'].unique()[0]

    # if trigger already exists for this Symbol - skip
    if trig_df.Symbol.isin([symbol]).any():
        return trig_df

    stock_historical_df = calc_SMAs(stock_historical_df)
    # check where fast SMA up-crosses slower SMA --> up trend
    fast_SMA = stock_historical_df['SMA9']
    slow_SMA = stock_historical_df['SMA50']
    up_crossing_indx = np.where(np.diff(np.sign(fast_SMA-slow_SMA)))
    # get most recent signal
    last_trigger = stock_historical_df.iloc[up_crossing_indx[0]].iloc[-1]

    # check if trigger is too old
    if isinstance(last_trigger.time, str):
        last_trigger_dt = dt.datetime.strptime(last_trigger.time, "%Y-%m-%d %H:%M:%S")
    else:
        last_trigger_dt = last_trigger.time
    trigger_in_timeframe = last_trigger_dt > (dt.datetime.now() - TRIGGER_TIME_WINDOW)
    if not trigger_in_timeframe:
        return trig_df

    # at this point this is a valid trigger
    dict = {'Symbol':symbol, 'time': last_trigger_dt, 'signal_type': 'SMA9xSMA50', 'handled': False}
    trig_df = trig_df.append(dict, ignore_index=True)
    return trig_df


def is_restricted(ticker, quantity):
    if quantity < 1:
        return True
    if quantity * get_stock_price(ticker) > MAX_POSITION_DOLLARS:
        return True
    return False

    if ib.position_exists(ticker):  # if position exists don't buy more
        return True
    if ib.open_positions_total_value() >= MAX_TRADING_FUNDS:  # Max funds invested - don't invest more
        return True
    if dt.datetime.now().time() < FIRST_TRADING_TIME:  # Too early in the day - don't buy yet
        return True
    if dt.datetime.now().time() > LAST_TRADING_TIME:  # Too late in the day - don't buy anymore today
        return True
    # TODO: price too high? (can't buy Google for 2,500$)
    # TODO: add more filters: Volume? other indicators (RSI? over-bought?) Volatility? Sudden high price increase?
    # TODO: think about ticker reputation - aggregate our history and experince with this ticker
    # TODO: too many positions in the same industry?
    # TODO: What time is it? Market almost closed? Do we want to buy late in the day?
    return False


def time_to_close(position):
    if dt.datetime.now() - position.time > POSITION_MAX_TIME:
        return True
    return False


def get_tracked_tickers(filename):
    try:
        tickers_df = pd.read_csv(filename)
    except:
        nan_list = [np.nan] * len(tickers_list)
        tickers_dict = {'ticker': tickers_list, 'last_price': nan_list, 'bid': nan_list, 'ask': nan_list, 'type': 'STK'}
        tickers_df = pd.DataFrame(tickers_dict)
    return tickers_df


def get_last_triggers(filename):
    try:
        triggers_df = pd.read_csv(filename)
    except:
        trig_cols = ['Symbol','time','signal_type','handled']
        triggers_df = pd.DataFrame(columns=trig_cols)
    return triggers_df


def get_available_funds():
    global available_funds
    available_funds.ILS = 0
    available_funds.USD = 0
    available_funds.EUR = 0
    # get current funds available
    ib_app.reqAccountUpdates(True, IB_ACCOUNT_NUMBER)
    # wait for available cash data to return from TWS
    while not (available_funds.ILS or available_funds.USD or available_funds.USD):
        time.sleep(1)
    return

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ==================================================
# ====================== init ======================
# ==================================================
print("Begin - Init")
# set the tickers to trade:
tickers_df = get_tracked_tickers('tracked_tickers_stocks.csv')
triggers_df = get_last_triggers('triggers_stocks.csv')

# start IB App:
ib_app = IB_App()
ib_app.connect(TWS_IP_ADDR, TWS_PORT, TWS_CLIENT_ID)
ib_thread = Thread(target=run_ib_app, args=(ib_app,))
ib_app.nextOrderId = None
ib_thread.start()
# wait_for_connection()
# ------ wait for connection ------
# TODO: fix connection miss issue
time.sleep(3)
while True:
    if isinstance(ib_app.nextOrderId, int):
        print('connected')
        break
    else:
        print('waiting for connection')
        time.sleep(1)

# TODO: get live market data subscription https://www.interactivebrokers.com/en/index.php?f=4945&p=tradingpermissions
# get market data for tracked stocks
# set historical data df to track stocks history and moving average
historical_columns = ['Symbol', 'time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Average']
historical_data_df = pd.DataFrame(columns=historical_columns)
# historical_data_dict = {}
# for sym in tickers_list:
#     exec("historical_data_dict['{0}'] = pd.DataFrame(columns=historical_columns)".format(sym))

ib_app.reqMarketDataType(4)  # switch to delayed-frozen if live isn't available
if DEBUG:
    historical_data_df = pd.read_csv('historical_data.csv', index_col=False)
else:
    last_historical_reqId = -1
    for tickerId, row in tickers_df.iterrows():  # request stream data for tracked stocks
        contract = ib_app.create_nasdaq_contract(row['ticker'])
        # ib_app.reqMktData(tickerId, contract, "", False, False, [])
        # ib_app.reqHistoricalData(ib_app.nextOrderId, contract, endDateTime="",
        #                          durationStr="10 D", barSizeSetting="1 min", whatToShow="TRADES", useRTH=1,
        #                          formatDate=1, keepUpToDate=True, chartOptions=[])
        ib_app.reqHistoricalData(tickerId, contract, endDateTime="",
                                 durationStr="3 M", barSizeSetting="30 mins", whatToShow="TRADES", useRTH=1,
                                 formatDate=1, keepUpToDate=True, chartOptions=[])

        # queryTime = (dt.datetime.today() - dt.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")
        # ib_app.reqHistoricalData(ib_app.nextOrderId, contract, queryTime,"1 M", "1 day", "MIDPOINT", 1, 1, False, [])

    while last_historical_reqId < tickerId:
        time.sleep(10)
print("Done - Historical data")
# init available cash
available_funds = Funds()
get_available_funds()

# subscribe to get current stock positions + updates
stock_positions_columns = ['Symbol', 'SecType', 'Currency', 'Position', 'Avg_cost']
stock_positions_df = pd.DataFrame(columns=stock_positions_columns)
initial_position_update_done = False
ib_app.reqPositions()
while not initial_position_update_done:
    time.sleep(5)
print("Done - Position update")
stock_positions_df.set_index('Symbol', inplace=True)

print("Done - Init")
# ==========================================================
# ========================== Main ==========================
# ==========================================================

# # debug
# trigger_flag = True;


while True:
    # get triggers for each tracked ticker
    for tickerId, row in tickers_df.iterrows():
        ticker_df = historical_data_df[historical_data_df['Symbol'] == row.ticker]
        # if DEBUG:
        #     triggers_df = dbg_get_triggers_df(ticker_df, triggers_df)
        # else:
        if not ticker_df.empty:
            triggers_df = get_new_triggers(ticker_df, triggers_df)


    # get unhandled triggers
    triggers_df = triggers_df[triggers_df['handled']==False]
    trigger_flag = not triggers_df.empty
    if trigger_flag:
        trigger_flag = False
        # TODO: Clean up triggers_df and check for restricted triggers
        if (triggers_df is not None) and (triggers_df.count()['Symbol'] > 0):  # if there are relevant messages:
            for ticker in triggers_df.Symbol.unique():
                # id = a unique number from df to track this ticker's callbacks
                ticker_id = get_ticker_id(ticker=ticker)
                # last_price = get_stock_price(ticker=ticker)  # FB stock price = ~240
                # debug:
                last_price = dbg_get_stock_price(ticker=ticker)
                if math.isnan(last_price):
                    triggers_df = triggers_df[triggers_df['Symbol']!=ticker]
                    continue
                while not (last_price > 0):
                    time.sleep(3)
                    last_price = get_stock_price(ticker=ticker)

                # how much to buy
                quantity = math.floor(DEFAULT_POSITION_VALUE / last_price)  # 1,000$/240$ = 4 stocks

                # skip restricted tickers
                if is_restricted(ticker, quantity):
                    # strategy restrictions prevent buying this ticker
                    # TODO: clear_trigger(ticker)
                    continue

                # buy stock @ Market price
                order_id = ib_app.send_order(order_action="BUY", order_type="MKT", quantity=quantity, sec_type="STK",
                                             ticker=ticker)

                # TODO: verify order execution in Callback function

                # wait for the next order ID
                ib_app.reqIds(numIds=1)
                while (ib_app.nextOrderId == order_id):
                    continue

                # TODO: only if prev order executed - Sell trail
                # set trailing stop & take profit
                order_id = ib_app.send_order(order_action="SELL", order_type="TRAIL", trail_percent=2,
                                             quantity=quantity, sec_type="STK", ticker=ticker)
                # TODO: Change order to GTC
                # TODO: verify order execution in Callback function

                # subtract money invested from total allowed / update open positions / update executed orders
                # TODO: Move this to execution callback
                # invested_funds -= quantity * exec_price
                # restrictions = update_restrictions(quantity*exec_price)

            # delete all rows in triggers df after all is handled
            triggers_df.drop(triggers_df.index, inplace=True)

    # for position in ib.get_open_positions():  # for each open position:
    #     if time_to_close(position):
    #         ib.close_position(position.id)

    # time.sleep(SLEEP_SECONDS)

# ------------------------------------------------------------------

import datetime as dt
import time
import pandas as pd
import random as rand
import math
import numpy as np

# Global variables
tickers_list = ['AAPL','TSLA','CL','JETS','FB','INTL','BA','T']     # tickers to trade on
trigger_flag = False
SLEEP_SECONDS = 30
# POSITION_MAX_TIME = dt.timedelta(minutes=120)
TWS_IP_ADDR = "127.0.0.1"
TWS_PORT = 7497     # 7497 - paper account
TWS_CLIENT_ID = 0

ALLOCATION_PERCENT = 0.1            # How much stocks to buy - 10% of total portfolio
MAX_TRADING_FUNDS = 10000         # Total value of positions - Don't invest more then this
DEFAULT_POSITION_VALUE = ALLOCATION_PERCENT * MAX_TRADING_FUNDS  # 10% * 10,000$ = 1,000$
FIRST_TRADING_TIME = dt.time(11,00) # Don't buy before this hour
LAST_TRADING_TIME = dt.time(15,00)  # Don't after before this hour


# =================== Functions ===================
def get_stock_price(ticker):
    if ticker is None:
        return None
    last_price = tickers_df[tickers_df['ticker'] == ticker]['last_price'].iloc[0]
    return last_price


def get_ticker_id(ticker):
    if None == ticker:
        return None
    ticker_id = tickers_df[tickers_df['ticker'] == ticker].index[0]
    return ticker_id


def update_price(ticker_index, price_type, price):
    global tickers_df
    tickers_df.iloc[ticker_index,tickers_df.columns.get_loc(price_type)] = price


# --- Trading strategy functions ---
# Random triggers for now
def get_triggers_df(stocks_df):
    #TODO: create SMA20 triggers
    rnd = rand.randint(0, 10*stocks_df.__len__())
    if rnd>=stocks_df.__len__():
        return None
    return stocks_df.iloc[rnd]


def strategy_restrictions(ticker):
    if ib.position_exists(ticker):                              # if position exists don't buy more
        return True
    if ib.open_positions_total_value() >= MAX_TRADING_FUNDS:    # Max funds invested - don't invest more
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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ====================== IB App ======================
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
from ibapi.ticktype import TickTypeEnum
from threading import Timer


def create_nasdaq_contract(ticker):
    contract = Contract()
    contract.symbol = row['ticker']
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "NASDAQ"
    return contract


# Callback overrides
class IB_App(EWrapper,EClient):
    def __init__(self):
        EClient.__init__(self,self)

    # EWrapper callback
    def error(self,reqId, errorCode, errorString):
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
        # ! [trailingstop]
        order = Order()
        order.action = action
        order.orderType = "TRAIL"
        order.totalQuantity = quantity
        order.trailingPercent = trailingPercent
        order.trailStopPrice = trailStopPrice
        # ! [trailingstop]
        return order

    # ---------------- stock price data ----------------
    # ! [tickprice]
    def tickPrice(self, reqId, tickType, price, attrib):
        print("TickPrice. TickerId:", reqId, "tickType:", TickTypeEnum.to_str(tickType),
              "Price:", price, "CanAutoExecute:", attrib.canAutoExecute,
              "PastLimit:", attrib.pastLimit, end=' ')

        # update stocks tracking table
        if TickTypeEnum.BID == tickType or TickTypeEnum.DELAYED_BID == tickType:
            update_price(reqId, 'bid', price)
        if TickTypeEnum.ASK == tickType or TickTypeEnum.DELAYED_ASK == tickType:
            update_price(reqId, 'ask', price)
        if TickTypeEnum.LAST == tickType or TickTypeEnum.DELAYED_LAST == tickType:
            update_price(reqId, 'last_price', price)

        if tickType == TickTypeEnum.BID or tickType == TickTypeEnum.ASK:
            print("PreOpen:", attrib.preOpen)
        else:
            print()
    # ! [tickprice]

    # ! [ticksize]
    def tickSize(self, reqId, tickType, size):
        print("TickSize. TickerId:", reqId, "TickType:", TickTypeEnum.to_str(tickType), "Size:", size)
    # ! [ticksize]
    # --------------------------------------------------

    # --- Assaf - IB Shortcuts ---
    def send_order(self, ticker, order_action, quantity, sec_type="STK", order_type="MKT", limit_price=None):
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
        order.lmtPrice = limit_price

        self.placeOrder(self.nextOrderId, contract, order)
        return self.nextOrderId
    # ----------------------------

# --------------------------------------------------------------------

# ====================== init ======================
# tickers to trade:
nan_list = [np.nan] * len(tickers_list)
tickers_dict = {'ticker':tickers_list, 'last_price':nan_list, 'bid':nan_list, 'ask':nan_list, 'type':'STK'}
tickers_df = pd.DataFrame(tickers_dict)

# IB App:
ib_app = IB_App()
ib_app.connect(TWS_IP_ADDR, TWS_PORT, TWS_CLIENT_ID)

ib_app.reqMarketDataType(4)  # switch to delayed-frozen if live isn't available
for tickerId, row in tickers_df.iterrows(): # request stream data for tracked stocks
    contract = create_nasdaq_contract(row['ticker'])
    ib_app.reqMktData(tickerId, contract, "", False, False)

ib_app.run()

# ====================== Main ======================
while(True):
    if trigger_flag:
        trigger_flag = False
        triggers_df = get_triggers_df(tickers_df)        # retrieve new tickers to buy
    if triggers_df.count()['ticker'] > 0:               # if there are relevant messages:
        for ticker in triggers_df['ticker'].unique():   # (buy position for each ticker)
            if strategy_restrictions(ticker):
                # strategy restrictions prevent buying this ticker
                # clear_trigger(ticker)
                continue

            # id = a unique number from df to track this ticker's callbacks
            ticker_id = get_ticker_id(ticker=ticker)
            # get last price
            last_price = get_stock_price(ticker=ticker)                 # FB stock price = ~240
            quantity = math.floor(DEFAULT_POSITION_VALUE/last_price)    # 1,000$/240$ = 4 stocks

            # buy stock
            order_id = ib_app.send_order(ticker=ticker, order_action="BUY", quantity=quantity, sec_type="STK", order_type="MKT")
            # TODO: send order?
            # set trailing stop & take profit
            ib_app.TrailingStop(action="SELL", quantity=position, trailingPercent=2)
            ib.set_stop_loss(position_id)
            ib.set_take_profit(position_id)
            ib.send_order()

            # subtract money invested from total allowed / update open positions / update executed orders
            # TODO: Move this to execution callback
            invested_funds -= quantity*exec_price
            # restrictions = update_restrictions(quantity*exec_price)

    for position in ib.get_open_positions():                # for each open position:
        if time_to_close(position):
            ib.close_position(position.id)

    time.sleep(SLEEP_SECONDS)

# ------------------------------------------------------------------


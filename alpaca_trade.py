import argparse
import pandas as pd
import numpy as np
import alpaca_trade_api as tradeapi
from time import sleep
from datetime import date
import configparser
import os
import mysql.connector as mysql
from datetime import datetime

# loading configuration file
config = configparser.ConfigParser()
config.read('config.ini')
key_id = config["DEFAULT"]["APCA_API_KEY_ID"]
secret_id = config["DEFAULT"]["APCA_API_SECRET_KEY"]
live_key_id = config["DEFAULT"]["LIVE_APCA_API_KEY_ID"]
live_secret_id = config["DEFAULT"]["LIVE_APCA_API_SECRET_KEY"]

os.environ["APCA_API_KEY_ID"] = live_key_id
os.environ["APCA_API_SECRET_KEY"] = live_secret_id

# loading database information from config file
host = config["DEFAULT"]["HOST"]
user = config["DEFAULT"]["DATABASE_USERNAME"]
password = config["DEFAULT"]["PASSWORD"]
dbname = config["DEFAULT"]["DATABASE_NAME"]

# loading filename
file_name = config["DEFAULT"]['FILE_NAME']

# order method
order_method = config["DEFAULT"]["ORDER_METHOD"]


args_group = []
symbol_group = []
current_date = date.today()


# connecting to the database using 'connect()' method
db = mysql.connect(
    host = host,
    user = user,
    passwd = password,
    database = dbname
)
cursor = db.cursor()


def run(args):
    symbol = args.symbol
    opts = {}
    if args.key_id:
        opts['key_id'] = args.key_id
    if args.secret_key:
        opts['secret_key'] = args.secret_key
    if args.base_url:
        opts['base_url'] = args.base_url
    elif 'key_id' in opts and opts['key_id'].startswith('PK'):
        opts['base_url'] = 'https://paper-api.alpaca.markets'
    # Create an API object which can be used to submit orders, etc.
    api = tradeapi.REST(**opts)

    #Check opeing Market
    if not api.get_clock().is_open:
        print('Market is closed.  Try again later.')
        return
    
    # Get current price from polygon api
    polygon_data = tradeapi.REST(live_key_id, live_secret_id).polygon.snapshot(symbol)
    current_price = polygon_data.ticker['lastQuote']['P']
    max_dollars = args.max_dollar
    open_price = polygon_data.ticker['day']['o']
    high_price = polygon_data.ticker['day']['h']
    low_price = polygon_data.ticker['day']['l']
    previous_close_price = polygon_data.ticker['prevDay']['c']

    print("symbol==", symbol, "current_price==", current_price)

   
    # Intial sell and buy price
    buy_above_open_price = 0
    sell_above_open_price = 0
    buy_below_open_price = 0
    sell_below_open_price = 0
    buy_below_high_price = 0
    sell_below_high_price = 0
    buy_above_low_price = 0
    sell_above_low_price = 0
    buy_below_previous_close_1 = 0
    sell_below_previous_close_1 = 0
    buy_below_previous_close_2 = 0
    sell_below_previous_close_2 = 0
    buy_price = 0
    sell_price = 0
    
    # Get buy price and sell price
    if args.buy_price > 0:
        buy_price = args.buy_price
        sell_price = args.sell_price
    elif args.buy_above_open_price > 0:
        buy_above_open_price = float(open_price) * (1 + args.buy_above_open_price/100)
        sell_above_open_price = float(buy_above_open_price) * (1 + args.sell_above_open_price/100)
    elif args.buy_below_open_price > 0:
        buy_below_open_price = float(open_price) * (1 - args.buy_below_open_price/100)
        sell_below_open_price = float(buy_below_open_price) * (1 + args.sell_below_open_price/100)
    elif args.buy_below_high_price > 0:
        buy_below_high_price = float(high_price) * (1 - args.buy_below_high_price)
        sell_below_high_price = float(buy_below_high_price) * (1 + args.sell_below_high_price)
    elif args.buy_above_low_price > 0:
        buy_above_low_price = float(low_price) * (1 + args.buy_above_low_price)
        sell_above_low_price = float(buy_above_low_price) * (1 + args.sell_above_low_price)
    elif args.buy_below_previous_close_1 > 0:
        buy_below_previous_close_1 = float(previous_close_price) * (1 - args.buy_below_previous_close_1)
        sell_below_previous_close_1 = float(buy_below_previous_close_1) * (1 + args.sell_below_previous_close_1)
    elif args.buy_below_previous_close_2 > 0:
        buy_below_previous_close_2 = float(previous_close_price) * (1 + args.buy_below_previous_close_2)
        sell_below_previous_close_2 = float(buy_below_previous_close_2) * (1 + args.sell_below_previous_close_2)
    print(buy_price, sell_price, sell_below_previous_close_2, buy_below_previous_close_2, sell_below_previous_close_1, buy_below_previous_close_1, buy_above_open_price, sell_above_open_price, buy_below_open_price, sell_below_open_price, buy_below_high_price, sell_below_high_price, buy_above_low_price, sell_above_low_price, )
    # Get current symbol position
    current_status = get_postion(symbol, api.list_positions())
    trade_num = int(get_trade_num(symbol)[0][2])
    quantity = int(max_dollars / current_price)

    if trade_num < args.max_number:
        if current_status == '':
            if buy_price > 0 and current_price <= buy_price:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_price', current_price, 'sell_price', sell_price, quantity, max_dollars)
                    return
                else:
                    return
            elif buy_above_open_price > 0 and current_price <= buy_above_open_price:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_above_open_price', current_price, 'sell_above_open_price', sell_above_open_price, quantity, max_dollars)
                    return
                else:
                    return
            elif buy_below_open_price > 0 and current_price <= buy_below_open_price:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_below_open_price', current_price, 'sell_below_open_price', sell_below_open_price, quantity, max_dollars)
                    return
                else:
                    return
            elif buy_below_high_price > 0 and current_price <= buy_below_high_price:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_below_high_price', current_price, 'sell_below_high_price', sell_below_high_price, quantity, max_dollars)
                    return
                else:
                    return
            elif buy_above_low_price > 0 and current_price <= buy_above_low_price:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_above_low_price', current_price, 'sell_above_low_price', sell_above_low_price, quantity, max_dollars)
                    return
                else:
                    return
            elif buy_below_previous_close_1 > 0 and current_price <= buy_below_previous_close_1:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_below_previous_close_1', current_price, 'buy_below_previous_close_1', sell_below_previous_close_1, quantity, max_dollars)
                    return
                else:
                    return
            elif buy_below_previous_close_2 > 0 and current_price <= buy_below_previous_close_2:
                order_id = buy(symbol, quantity, current_price, api)
                if order_id != False:
                    current_postion_id = get_postion(symbol, api.list_positions())
                    insert_trade_data(current_postion_id, symbol, 'buy_below_previous_close_2', current_price, 'sell_below_previous_close_2', sell_below_previous_close_2, quantity, max_dollars)
                    return
                else:
                    return

        else:
            positions = api.list_positions()
            order_id = ''
            recode_sell_price = 0
            for position in positions:
                if position.symbol == symbol:
                    order_id = position.asset_id
                    break
            for x in range(4, 17, 2):
                if get_trade_history(order_id)[0][x] != None: 
                   recode_sell_price = get_trade_history(order_id)[0][x]
                   break
            if recode_sell_price <= current_price:
                quantity = get_trade_history(order_id)[0][17]
                status_sell = sell(symbol, quantity, current_price, api)
                if status_sell == True:
                    update_trade_data(order_id)
                    trade_num_update = trade_num + 1
                    update_trade_num(symbol, trade_num_update)

   
def buy(symbol, quantity, price, api):
    try:
        if order_method == '1':
            o = api.submit_order(
                symbol=symbol, qty=quantity, side='buy',
                type='limit', time_in_force='day',
                limit_price=str(price)
            )
            print('Buy at', price, symbol, flush=True)
            while True:
                current_postion_id = get_postion(symbol, api.list_positions())
                if current_postion_id != '':
                    print('----', current_postion_id)
                    return o.id
            
        else:
            o = api.submit_order(
                symbol=symbol, qty=quantity, side='buy',
                type='market', time_in_force='day',
            )
            print('Buy at', price, symbol, flush=True)
            while True:
                current_postion_id = get_postion(symbol, api.list_positions())
                if current_postion_id != '':
                    print('----', current_postion_id)
                    return o.id
    except Exception as e:
        print(e)
        return False

def sell(symbol, quantity, price, api):
    try:
        if order_method == 1:
            o = api.submit_order(
                symbol=symbol, qty=quantity, side='sell',
                type='limit', time_in_force='day',
                limit_price=str(price)
            )
            print('Sell at', price, symbol, flush=True)
            return True
        else:
            o = api.submit_order(
                symbol=symbol, qty=quantity, side='sell',
                type='market', time_in_force='day',
            )
            print('Sell at', price, symbol, flush=True)
            return True
    except Exception as e:
        print(e)
        return False

def delete_table():
    global cursor
    query = 'DELETE FROM trading_number_per_day'
    cursor.execute(query)
    db.commit()

def format_trade_num(alpaca_stocks):
    delete_table()
    global cursor
    for alpaca_stock in alpaca_stocks:
        query = "INSERT INTO trading_number_per_day (symbol, max_num, trade_num, trade_time) VALUES (%s, %s, %s, %s)"
        values = (alpaca_stock['Symbol'], alpaca_stock['Max Number of Trades Per Day'],  0, datetime.now())
        cursor.execute(query, values)
        db.commit()

def get_postion(symbol, positions):
    current_postion_id = ''
    for position in positions:
        if position.symbol == symbol:
            current_postion_id = position.asset_id
            break
    return current_postion_id

def get_trade_num(symbol):
    global cursor
    query = "SELECT * FROM trading_number_per_day WHERE symbol = '" + symbol + "'"
    cursor.execute(query)
    trade_num = cursor.fetchall()
    return trade_num

def  update_trade_num(symbol, trade_num):
    global cursor
    print(trade_num)
    query = "UPDATE trading_number_per_day SET trade_num = '" + str(trade_num) + "', trade_time = '" + str(current_date) + "' WHERE symbol = '" + symbol + "'"
    cursor.execute(query)
    db.commit()

def insert_trade_data(id, symbol, buy, buy_price, sell, sell_price, quantity, max_dollars):
    global cursor
    query = "INSERT INTO trading_history (stock_id, symbol, " + buy + ", " + sell + ", stock_num, max_dollars, start_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (id, symbol, buy_price, sell_price, quantity, max_dollars, str(datetime.now()))
    print(values)
    cursor.execute(query, values)
    db.commit()

def update_trade_data(id):
    global cursor
    current_time = str(datetime.now())
    query = "UPDATE trading_history SET end_time = '" + current_time +"' WHERE stock_id = '" + id + "'"
    cursor.execute(query)
    db.commit()

def get_trade_history(order_id):
    global cursor
    query = "SELECT * FROM trading_history WHERE stock_id = '" + order_id + "'"
    cursor.execute(query)
    trade_history = cursor.fetchall()
    return trade_history


if __name__ == '__main__':

    # Read excel data from .xlsx file
    excel_data = pd.read_excel(file_name, sheet_name='Sheet1')
    alpaca_stocks = excel_data.to_dict(orient='record')
    format_trade_num(alpaca_stocks)
    while True:
        for alpaca_stock in alpaca_stocks:
            parser = argparse.ArgumentParser()
            parser.add_argument(
                '--symbol', type=str, default=alpaca_stock['Symbol'],
                help='Symbol you want to trade.'
            )
            parser.add_argument(
                '--key-id', type=str, default=key_id,
                help='API key ID',
            )
            parser.add_argument(
                '--secret-key', type=str, default=secret_id,
                help='API secret key',
            )
            parser.add_argument(
                '--base-url', type=str, default='https://paper-api.alpaca.markets',
                help='set https://paper-api.alpaca.markets if paper trading',
            )
            parser.add_argument(
                '--buy-price', type=float, default=alpaca_stock['Buy At'],
                help='The price to buy',
            )
            parser.add_argument(
                '--sell-price', type=float, default=alpaca_stock['Sell At'],
                help='The price to sell',
            )
            parser.add_argument(
                '--max-dollar', type=int, default=alpaca_stock['Max Dollars'],
                help='Max Dollars of trading price'
            )
            parser.add_argument(
                '--max-number', type=int, default=alpaca_stock['Max Number of Trades Per Day'],
                help='Max Number of Trades Per Day'
            )
            parser.add_argument(
                '--trade-num', type=int, default=0,
                help='The number of trade'
            )
            parser.add_argument(
                '--status', type=str, default='buy',
                help='There status of ordfer buy or sell'
            )
            
            parser.add_argument(
                '--buy-above-open-price', type=float, default=alpaca_stock['Buy above open'],
                help=''
            )
            parser.add_argument(
                '--sell-above-open-price', type=float, default=alpaca_stock['Sell above buy D'],
                help=''
            )
            parser.add_argument(
                '--buy-below-open-price', type=float, default=alpaca_stock['Buy below the open'],
                help=''
            )
            parser.add_argument(
                '--sell-below-open-price', type=float, default=alpaca_stock['Sell above buy F'],
                help=''
            )
            parser.add_argument(
                '--buy-below-high-price', type=float, default=alpaca_stock['Buy below the high'],
                help=''
            )
            parser.add_argument(
                '--sell-below-high-price', type=float, default=alpaca_stock['Sell above buy H'],
                help=''
            )
            parser.add_argument(
                '--buy-above-low-price', type=float, default=alpaca_stock['Buy above the low'],
                help=''
            )
            parser.add_argument(
                '--sell-above-low-price', type=float, default=alpaca_stock['Sell above buy J'],
                help=''
            )
            parser.add_argument(
                '--buy-below-previous-close-1', type=float, default=alpaca_stock['Buy below previous close'],
                help=''
            )
            parser.add_argument(
                '--sell-below-previous-close-1', type=float, default=alpaca_stock['Sell above buy L'],
                help=''
            )
            parser.add_argument(
                '--buy-below-previous-close-2', type=float, default=alpaca_stock['Buy above previous close'],
                help=''
            )
            parser.add_argument(
                '--sell-below-previous-close-2', type=float, default=alpaca_stock['Sell above buy N'],
                help=''
            )
            args = parser.parse_args()
            run(args)

        # Delay time
        # sleep(20)

        # trade number format if come to new day
        if current_date != get_trade_num(alpaca_stocks[0]['Symbol'])[0][3]:
            format_trade_num(alpaca_stocks)
           
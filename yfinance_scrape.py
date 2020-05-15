import yfinance as yf
import datetime
import json
from basecode import DBconnection

def get_stock_info(list_of_stocks):
    main_dict = {}
    for stocks in list_of_stocks:
        try:
            stock = yf.Ticker(stocks)
        except:
            return "error"
        
        L2_dict = {'52WeekChange': '', 'dividendYield': '', 'marketCap': '', 'currency': '', 'previousClose': '',
                   'regularMarketOpen': '', 'regularMarketPrice': '', 'updated_as_of': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        for keystock, valuestock in stock.info.items():
            for key in L2_dict.keys():
                if keystock == key:
                    L2_dict[key] = valuestock
        main_dict[stocks] = L2_dict
        if check_for_existing_stock(stocks):
            sql_statement = """UPDATE stock_data SET data_stored = %s, last_updated = %s where stock_id = %s"""
            sql_run = (json.dumps(L2_dict),datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stocks)
        else:
            sql_statement = """INSERT INTO stock_data (stock_id, data_stored, last_updated) VALUES(%s,%s,%s)"""
            sql_run = (stocks, json.dumps(L2_dict), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        DBconnection(sql_statement, sql_run)

        L2_dict = {'52WeekChange': '', 'dividendYield': '', 'marketCap': '', 'currency': '', 'previousClose': '',
                   'regularMarketOpen': '', 'regularMarketPrice': '', 'updated_as_of': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    return


def check_for_existing_stock(stock_id):
    exist = True
    sql_statement = """SELECT stock_id FROM stock_data where stock_id in (%s)"""
    sql_run = (stock_id)
    output = DBconnection(sql_statement, sql_run)
    if output == ():
        exist = False
    return exist

get_stock_info(['MSFT', 'GOOG', 'FB'])
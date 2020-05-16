import datetime
import pymysql.cursors
import json
import requests
from bs4 import BeautifulSoup


def DBconnection(sql_statement, input_data):
    conn = pymysql.connect(
        'database-1.cqifbqu4xgne.ap-southeast-1.rds.amazonaws.com', 'admin', 'password', 'XTASFinanceBot')

    with conn:
        cur = conn.cursor()
        cur.execute(sql_statement, input_data)
        rows = cur.fetchall()
        return rows


def get_stock_info(stock_id):
    panels = ["D(ib) W(1/2) Bxz(bb) Pend(12px) Va(t) ie-7_D(i) smartphone_D(b) smartphone_W(100%) smartphone_Pend(0px) smartphone_BdY smartphone_Bdc($seperatorColor)",
              "D(ib) W(1/2) Bxz(bb) Pstart(12px) Va(t) ie-7_D(i) ie-7_Pos(a) smartphone_D(b) smartphone_W(100%) smartphone_Pstart(0px) smartphone_BdB smartphone_Bdc($seperatorColor)"]

    web_link = 'https://sg.finance.yahoo.com/quote/' + stock_id + '?p=' + stock_id
    source = requests.get(web_link, timeout=5).text
    soup = BeautifulSoup(source, 'lxml')

    main_dt = {}
    data_arr = []
    try:
        # *Getting current price and changes
        stock_names = soup.find('h1', class_="D(ib)").text
        stock_name = stock_names.split(" - ")[1]
        price = soup.find('span', class_="Trsdu(0.3s)").text
        change = soup.find('span', class_="Fw(500)").text
        change = change.split(" ")
        change[1] = change[1].lstrip("(").rstrip(")")

        # *Getting time of price and market status
        time = soup.find('div', class_="Fw(n)").span.text
        time = time.split(" ")
        current_time = time[3] + " " + time[4].rstrip(".")

        main_dt['Stock Name'] = stock_name
        main_dt['Current Price'] = price
        main_dt['Change'] = change[0]
        main_dt['Relative Change'] = change[1]
        main_dt['Time at close'] = current_time

        # *Start of panel scraping
        for class_name in panels:
            match = soup.find('div', class_=class_name)
            eachdata = match.findAll('tr')
            for tr in eachdata:
                td = tr.findAll('span')
                if len(td) != 2:
                    ran = tr.find('td', class_="Ta(end)")
                    td.append(ran)
                for i in td:
                    texts = i.text
                    if "," in texts:
                        texts = texts.split(",")
                        texts = "".join(texts)
                    if "\n" in texts:
                        texts = texts.split("\n")
                        a = texts[0]
                        a += " " + texts[1].strip()
                        data_arr.append(a)
                    else:
                        data_arr.append(texts)
            for i in range(1, len(data_arr), 2):
                main_dt[data_arr[i - 1]] = data_arr[i]

        return main_dt
    except:
        return


def check_for_existing_stock(stock_id):
    exist = True
    sql_statement = """SELECT stock_id FROM stock_data where stock_id in (%s)"""
    sql_run = (stock_id)
    output = DBconnection(sql_statement, sql_run)
    if output == ():
        exist = False
    return exist


def iterate_stocks(list_of_stocks):
    error_stocks = []
    for stock in list_of_stocks:
        main_dt = get_stock_info(stock)
        if main_dt == None:
            error_stocks.append(stock)
            continue
        else:
            # data cleaning
            if (main_dt['PE ratio (TTM)'] == 'N/A' or '∞' in main_dt['PE ratio (TTM)']):
                main_dt['PE ratio (TTM)'] = 0

            if (main_dt['EPS (TTM)'] == 'N/A' or '∞' in main_dt['EPS (TTM)']):
                main_dt['EPS (TTM)'] = 0

            if main_dt['Forward dividend & yield'].split(" ")[0] == 'N/A':
                main_dt['Forward dividend & yield'] = None
            else:
                main_dt['Forward dividend & yield'] = float(
                    main_dt['Forward dividend & yield'].split(" ")[0])

            if (main_dt['Market cap']) == 'N/A':
                main_dt['Market cap'] = None
            # data cleaning end

            # inserting into database
            if check_for_existing_stock(stock):
                sql_statement = """UPDATE stock_data SET stock_name = %s, current_price = %s, 52weekrange = %s, market_cap = %s, pe_ratio = %s,
                eps = %s, fdy = %s, last_updated = %s, data_stored = %s where stock_id = %s"""

                sql_run = (main_dt['Stock Name'], float(main_dt['Current Price']), main_dt['52-week range'], main_dt['Market cap'],
                           float(main_dt['PE ratio (TTM)']), float(main_dt['EPS (TTM)']), main_dt['Forward dividend & yield'], datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"), json.dumps(main_dt), stock)

            else:
                sql_statement = """INSERT INTO stock_data (stock_id, stock_name current_price, 52weekrange, market_cap, pe_ratio,
                eps, fdy, last_updated, data_stored) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                sql_run = (stock, main_dt['Stock Name'], float(main_dt['Current Price']), main_dt['52-week range'], main_dt['Market cap'],
                           float(main_dt['PE ratio (TTM)']), float(main_dt['EPS (TTM)']), main_dt['Forward dividend & yield'], datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"), json.dumps(main_dt))
            DBconnection(sql_statement, sql_run)
            # inserting to database end

    if len(error_stocks) > 0:
        rtnstr = ""
        for x in range(len(error_stocks)):
            if x == len(error_stocks) - 1:
                rtnstr += "'" + str(error_stocks[x]) + "'"
            else:
                rtnstr += "'" + str(error_stocks[x]) + "'" + ", "
        return "There is(are) no stock named: " + rtnstr + "."


iterate_stocks([
    'U11.SI',
    'BTOU.SI',
    'GANR.SI',
    'B69.SI',
    'BRWY.SI',
    '5WH.SI',
    'N4E.SI',
    'I5H.SI',
    'WEST.SI',
    '5EC.SI',
    'O9E.SI',
    'CIPH.SI',
    'F34.SI',
    'A17U.SI',
    'C31.SI',
    'Z74.SI',
    'BN4.SI',
    'C09.SI',
    'C38U.SI',
    'V03.SI',
    'Y92.SI',
    'C61U.SI',
    'S63.SI',
    'BS6.SI',
    'D05.SI',
    'O39.SI',
    'G13.SI',
    'N21U.SI',
    'U14.SI',
    'C52.SI',
    'M44U.SI',
    'H78.SI',
    'S68.SI',
    'T39.SI',
    'U96.SI',
    'D01.SI',
    'C6L.SI',
    'S58.SI',
    'J36.SI',
    'C07.SI',
    'J37.SI'
])

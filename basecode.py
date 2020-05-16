import calendar
import datetime
import json
import os
import random
import time as t
import urllib
from uuid import uuid4

import pymysql.cursors
import requests
import telebot
# from fpdf import FPDF
from telegram.ext import CommandHandler, Filters, MessageHandler, updater
import ast

 
# with open('bottoken.txt','r') as tokenFile:
#     bot_token = tokenFile.read()
# bot = telebot.TeleBot(token = '1148932024:AAESzyLUTt8XBq_RgaNQMMgJuAX63C1YjZw')
bot = telebot.TeleBot(token = '1001700627:AAHw7pyoArTRO2V33eQk4u0KsN6Kr8FIe0U')

def DBconnection(sql_statement, data):
    conn = pymysql.connect('database-1.cqifbqu4xgne.ap-southeast-1.rds.amazonaws.com','admin','password','XTASFinanceBot')
    
    with conn:
        cur = conn.cursor()
        cur.execute(sql_statement, data)
        
        rows = cur.fetchall()

        data = []
        for row in rows:
            data.append(row)
        return data

def DBconnection2(sql_statement):
    conn = pymysql.connect('database-1.cqifbqu4xgne.ap-southeast-1.rds.amazonaws.com','admin','password','XTASFinanceBot')
    
    with conn:
        cur = conn.cursor()
        cur.execute(sql_statement)
        
        rows = cur.fetchall()

        data = []
        for row in rows:
            data.append(row)
        return data



def updateFinancialInstrumentsTable():
    dropIfExists = "DROP TABLE IF EXISTS financial_instruments"
    DBconnection2(dropIfExists)

    createTable = "CREATE TABLE financial_instruments (symbol varchar(10), unit_price decimal(10,0), dividend_yield varchar(45), PRIMARY KEY (symbol))"
    DBconnection2(createTable)

    retrieveFromStockTable = "select * from stock_data"
    stockDataList = DBconnection2(retrieveFromStockTable)
    lastData = stockDataList[0][-1]
    startPos = lastData.find("Forward dividend & yield")
    lastData = lastData[startPos:]
    lastData = lastData.split(":")
    forwardDivYield = lastData[-1].strip("}")

    for stockData in stockDataList:
        stockId = stockData[0]
        stockPrice = stockData[2]
        lastData = stockData[-1]
        startPos = lastData.find("Forward dividend & yield")
        lastData = lastData[startPos:]
        lastData = lastData.split(":")
        forwardDivYield = lastData[-1].strip("}")
        forwardDivYield = forwardDivYield.strip()
        if forwardDivYield != "null":
            divYield = float(forwardDivYield) / stockPrice
            divYield *= 100
        else:
            divYield = 0
        
        statement = "INSERT INTO financial_instruments (symbol, unit_price, dividend_yield) VALUES(%s, %s, %s)"
        sql_run = (stockId, stockPrice, divYield)
        DBconnection(statement, sql_run)


@bot.message_handler(commands=['matrix'])
def call_matrix(message):

    userid = message.chat.id
    select_risk_level = "select risk_level from questionnaire where attempt = (select max(attempt) from questionnaire where userid = %s)  and userid = %s"
    sql_run = (userid, userid)
    risk_level = DBconnection(select_risk_level,sql_run)
    if risk_level:
        risk_level = risk_level[0][0]
    else:
        bot.reply_to(message,"Please ensure that you have completed your risk-assessment quiz.\nType /invest to learn more.")
        return

    select_capital = "Select capital from telegramusers where userid = %r"
    capital = DBconnection(select_capital,userid)
    if capital:
        capital = float(capital[0][0])
    else:
        bot.reply_to(message,"Please ensure that you have stated your investment value.\nType /invest to learn more.")
        return

        
    updateFinancialInstrumentsTable()

    matrix(userid, risk_level, capital) 


def matrix(userid, risk_level, capital):

    num_instruments = 0

    if capital <= 10000:
        num_instruments = 4
    elif capital <= 20000:
        num_instruments = 5
    elif capital <= 49999:
        num_instruments = 7
    elif capital <= 99999:
        num_instruments = 14
    else:
        num_instruments = 17

    if (risk_level == 'low'):
        sql_statement = 'SELECT * from financial_instruments where dividend_yield <= %s'
        data = DBconnection(sql_statement, 3)
    elif (risk_level == 'moderate'):
        sql_statement = 'SELECT * from financial_instruments where dividend_yield >= %s and dividend_yield <= %s'
        data = DBconnection(sql_statement, (4, 10))
    elif (risk_level == 'high'):
        sql_statement = 'SELECT * from financial_instruments where dividend_yield >= %s'
        data = DBconnection(sql_statement, 11)

    sorted_dividends = sorted(data, key=lambda dividend: dividend[2], reverse=True) 
    chosen_stocks = sorted_dividends[:num_instruments]
    if len(chosen_stocks) <= 0:
        bot.send_message(userid, "Sorry. We are unable to find any matching financial instrument for your portfolio.")
        return 
    sql_run = []
    print(f'sorted_dividends = {sorted_dividends}')
    portfolioid = None

    check_if_user_exists_statement = "SELECT * from portfolio where userid = %s ORDER BY portfolioid DESC"
    sql_run = userid
    result = DBconnection(check_if_user_exists_statement,sql_run)

    if result:
        portfolioid = result[0][1] + 1
    else:
        portfolioid = 1

    print(f'portfolioid is {portfolioid}')
    usable_capital = capital/2
    first_stock_allocated = False
    second_usable_capital = usable_capital / (num_instruments - 1)
    counter = 0
    print(f'chosen_stocks is {chosen_stocks}')
    for stock_details in chosen_stocks:
        counter += 1
        symbol = stock_details[0]
        purchase_price = float(stock_details[1])
        lot_size = 0
        if first_stock_allocated == False:
            lot_size = (usable_capital // purchase_price)
            first_stock_allocated = True
        else:
            lot_size = (second_usable_capital // purchase_price)
        print(f'lotsize is {lot_size}')
        insert_into_portfolio = "INSERT INTO portfolio (userid, portfolioid, symbol, purchase_price, lot_size) VALUES(%s, %s, %s, %s, %s)"
        sql_run = (userid, portfolioid, symbol, purchase_price, lot_size)
        DBconnection(insert_into_portfolio, sql_run)
        print("inserted into portfolio")

def questionaire(userid):
    risk_level = ''
    sql_statement = "SELECT * from telegramusers where userid = %s"
    sql_run = userid
    conn = DBconnection(sql_statement, sql_run)
    if (conn == ''):
        sql_statement = "INSERT INTO telegramusers (userid, risk_level,capital) VALUES(%s,%s,%s)"
        sql_run = (userid,'', 0)
        data = DBconnection(sql_statement,sql_run)
        #Add in questionaires here
    else:
        #Need to do the questionaires here to determine risk level
        sql_statement = "UPDATE telegramusers SET risk_level = %r"
        sql_run = ()
    #use telegram userid to get risk level
    return risk_level
 
@bot.message_handler(commands=['start'])
def send_welcome(message):
    userid = message.chat.id
    first_sql_statement = "SELECT * from telegramusers where userid = %s"
    first_sql_run = userid
    first = DBconnection(first_sql_statement,first_sql_run)
    if first:
        username = message.chat.first_name
        bot.reply_to(message, 'Welcome back ' + str(username) + '! type /information to find out more.\nType /commands to see all commands available.')
    else:
        sql_statement = """INSERT INTO telegramusers (userid, risk_level,capital) VALUES(%s,%s,%s)"""
        sql_run = (userid, '', 0)
        data = DBconnection(sql_statement, sql_run)
        bot.reply_to(message, 'Im a Finance Advisor Bot created by Xiuling, Timothy, Aaron & Sean, type /information to find out more.')
        

@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message,"type /begin to start your risk level questionaire, /invest to dermarcate the amount you are intending to invest, /view to view various financial instruments after your risk appetite has been determined and your current investment has been captured.")


@bot.message_handler(commands=['report'])
def send_report(message):
    userid = message.chat.id
    sql_statement = "Select max(portfolioid) from portfolio where userid = %s"
    check = DBconnection(sql_statement,userid)
    #print(check[0][0])
    double_check = "select count from portfolio_link where portfolioid = %s"
    retrieve_count = DBconnection(double_check,check[0][0])
    #print(retrieve_count)
    #print("this is retrieve count")

    if check: #and retrieve_count != 1:
        generatePDF(userid)
        bot.reply_to(message,"Here is a detailed analysis and suggested financial instruments for you, " + message.chat.first_name)
        doc = open(str(userid) +'.pdf','rb')
        bot.send_document(userid,doc)
        bot.send_document(userid, "FILEID")
      #  sql = "SELECT max(portfolioid) from portfolio where userid = %s"
       # sqlstatement = """INSERT INTO portfolio_link (portfolioid, pdf_link,count) VALUES(%s,%s,%s)"""
       # insert_statement = (check[0][0], str(userid) + '.pdf', 1)
     #   insert = DBconnection(sqlstatement,insert_statement)
    else:
        print("not check")
        bot.reply_to(message,"Im sorry, " + message.chat.first_name + " you do not satisfy the requirements for a detailed report yet.")
        
#############################################################################################################################################


@bot.message_handler(commands=['begin'])
def questionnaire_1(message):
    #insert ID into database
    userid = message.chat.id
    sql_run= userid

    if_attempt_exist_statment= 'select attempt from questionnaire where userid=%s'

    if DBconnection(if_attempt_exist_statment,sql_run):
        attempt= DBconnection(if_attempt_exist_statment,sql_run)
        num_attempt= int(attempt[-1][0])
        new_attempt= num_attempt+1
        sql_run= (new_attempt, userid)
        sql_statement = "Insert into questionnaire (attempt,userid) values(%s,%s)"
        DBconnection(sql_statement,sql_run)

    else:
        sql_run= (1, userid)
        sql_statement = "Insert into questionnaire (attempt,userid) values(%s,%s)"
        DBconnection(sql_statement,sql_run)

    option1={'Always stop at yellow no matter what.':11,'Break and stop at the light. You’re late anyway, right?':21,'You blow through that sucker!':31}

    keyboard = telebot.types.InlineKeyboardMarkup() 
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )

    bot.send_message(
    message.chat.id,
    'You are driving to meet some friends. You’re running late. The traffic light ahead turns yellow. What will you do?' + 
    "Next question: /Q2",
    reply_markup=keyboard
    )




@bot.message_handler(commands=['Q2'])
def questionnaire_2(message):

    option1={'Hear this stuff all the time, know it’s not true and ignore her.':12,'Nod, squint your eyes, log onto E*Trade and invest a grand.':22,'Take 5k of that money you had for a rainy day and invest.':32}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    'Your friend gives you a tip. She heard this stock is gonna go through the roof in the next week. What is your reaction?'+
    "Next question: /Q3",
    reply_markup=keyboard
    )



    
    
@bot.message_handler(commands=['Q3'])
def questionnaire_3(message):

    option1={'Look at your wedding ring, order yourself another drink and continue on with your conversation.':13,
    'Envision a plan where if the stars aligned and you were both at the bar at the same time you would definitely have something to talk about.':23,
    'Immediately excuse yourself and head across the room.':33}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    'You are a really cool cocktail party. Your spouse is home. You see this seriously smoking hottie across the room. What will you do?'+
    "Next Question: /Q4",
    reply_markup=keyboard
    )

    
@bot.message_handler(commands=['Q4'])
def questionnaire_4(message):

    option1={'Put your head down in shame.':14,'Chuckle with most of the crowd.':24,
    'Realize this is your time to shine and head up to the front.':34}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    'It’s the dreaded annual company Christmas party.'+
    'The COO is a little enebriated and asks if anyone else would like to get up to attest to the company’s good fortune. What will you do?'+
    "Next Question: /Q5",
    reply_markup=keyboard
    )

    
@bot.message_handler(commands=['Q5'])
def questionnaire_5(message):

    option1={'Leave':15,'Stick around to see the free show.':25,
    'Exclaim, “Heck, I’ve got ten bucks!” And get in line.':35}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    "You’re with a friend in Thailand. You walk into this interesting tent. In the center is a cobra in a cage. People are queued up to pay ten dollars for a chance to grab the five one-hundred dollar bills on top of the snake's cage. You:"+
    "Next Question: /Q6",
    reply_markup=keyboard
    )



@bot.message_handler(commands=['Q6'])
def questionnaire_6(message):

    option1={'Thank him politely and inside your head you can’t wait for the plane to land.':16,
    'C Give him your business card and ask for his, knowing full well this guy is full of crap.':26,
    'You try to find a polite way to tell him his body odor offends.':36}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    "You’re sitting next to this old man on the airplane. It’s obvious he hasn’t showered and he sleeps through the beverage service. When he wakes up he starts talking to you, his ramblings culminate with him explaining how he can help your business. What will you do?"+
    "Next Question: /Q7",
    reply_markup=keyboard
    )


@bot.message_handler(commands=['Q7'])
def questionnaire_7(message):

    option1={'Decide it’s better to wait until you have more of a cushion.':17,
    'Buy the property and hope for the best.':27,
    'Are so convinced the deal is so good, you buy two. The other with money from a 2nd mortgage on your home.':37}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    "You’ve spent time researching the perfect part of town to buy a rental property. You think you have all your bases covered, but investing in this property will definitely put you and your family out there. What will you do?"+
    "Next Question: /Q8",
    reply_markup=keyboard
    )

@bot.message_handler(commands=['Q8'])
def questionnaire_8(message):

    option1={'Tell your friends you’ll greet them when they get back.':18,
    'Go to the front desk and hire a car and recommendations on the best places to drink in town.':28,
    'Are the first one tethered to the cord.':38}

    keyboard = telebot.types.InlineKeyboardMarkup()
    for key in option1:
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                key, callback_data= option1[key]
            )
        )
        
    bot.send_message(
    message.chat.id,
    "Today is your birthday and you are on vacation in the Bahamas to celebrate. Everyone has been drinking and the gang decides it’s the perfect time to rent mopeds from the front desk and go bungee jumping. What will you do?"+
    "To view results: /results",
    reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
    userid = query.from_user.id

    data = query.data
    question= 'Qn'+ str(data[-1])
    sql_run = (data[0], userid)
    sql_statement= "update questionnaire set " + question + "= %s where userid=%s and " + question+ " is null;"
    DBconnection(sql_statement,sql_run)



@bot.message_handler(commands=['results'])
def results(message):
    userid = message.chat.id
    sql_run= userid
    sql_statement= "select qn1+qn2+qn3+qn4+qn5+qn6+qn7+qn8 from questionnaire, (select max(time_completed) as t from questionnaire where userid= %s) as temp where time_completed=temp.t;"
    total_number_tuple=DBconnection(sql_statement,sql_run)
    total_number= total_number_tuple[0][0]
    

    if total_number<=12:
        risk_level= "low"
    elif total_number<=18:
        risk_level="moderate"
    else:
        risk_level="high"
    

    sql_run=(risk_level,userid)
    sql_statement_risk= "update questionnaire set risk_level = %s where userid= %s and risk_level is null;"

    DBconnection(sql_statement_risk,sql_run)

    bot.reply_to(message, "Base on the questionnire you are a "+ risk_level + "risk taker. Please input your desired amount for investment under /invest")

    sql_statement= "update telegramusers set risk_level= %s where userid= %s;"
    DBconnection(sql_statement,sql_run)



############################################################################################################################################



@bot.message_handler(commands=['invest'])
def send_invest(message):
    userid = message.chat.id
    sql_statement = "Select capital from telegramusers where userid = %r"
    conn = DBconnection(sql_statement,userid)

    bot.reply_to(message, "Your current capital investment is $" + str(conn[0][0]) + ". If you would like to change the amount simply type invest amount for example invest $100000, we will update you with a new investment portfolio accordingly")


@bot.message_handler(content_types=['text'])
def setCapital(message):
    userid = message.chat.id
    sql_statement = ""
    msg = message.text.lower()
    msg = msg.strip()
    if (msg[:6] == 'invest'):
        amount = msg[6:].strip()
        if (amount.isdigit() == False):
            bot.send_message(userid, "Please make sure your investment value consists of only digits.")
        else:
            amount = float(amount)
            sql_statement = """UPDATE telegramusers SET capital = %s where userid = %s"""
            sql_run = (amount, userid)
            DBconnection(sql_statement, sql_run)
            bot.send_message(userid, "Your investment value has been demarcated.")


#'chat': {'id': 907456913, 'first_name': 'ExpediteSG', 'username': 'EXPEDITESG', 'type': 'private'}, 'date': 1589559756, 'text': 'Invest $50000'}}
def findCapital(msg):
    for word in msg:
        if '$' in msg:
            return word

@bot.message_handler(func=lambda msg:msg.text is not None and '$' in msg.text)
def getCapital(message):
    userid = message.chat.id
    sentence = message.text.split()
    sentence = sentence[1]
    capital = sentence[1:]
    sql_statement = "UPDATE telegramusers set capital = %r where userid = %r"
    data = (float(capital), userid)
    conn = DBconnection(sql_statement,data)
    
    bot.reply_to(message, "Your intended initial investment has been recorded, we will soon send you a collated financial instruments for you.")



def generatePDF(userid):
    sql_statement = "SELECT symbol, purchase_price, lot_size from portfolio where userid = %s"
    data = userid
    connection = DBconnection(sql_statement,data)
    Symbol = [i[0] for i in connection]
    PurchasePrice = [i[1] for i in connection]
    Lot_Size = [i[2] for i in connection]

    pdf = FPDF()

#header of the pdf file
    header = 'Specifically curated for ' + str(userid)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    w = pdf.get_string_width(header) + 6
    pdf.set_x((210 - w) / 2)
    pdf.cell(w, 9, header, 0, 0, 'C')
    pdf.line(20, 18, 210-20, 18)

    pdf.ln(10)
    pdf.set_font('Times', '', 12)
    pdf.multi_cell(0, 5, 'Here is a list of suggested financial instruments for your peruse.')

    for i in range(len(Symbol)):
        pdf.ln()
        pdf.set_font('Arial', '', 12)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 6, 'Financial Instrument ' + str(i+1) + ": " + str(Symbol[i]) + " Unit Price " + str(PurchasePrice[i]) + " Lot Size " + str(Lot_Size[i]), 0 , 1, 'L', 1)

        pdf.ln()
        pdf.set_font('Courier', 'B', 12)
        pdf.multi_cell(0, 5, 'A detailed analysis on' + Symbol[i] + '---------------')
        

    #pdf.set_y(0) #on top of the page
    pdf.set_y(-30) #30 CM from the bottom of the page
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0)
    pdf.cell(0, 5, 'Page ' + str(pdf.page_no()), 0, 0, 'C')

    pdf.output(str(userid) +'.pdf', 'F')
    return pdf

@bot.message_handler(commands=['viewproposedproducts'])
def send_proposed(message):
    userid = message.chat.id
    sql_statement = "Select capital, risk_level from telegramusers where userid = %r"
    retrieved_data = DBconnection(sql_statement,userid)
    print(retrieved_data[0])

@bot.message_handler(commands=['commands'])
def display_commands(message):
    bot.reply_to(message, "The possible commands here are:\n /start \n /information \n /invest \n /viewproposedproducts")
    
while True:
    try:
        bot.polling()
    except Exception:
        t.sleep(15)

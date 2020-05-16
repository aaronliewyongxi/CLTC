from uuid import uuid4
from telegram.ext import updater, CommandHandler, MessageHandler, Filters
import telebot
import time as t
import datetime
import random
import urllib
import requests
import os
import json
import calendar
import pymysql.cursors
# import yfinance as yf

 
# with open('bottoken.txt','r') as tokenFile:
#     bot_token = tokenFile.read()
# bot = telebot.TeleBot(token = '1148932024:AAESzyLUTt8XBq_RgaNQMMgJuAX63C1YjZw')
bot = telebot.TeleBot(token = '1001700627:AAHw7pyoArTRO2V33eQk4u0KsN6Kr8FIe0U')

#Database connection and retrieving it accordingly by SQL_statement, it will then retrieve data in the form of a list
#Need to connect to cloud first -> because right now using localDB -> Inflexible
def DBconnection(sql_statement, data):
    conn = pymysql.connect('database-1.cqifbqu4xgne.ap-southeast-1.rds.amazonaws.com','admin','password','XTASFinanceBot')
    
    with conn:
        cur = conn.cursor()
        cur.execute(sql_statement, data)
        
        rows = cur.fetchall()
        print(rows)
        data = []
        for row in rows:
            data.append(row)
        return data

# def insert_DBconnection(sql_statement):
#     conn = pymysql.connect('database-1.cqifbqu4xgne.ap-southeast-1.rds.amazonaws.com','admin','password','XTASFinanceBot')
    
#     with conn:
#         cur = conn.cursor()
#         cur.execute(sql_statement)
        
#         rows = cur.fetchall()
#         # print(rows)
#         data = []
#         for row in rows:
#             data.append(row)
#         return data

# insert_DBconnection("INSERT INTO financial_instruments (symbol, unit_price, risk_level) VALUES('SXL', 520, 'low')")


#   /matrix
@bot.message_handler(commands=['matrix'])
def call_matrix(message):
    # fetch from db the risk_level of userid (message.chat.id) based on latest attempt
    userid = message.chat.id
    select_risk_level = "select risk_level from questionnaire where attempt = (select max(attempt) from questionnaire where userid = %s)"
    sql_run = userid
    risk_level = DBconnection(select_risk_level,sql_run)
    
    select_capital = "Select capital from telegramusers where userid = %r"
    capital = DBconnection(select_capital,userid)

    matrix(userid, risk_level, capital) #insert portfolio into db

def matrix(userid, risk_level, capital):
    # self-declared matrix function to suggest a variety of financial plans according to risk level
    # db risk_level = low, moderate, high, very high
    num_instruments = 0
    instruments_allocation = {    
                                10000: 4,
                                20000: 5,
                                49999: 7,
                                99999: 14,
                                100000: 17
    }
    if capital > 100000:
        num_instruments = instruments_allocation[100000]
    else:
        for key, value in instruments_allocation.items():
            if capital <= key:
                num_instruments = value

    # data is [ ('ABC', Decimal('5'), 3),
    #           ('SXL', Decimal('520'), 5), 
    #           ('XYZ', Decimal('2'), 11) ]
    
    # low dividend yield <= 3%
    # moderate dividend yield = 4% - 10%
    # high dividend yield >= 11% 

    if (risk_level == 'low'):
        sql_statement = 'SELECT * from financial_instruments where dividend_yield <= %s'
        data = DBconnection(sql_statement, 3)
    elif (risk_level == 'moderate'):
        sql_statement = 'SELECT * from financial_instruments where dividend_yield >= %s and dividend_yield <= %s'
        data = DBconnection(sql_statement, (4, 10))
    elif (risk_level == 'high'):
        sql_statement = 'SELECT * from financial_instruments where dividend_yield >= %s'
        data = DBconnection(sql_statement, 11)

    # now i need to sort the instruments into highest dividend yield to lowest dividend yield
    sorted_dividends = sorted(data, key=lambda dividend: dividend[2], reverse=True) 
    chosen_stocks = sorted_dividends[:num_instruments] #sieve out appropriate number of financial instruments

    sql_run = []
    # userid = 358771567
    portfolioid = None

    check_if_user_exists_statement = "SELECT * from portfolio where userid = %s ORDER BY portfolioid DESC"
    sql_run = userid
    result = DBconnection(check_if_user_exists_statement,sql_run)

    if result:
        portfolioid = result[0][1] + 1
    else:
        portfolioid = 1

    # allocate half of capital to top dividend yield stock
    # remaining half, split equally between remaining financial instruments
    usable_capital = capital/2
    first_stock_allocated = False
    for stock_details in chosen_stocks:
        symbol = stock_details[0]
        purchase_price = stock_details[1][0]

        if first_stock_allocated == False:
            lot_size = (usable_capital // purchase_price)
            first_stock_allocated = True
        else:
            usable_capital /= (num_instruments - 1)
            lot_size = (usable_capital // purchase_price)

        insert_into_portfolio = "INSERT INTO portfolio (userid, portfolioid, symbol, purchase_price, lot_size) VALUES(%s, %s, %s)"
        sql_run = (userid, portfolioid, symbol, purchase_price, lot_size)
        DBconnection(insert_into_portfolio, sql_run)

    # percentage = forward_dividend_yield / current_share_price

# matrix('low', 25000)


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
        # print(data)
        bot.reply_to(message, 'Im a Finance Advisor Bot created by Xiuling, Timothy, Aaron & Sean, type /information to find out more.')
        

@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message,"type /begin to start your risk level questionaire, /invest to dermarcate the amount you are intending to invest, /view to view various financial instruments after your risk appetite has been determined and your current investment has been captured.")


#############################################################################################################################################

@bot.message_handler(commands=['begin'])
def questionaire_1(message):

    option1={'Always stop at yellow no matter what.':1,'Break and stop at the light. You’re late anyway, right?':2,'You blow through that sucker!':3}

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


@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query, score=[]):
    data = query.data
    int_data=int(data)
    score += [int_data]
    print(score)

    if len(score)==4:
        total= sum(score)
        if total== 4:
            risk_level= "low"
        elif total<=6:
            risk_level='moderate'
        elif total<=8:
            risk_level='High'
        else:
            risk_level='Very High'

        return risk_level

    elif len(score)>4:
        score=[]
        print(score)
        print("hello")
    
    


@bot.message_handler(commands=['Q2'])
def questionaire_2(message):

    option1={'Hear this stuff all the time, know it’s not true and ignore her.':1,'Nod, squint your eyes, log onto E*Trade and invest a grand.':2,'Take 5k of that money you had for a rainy day and invest.':3}

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
def questionaire_3(message):

    option1={'Look at your wedding ring, order yourself another drink and continue on with your conversation.':1,
    'Envision a plan where if the stars aligned and you were both at the bar at the same time you would definitely have something to talk about.':2,
    'Immediately excuse yourself and head across the room.':3}

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
def questionaire_4(message):

    option1={'Put your head down in shame.':1,'Chuckle with most of the crowd.':2,
    'Realize this is your time to shine and head up to the front.':3}

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
    "To view results: /results",
    reply_markup=keyboard
    )

@bot.message_handler(commands=['results'])
def results(message):
    bot.reply_to(message, "Base on the questionnaire you are a __<need to extract the risk level>__ risk taker. Please input your desired amount for investment under /invest")



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

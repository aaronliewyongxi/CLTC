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
def questionnaire_4(message):

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
def questionnaire_4(message):

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
def questionnaire_4(message):

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
def questionnaire_4(message):

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

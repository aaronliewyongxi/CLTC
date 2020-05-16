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
import re
 
with open('bottoken.txt','r') as tokenFile:
    bot_token = tokenFile.read()
bot = telebot.TeleBot(token = bot_token)

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

def matrix(risk_level, capital):
    # self-declared matrix function to suggest a variety of financial plans according to risk level

    financial_instruments = []
    sql_statement = ''
    total_value = 0
    if(capital < 10000 & risk_level == 'low'):
        sql_statement = ['select financial_plans, total_value from plans where risk_level = %r']
        conn = "low"
        data = DBconnection(sql_statement, conn)
        financial_instruments = [data[0]]
        total_value = [data[1]]
        
    return financial_instruments
 
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
    bot.reply_to(message, "Your current capital investment is " + str(conn[0][0]) + ". If you would like to change the amount simply type invest amount for example invest $100000, we will update you with a new investment portfolio accordingly")
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

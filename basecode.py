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
from PyPDF2 import PdfFileReader
import pandas as pd
import matplotlib
from pylab import title, figure, xlabel, ylabel, xticks, bar, legend, axis, savefig
from fpdf import FPDF
 
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


@bot.message_handler(commands=['report'])
def send_report(message):
    userid = message.chat.id
    sql_statement = "Select * from portfolio where userid = %s"
    check = DBconnection(sql_statement,userid)
    if check:
        doc = open(str(userid) +'.pdf','rb')
        bot.send_document(userid,doc)
        bot.send_document(userid, "FILEID")

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



def generatePDF(userid):
    df = pd.DataFrame()
    sql_statement = "SELECT symbol, purchase_price, lot_size from portfolio where userid = %s"
    data = userid
    connection = DBconnection(sql_statement,data)
    print(connection)
    size_of_df = len(connection)
    print(size_of_df)

    df['Symbol'] = [connection[0][0],connection[0][1]]
    df['Purchase Price'] = [connection[0][1], connection[1][1]]
    df['Lot Size'] = [connection[0][2], connection[1][2]]

    title("Personalized Portfolio Analysis for" + str(userid))
    xlabel("Expected Growth Over One Year")
    ylabel("Predicted Stock Price")

    total_range = [2,4,6,8,10]
    m = [x - 0.5 for x in total_range]

    xticks(m, df['Symbol'])

    bar(m, df['Purchase Price'], width=0.5, color="#91eb87", label="Purchase Price")
    bar(total_range, df['Lot Size'], width=0.5, color="#eb879c", label="Lot Size")

    legend()
    axis([0, 10, 0, 8])
    savefig('barchart.png')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_xy(0, 0)
    pdf.set_font('arial', 'B', 12)
    pdf.cell(60)
    pdf.cell(75, 10, "A Sample Analysis of return on investment for " + str(userid), 0, 2, 'C')
    pdf.cell(90, 10, " ", 0, 2, 'C')
    pdf.cell(-40)
    pdf.cell(50, 10, 'Symbol', 1, 0, 'C')
    pdf.cell(40, 10, 'Purchase Price', 1, 0, 'C')
    pdf.cell(40, 10, 'Lot Size', 1, 2, 'C')
    pdf.cell(-90)
    pdf.set_font('arial', '', 12)
    for i in range(0, len(df)):
        pdf.cell(50, 10, '%s' % (df['Symbol'].iloc[i]), 1, 0, 'C')
        pdf.cell(40, 10, '%s' % (str(df.LotSize.iloc[i])), 1, 0, 'C')
        pdf.cell(40, 10, '%s' % (str(df.Purchase_price.iloc[i])), 1, 2, 'C')
        pdf.cell(-90)
    pdf.cell(90, 10, " ", 0, 2, 'C')
    pdf.cell(-30)
    pdf.image('barchart.png', x = None, y = None, w = 0, h = 0, type = '', link = '')
    pdf.output(str(userid) + '.pdf', 'F')
    
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

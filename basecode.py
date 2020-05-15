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
        data = []
        for row in rows:
            data.append(row)
        return data
 
def matrix(risk_level, capital):
    #self-declared matrix function to suggest a variety of financial plans according to risk level
    
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
        bot.reply_to(message, 'Welcome back' + str(username) + ' type /information to find out more')
    else:
        sql_statement = """INSERT INTO telegramusers (userid, risk_level,capital) VALUES(%s,%s,%s)"""
        sql_run = (userid, '', 0)
        data = DBconnection(sql_statement, sql_run)
        print(data)
        bot.reply_to(message, 'Im a Finance Advisor Bot created by Xiuling, Timothy, Aaron & Sean, type /information to find out more.')
        

@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message,"type /begin to start your risk level questionaire, /invest to dermarcate the amount you are intending to invest, /view to view various financial instruments")


@bot.message_handler(commands=['invest'])
def send_invest(message):
    userid = message.chat.id
    sql_statement = "Select capital from telegramusers where userid = %r"
    conn = DBconnection(sql_statement,userid)
    bot.reply_to(message, "Your current capital investment is " + conn[0] + ". If you would like to change the amount simply type invest amount for example invest $100000, we will update you with a new investment portfolio accordingly")
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

    

    
while True:
    try:
        bot.polling()
    except Exception:
        t.sleep(15)

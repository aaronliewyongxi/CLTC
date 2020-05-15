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
        sql_statement = ['select financial_plans, total_value from plans where risk_level = low']
        data = DBconnection(sql_statement)
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
        bot.reply_to(message, 'Welcome back' + str(userid) + ' type /information to find out more')
    else:
        sql_statement = """INSERT INTO telegramusers (userid, risk_level,capital) VALUES(%s,%s,%s)"""
        sql_run = (userid, '', 0)
        data = DBconnection(sql_statement, sql_run)
        print(data)
        bot.reply_to(message, 'Im a Finance Advisor Bot created by Xiuling, Timothy, Aaron & Sean, type /information to find out more.')
        

@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message,"type /begin to start your risk level questionaire, /invest to dermarcate the amount you are intending to invest, /view to view various financial instruments")

def findCapital(msg):
    sieveNumbers = [int(i) for i in msg if i.isdigit()]
    return sieveNumbers

@bot.message_handler(commands=['invest'])
def send_invest(message):
    userid = message.chat.id
    sql_statement = "SELECT capital from telegramusers where userid = %s"
    sql_data = userid
    conn = DBconnection(sql_statement,sql_data)
    capital = findCapital(message)
    
    if conn == 0 and capital == '':
        bot.reply_to(message,"We will choose selected financial instruments according to your investment, how much would you like to invest?, Please type /invest amount, for example /invest 50000")
    elif capital:
        sql_statement = "UPDATE telegramusers SET capital = %s where userid = %s"
        sql_data = (capital, userid)
        conn = DBconnection(sql_statement,sql_data)
    else:
        sql_statement = 'SELECT risk_level, capital from telegramusers where userid = %s'
        data_connect = userid
        result = DBconnection(sql_statement,data_connect)
        if result[0] == 'low': 
        #Ideally based on user's risk level, set a certain percentage to high risk stocks, mid risk stocks & low risk stocks
            sql_statement = 'SELECT stock_name, unit_price from financial_instruments where risk_level = %r'
            conn = "low"
            result = DBconnection(sql_statement,conn)
        elif result[0] == 'moderate':
            sql_statement  = "SELECT stock_name, unit_price from financial_instruments where risk_level = %r"
            conn = "moderate"
            result = DBconnection(sql_statement,conn)
        else:
            sql_statement  = "SELECT stock_name, unit_price from financial_instruments where risk_level = %r"
            conn = "high"
            result = DBconnection(sql_statement, conn)
while True:
    try:
        bot.polling()
    except Exception:
        t.sleep(15)

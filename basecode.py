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
 
# with open('bottoken.txt','r') as tokenFile:
#     bot_token = tokenFile.read()
bot = telebot.TeleBot(token = '1044274360:AAH8XZiyYx2aHnyOOAfXS1whKYp3x4IwOoA')
 
#Database connection and retrieving it accordingly by SQL_statement, it will then retrieve data in the form of a list
#Need to connect to cloud first -> because right now using localDB -> Inflexible
def DBconnection(sql_statement):
    conn = pymysql.connect('database-1.cqifbqu4xgne.ap-southeast-1.rds.amazonaws.com','admin','password','XTASFinanceBot')
    
    with conn:
        cur = conn.cursor()
        cur.execute(sql_statement)
        
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

    sql_keyword_dict = {}

    # risk_level: low, mid, high

    if(capital < 10000 and risk_level == 'low'):
        sql_statement = ['select financial_plans, total_value from plans where risk_level = low']
        data = DBconnection(sql_statement)
        financial_instruments = [data[0]]
        total_value = [data[1]]
        
    return financial_instruments
 
def questionaire(userid):
    risk_level = ''
    sql_statement = "SELECT * from telegramusers where userid = {userid}"
    conn = DBconnection(sql_statement)
    if (conn == ''):
        sql_statement = "INSERT INTO telegramusers (userid, risk_level,capital) VALUES({userid},'','')"
    else:
        #Need to do the questionaires here to determine risk level
        sql_statement = "UPDATE telegramusers SET risk_level = {risk_level}"
    #use telegram userid to get risk level
    return risk_level
 
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Im a Finance Advisor Bot created by Xiuling, Timothy, Aaron & Sean, type /information to find out more.')
 
@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message,"type /begin to start your risk level questionaire, /invest to dermarcate the amount you are intending to invest, /view to view various financial instruments")
 
@bot.message_handler(commands=['invest'])
def send_invest(message):
    bot.reply_to(message,"We will choose selected financial instruments according to your investment")
    sql_statement = 'SELECT risk_level from telegramusers'
    result = DBconnection(sql_statement)
 
    if result == 'low': 
        #Ideally based on user's risk level, set a certain percentage to high risk stocks, mid risk stocks & low risk stocks
        sql_statement = "SELECT stock_name, unit_price from financial_instruments where risk_level = low"
        result = DBconnection(sql_statement)
    elif result == 'moderate':
        sql_statement  = "SELECT stock_name, unit_price from financial_instruments where risk_level = moderate"
        result = DBconnection(sql_statement)
    else:
        sql_statement  = "SELECT stock_name, unit_price from financial_instruments where risk_level = high"
        result = DBconnection(sql_statement)
while True:
    try:
        bot.polling()
    except Exception:
        t.sleep(15)

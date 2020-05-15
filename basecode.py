rom uuid import uuid4
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
import mySQLdb

bot_token = '1044274360:AAH8XZiyYx2aHnyOOAfXS1whKYp3x4IwOoA'
bot = telebot.TeleBot(token = bot_token)
db = MySQLdb.connect(host="127.0.0.1",    # localhost
                 user="root",         #  username
                 passwd="",  #  password
                 db="xtasfinancebot")        # name of the data base
                 cur = db.cursor()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Im a Finance Advisor Bot created by Xiuling, Timothy, Aaron & Sean, type /information to find out more.')

@bot.message_handler(commands=['information'])
def send_information(message):
    bot.reply_to(message,"type /begin to start your risk level questionaire, /invest to dermarcate the amount you are intending to invest, /view to view various financial instruments")

@bot.message_handler(commands=['invest'])
def send_invest(message):
    bot.reply_to(message,"We will choose selected financial instruments according to your investment")
    result = cur.execute('SELECT risk_level from user')

    if result == 'low': 
        #Ideally based on user's risk level, set a certain percentage to high risk stocks, mid risk stocks & low risk stocks
        financial_products = [cur.execute("SELECT stock_name, unit_price from financial_instruments where risk_level = low")]
    elif result == 'moderate':
        financial_products = [cur.execute("SELECT stock_name, unit_price from financial_instruments where risk_level = moderate")]
    else:
        financial_products = [cur.execute("SELECT stock_name, unit_price from financial_instruments where risk_level = high")]
while True:
    try:
        bot.polling()
    except Exception:
        t.sleep(15)


def matrix(risk_level, capital):
    #self-declared matrix function to suggest a variety of financial plans according to risk level
    financial_instruments = []
    sql_statement = ''
    total_value = 0
    if(capital < 10000 & risk_level == 'low'):
        sql_statement = ['select financial_plans, total_value from plans where risk_level = low']
        financial_instruments = [sql_statement[0]]
        total_value = [sql_statement[1]]
        
    return financial_instruments

def questionaire(userid):
    risk_level = ''
    #use telegram userid to get risk level
    return risk_level
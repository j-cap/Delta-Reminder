
# Web scrapper to download all new Delta-Chat messages in whatsapp
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException

from simon.accounts.pages import LoginPage
from simon.header.pages import HeaderPage
from simon.chat.pages import ChatPage
from simon.chats.pages import PanePage

from bs4 import BeautifulSoup
import pprint
import os, sys
import smtplib
import pandas as pd
import datetime

_PATH = "data/"

def login():
    # Web scrapper for infinite scrolling page 
    driver = webdriver.Chrome(executable_path=r"C:/Users/jakob/chromedriver.exe")
    #driver.get("https://web.whatsapp.com/")
    time.sleep(2)  # Allow 2 seconds for the web page to open

    login_page = LoginPage(driver)
    login_page.load()
    input("Please use the QR-Code")
    return driver

def get_delta_chat(driver):
    # get all chats
    all_chats = driver.find_elements_by_class_name("_210SC") 
    # find DELTA
    for chat in all_chats:
        soup = BeautifulSoup(chat.text, "html.parser")
        if "DELTA" in soup.text:
            print("Found DELTA")
            driver.execute_script("arguments[0].scrollIntoView();", chat)
            delta_chat = chat
            break
    # click to focus
    delta_chat.click()
    return delta_chat

def scroll(driver, n_scrolls):
    for _ in range(n_scrolls):
        actions = ActionChains(driver)
        actions.send_keys(Keys.UP*10)
        actions.perform()
        time.sleep(0.2)
    
def create_datetime_from_msg(msg):
    
    time_and_autor = msg.raw_datetime_and_contact()

    t, a = time_and_autor.split("] ")
    time_, date = t[1:].split(", ")

    dt = datetime.datetime.strptime(time_+","+date, "%H:%M,%d.%m.%Y")
    return dt
        
def check_if_msg_already_in_df(msgs, dt_last_in_df):
    counter = 0
    for i, msg in enumerate(msgs):
        # print(f"Message nr. {i+1}")
        try:
            dt = create_datetime_from_msg(msg)
            # print(dt)
        except AttributeError:
            # print("Exception")
            dt = datetime.datetime.now()
            continue
            
        if dt == dt_last_in_df:
            print(f"Message on {dt.strftime('%H:%M, %d:%m:%y')} already in database -> break!")
            stop = True
            break
        else:
            stop = False
        counter += 1
    return stop, counter  


def merge_dataframes(msgs, chat_df, dt_last_in_df, save_=True):
    rows = []
    for _, msg in enumerate(msgs):
        try:
            dt = create_datetime_from_msg(msg)
            text = msg.text
            if text == None:
                text = "pic-or-gif"
            d1 = dict(Time=dt.strftime("%H:%M"), Date=dt.strftime("%d.%m.%y"), Author=msg.contact, Text=text, Text_lower=text.lower())
        except:
            pass
        if dt == dt_last_in_df:
            print(f"Message on {dt.strftime('%H:%M, %d:%m:%y')} already in database -> break!")
            break
        else:
            rows.append(d1)
    df_ = pd.DataFrame(rows)
    df_c = pd.concat([chat_df, df_.sort_index(ascending=False)], ignore_index=True)
    if save_:
        save_time = datetime.datetime.fromtimestamp(time.time())
        fname = f"chat_{save_time.strftime('%d_%m_%y')}.csv"
        print("Save Chat to ", _PATH+fname)
        df_c.loc[df_c["Text"].isnull()] = "000"
        df_c.to_csv(_PATH+fname)
    return df_c

def parse_chat(driver, datetime_lm, chat_df, speed=10):
    """Parse all new messages and save it by appending it to chat_df dataframe"""

    # find any message and click it
    msg = driver.find_element_by_xpath("/html/body/div[1]/div/div/div[4]/div/div[3]/div/div/div[3]/div[13]/div")
    msg.click()
    time.sleep(1)
    # scroll through the chat and check if the messages are already in the dataframe
    stop_scrolling = False
    while not stop_scrolling:

        scroll(driver=driver, n_scrolls=speed)    
        # use simon to extract all messages
        chatPage = ChatPage(driver)
        msgs = chatPage.messages.all()

        stop_scrolling, counter = check_if_msg_already_in_df(msgs, dt_last_in_df=datetime_lm)
        print("MESSAGE COUNTER AT ".ljust(50, "="), counter)  
    time.sleep(1)
    # generate the new dataframe and save it
    df = merge_dataframes(msgs=msgs, chat_df=chat_df, dt_last_in_df=datetime_lm, save_=True)
    return df


def check_sitzungen():
    """Read the file sitzungen.csv and check if there are planned Sitzungen. """
    df_s = pd.read_csv(_PATH+"sitzungen.csv")
    date = datetime.datetime.now()
    df_s["Date"]= pd.to_datetime(df_s["Date"], format="%d.%m.%y")
    new_dates = df_s[df_s["Date"] > date]
    if not new_dates.empty:
        print("We have planned meetings!")
    return new_dates
    
def send_mails(dates, send_to=False, pw=None):
    
    from email.message import EmailMessage

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    # sender_mail = "weberjakob64@gmail.com"
    sender_mail = "delta.base.vienna@gmail.com"
    server.login(sender_mail, password=pw)
    body = f"Subject: Reminder: Naechste Sitzung. Die naechste Sitzung ist von Type {dates.iloc[-1]['Type']} am {dates.iloc[-1]['Date'].strftime('%d.%m.%y')}"
   
    if send_to:
        msg = EmailMessage()
        msg["From"] = sender_mail
        msg["Subject"] = body   
        msg["To"] = send_to
        print("Sending email to %s..."%send_to)
        server.send_message(msg)
    else:
        mgl = pd.read_csv(_PATH+"mgl_list.csv")
        for email_to in mgl["Email"]:
            print("Sending email to %s..."%email_to)
            msg = EmailMessage()
            msg["From"] = sender_mail
            msg["Subject"] = body   
            msg["To"] = email_to
            server.send_message(msg)
    
    server.quit()
    print("Finished")


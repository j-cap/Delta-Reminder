
import datetime
import time
import pandas as pd
from utils_deltachat import login, get_delta_chat, scroll
from utils_deltachat import create_datetime_from_msg, check_if_msg_already_in_df
from utils_deltachat import merge_dataframes, PATH, parse_chat
from utils_deltachat import check_sitzungen, send_mails

def main():


    # get the chat dataframe and the last message
    chat_df = pd.read_csv(PATH+"chat_21_09_20.csv", index_col="idx")
    last_message_time_and_date = chat_df.iloc[-1]["Time"], chat_df.iloc[-1]["Date"]
    datetime_lm = datetime.datetime.strptime(last_message_time_and_date[0]+","+last_message_time_and_date[1], "%H:%M,%d.%m.%y")

    print("Login to Whatsapp web using QR-Code".center(100, "="))
    driver = login()
    time.sleep(1)

    # get the delta chat
    delta_chat = get_delta_chat(driver=driver)
    time.sleep(1)
    # parse the chat and save new msg to the existimg dataframe chat_df
    df = parse_chat(driver=driver, datetime_lm=datetime_lm, chat_df=chat_df, speed=10)

#mgl = pd.read_csv(PATH+"mgl_list.csv")
#df_s = pd.read_csv(PATH+"sitzungen.csv")
# date = datetime.datetime(year=2020, month=12, day=2)
#date = datetime.datetime.now()
#df_s["Date"]= pd.to_datetime(df_s["Date"], format="%d.%m.%y")
#new_meetings = df_s[df_s["Date"] > date]

    
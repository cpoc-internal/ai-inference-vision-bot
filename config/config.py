import os
from  pathlib import Path
import datetime
import logging
import streamlit as st

def pathfile():
    parent_dir = "./"
    path = os.path.join(parent_dir)
    THIS_FOLDER = os.path.abspath(path)
    return THIS_FOLDER

def parent_path():
    parent_path = Path("./")
    return parent_path

def config_path():
    parent_path = Path("./config")
    return parent_path

def assets_path():
    parent_path = Path("./config/assets")
    return parent_path

def services_path():
    parent_path = Path("./services")
    return parent_path

def img_path():
    parent_path = Path("./services/img")
    return parent_path

def date_now():
    now= datetime.utcnow()
    return now
        
def clock():
    while True:
        timer =datetime.now().strftime("%H:%M:%S")
        return timer
    
def logs(info):
    try:
        logging.basicConfig(filename=f'{parent_path()}/logs.txt', level=logging.INFO, format='%(asctime)s %(message)s')
        logging.info(info)
    except Exception as e:
        ('Error saving logs'+ str(e))

def clear_history():
        st.session_state.messages = []
from sanic import Sanic, Blueprint
import asyncio
import MySQLdb
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import pyodbc
import os

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

logname = f'logs/polytama-dev.log'
handler = TimedRotatingFileHandler(logname, when="midnight", interval=1)
handler.setFormatter(formatter)
handler.suffix = "%Y-%m-%d"
logger = logging.getLogger('')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

handlerOut = logging.StreamHandler()
handlerOut.setLevel(logging.INFO)
handlerOut.setFormatter(formatter)
logger.addHandler(handlerOut)

SQLCONNECT = True
while(SQLCONNECT):
    '''
    TRYING CONNECT TO THE DATABASE
    IF THERE'S NO RESPONE FROM DATABSE
    LOOPING WILL ACTIVE UNTIL CONNECTED TO DATABASE
    '''
    try:
        mydb = MySQLdb.connect(host="127.0.0.1", user="root", db="polytama_dev", port=3306)

        logger.info("[MYSQL]         :   SUCCESCFULLY CONNECTED to MYSQL")
        cursor = mydb.cursor()
        sqlip = "SELECT ip, port, dbname, dbport, dbuid, dbpass FROM ipserver"
        cursor.execute(sqlip)
        dat = cursor.fetchone()
        SERVER = f'{dat[0]},{dat[3]}'
        dbname = f'{dat[2]}'
        dbuid = f'{dat[4]}'
        dbpwd = f'{dat[5]}'
        conn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}',
                                       server=SERVER,
                                       database=dbname,
                                       uid=dbuid,pwd=dbpwd)
        cursorsql = conn.cursor()
        logger.info("[SQL SERVER]    :   SUCCESCFULLY CONNECTED to SQL SERVER")
        # URL_ALARM = f'http://{dat[0]}'
        SQLCONNECT = False
    except:
        logger.info("[SQL SERVER]    :   NOT CONNECTED")
        time.sleep(5)

app = Sanic(__name__)


from gateway_dock.views import gateway

gateRoute = Blueprint.group(gateway, url_prefix='')
app.blueprint(gateRoute)

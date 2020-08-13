from sanic import Sanic, request, Blueprint
from sanic.response import json, text
from datetime import datetime, date, timedelta
import time
import asyncio
from gateway_dock import cursor, app, mydb, logger
from gateway_dock.config import reconMysql, reconnenctToDbServer, getIPdisplay
from gateway_dock.sendServer import sendErrorBook
import requests_async as requests
gateway = Blueprint('gateway', url_prefix='')


async def trySendBooking():
    await asyncio.sleep(5)
    trySend = await sendErrorBook()
    if not trySend:
        app.add_task(trySendBooking())

app.add_task(reconnenctToDbServer())
app.add_task(reconMysql())


@gateway.route("/dock/booking/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    now = datetime.now()
    data_dock = dict(eval(request.body.decode('utf-8')))
    logger.info(f"[DATA IN]       :  {data_dock}")
    # print(database.is_connected)
    try:
        updateBOOKING = "UPDATE loading_dock SET UID = %s, STATUS = %s, POLICE_NO = %s, LAST_UPDATE = %s  WHERE ID = %s"
        valBOOKING = [data_dock['uidRfid'].upper(), "BOOKING", data_dock['policeNo'].upper(), str(now), int(dockCode)]
        cursor.execute(updateBOOKING,valBOOKING)
        logger.info(f'[BOOKING]       :   {valBOOKING}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   UPDATE TO DOCK {dockCode} ERROR')
    try:
        updateBookingLog = "INSERT INTO log_server (UID, STATUS, DOCK, POLICE_NO, TIME, DATA) VALUES (%s, %s, %s, %s, %s, %s)"
        valBookingLog = data_dock['uidRfid'].upper(), "BOOKING", int(dockCode), data_dock['policeNo'].upper(), str(now), "IN"
        cursor.execute(updateBookingLog, valBookingLog)
        logger.info(f'[BOOKING]       :   {valBookingLog}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   INSERT TO LOG ERROR')
    ipDisplay = await getIPdisplay(dockCode)
    policeNumber = data_dock['policeNo'].upper()
    URL_BOOK = f'http://{ipDisplay}/booking/{policeNumber}'
    try:
        logger.info(f'[BOOKING]       :   SEND GET {URL_BOOK}')
        rBooking = await requests.get(URL_BOOK, timeout = 2)
        logger.info(f'[BOOKING]       :   SUCCESCFULLY SEND GET TO DISPLAY')
    except:
        logger.error(f'[BOOKING]      :   SEND TO DISPLAY ERROR')
        pullBookError = "INSERT INTO send_error (URL, TIME, SEND_STATUS) VALUES (%s, %s, %s)"
        valBookError = URL_BOOK, str(now), "BOOKING"
        cursor.execute(pullBookError, valBookError)
        logger.error(f'[BOOKING]      :   SAVE TO DB PULLING')
        app.add_task(trySendBooking())

    mydb.commit()
    return text('OK')

@gateway.route("/dock/stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/start/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')



@gateway.route("/dock/alarm-stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/alarm-start/<num>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/LD/HF/<dockCode>", methods=['GET','POST'])
async def dockIdHF(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    dataEPC = request.body.decode('utf-8')
    return text('OK')

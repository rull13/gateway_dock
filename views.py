from sanic import Sanic, request, Blueprint
from sanic.response import json, text
from datetime import datetime, date, timedelta
import time
import asyncio
from gateway_dock import cursor, app, mydb, logger
from gateway_dock.config import reconMysql, reconnenctToDbServer, getIPdisplay, getIPServer
from gateway_dock.sendServer import sendErrorDisplay, sendErrorTapIn
import requests_async as requests
gateway = Blueprint('gateway', url_prefix='')


async def trySendDisplay():
    await asyncio.sleep(5)
    trySend = await sendErrorDisplay()
    if not trySend:
        app.add_task(trySendDisplay())

async def trySendHfServer():
    await asyncio.sleep(5)
    trySendHF = await sendErrorTapIn()
    if not trySendHF:
        app.add_task(trySendHfServer())

app.add_task(reconnenctToDbServer())
app.add_task(reconMysql())


@gateway.route("/dock/booking/<dockCode>", methods=['GET','POST'])
async def dockBook(request, dockCode):
    now = datetime.now()
    data_dock = dict(eval(request.body.decode('utf-8')))
    logger.info(f"[DATA IN]       :  {data_dock}")
    # print(database.is_connected)
    try:
        updateBOOKING = "UPDATE loading_dock SET UID = %s, STATUS = %s, POLICE_NO = %s, LAST_UPDATE = %s  WHERE ID = %s"
        valBOOKING = [data_dock['uidRfid'].upper(), "BOOKING", data_dock['policeNo'].upper(), str(now), int(dockCode)]
        cursor.execute(updateBOOKING,valBOOKING)
        logger.info(f'[BOOKING]       :   [QUERY] {valBOOKING}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   [QUERY] UPDATE TO DOCK {dockCode} ERROR')
    try:
        updateBookingLog = "INSERT INTO log_server (UID, STATUS, DOCK, POLICE_NO, TIME, DATA) VALUES (%s, %s, %s, %s, %s, %s)"
        valBookingLog = data_dock['uidRfid'].upper(), "BOOKING", int(dockCode), data_dock['policeNo'].upper(), str(now), "IN"
        cursor.execute(updateBookingLog, valBookingLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   [LOG] INSERT TO LOG ERROR')
    ipDisplay = await getIPdisplay(dockCode)
    policeNumber = data_dock['policeNo'].upper()
    URL_BOOK = f'http://{ipDisplay}/booking/{policeNumber}'
    try:
        logger.info(f'[BOOKING]       :   [SEND DISPLAY] SEND GET {URL_BOOK}')
        rBooking = await requests.get(URL_BOOK, timeout = 2)
        logger.info(f'[BOOKING]       :   [SEND DISPLAY] SUCCESCFULLY SEND GET TO DISPLAY')
    except:
        logger.error(f'[BOOKING]      :   [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullBookError = "INSERT INTO send_error (URL, TIME, SEND_STATUS) VALUES (%s, %s, %s)"
        valBookError = URL_BOOK, str(now), "TO DISPLAY"
        cursor.execute(pullBookError, valBookError)
        logger.error(f'[BOOKING]      :   [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay())

    mydb.commit()
    return text('OK')



@gateway.route("/LD/HF/<dockCode>", methods=['GET','POST'])
async def dockHF(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    dataEPC = request.body.decode('utf-8').upper()
    now = datetime.now()
    if dataEPC == "OK":
        return text("OK")
    try:
        updateHFLog = "INSERT INTO log_rfid (UID, DOCK, TIME) VALUES (%s, %s, %s)"
        valHFLog = dataEPC, int(dockCode), str(now)
        cursor.execute(updateHFLog, valHFLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[HF RFID]       :   [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[HF RFID]      :   [LOG] INSERT TO LOG ERROR')
    try:
        GetUidDock = "SELECT UID, POLICE_NO, STATUS FROM loading_dock WHERE ID = %s"
        cursor.execute(GetUidDock, [dockCode, ])
        GetUid = cursor.fetchone()
        UidDb = GetUid[0]
        PoliceNOHF = GetUid[1]
        statusHFLD = GetUid[2]
        logger.info(f'[HF RFID]       :   [QUERY] SELECT UID FROM DOCK {dockCode}')
        logger.info(f'[HF RFID]       :   [QUERY] {UidDb}')
    except:
        UidDb = "OFF"
        PoliceNOHF = "OFF"
        statusHFLD = "OFF"
        logger.error(f'[HF RIFD]      :   [QUERY] UID NOT FOUND IN DOCK {dockCode}')
    if UidDb == dataEPC and statusHFLD == "BOOKING":
        logger.info(f'[HF RFID]       :   [TAP] UID MATCH')
        ipDisplayHF = await getIPdisplay(dockCode)
        policeNumberHF = PoliceNOHF
        URL_HF = f'http://{ipDisplayHF}/start/{policeNumberHF}'
        try:
            logger.info(f'[HF RFID]       :   [SEND DISPLAY] SEND GET {URL_HF}')
            rHF = await requests.get(URL_HF, timeout = 2)
            logger.info(f'[HF RFID]       :   [SEND DISPLAY] SEUCCESFULLY SEND GET TO DISPLAY')
        except:
            logger.error(f'[HF RIFD]      :   [SEND DISPLAY] SEND TO DISPLAY ERROR')
            pullHFERROR = "INSERT INTO send_error (URL, TIME, SEND_STATUS) VALUES (%s, %s, %s)"
            valHFERROR = URL_HF, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            logger.error(f'[HF RIFD]      :   [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay())

        dataHF = {'uidRfid':dataEPC,
                'dockCode':dockCode,
                'time':str(now) }
        ipServerHF = await getIPServer(dockCode)
        URL_SERVERIN = f"http://{ipServerHF}/dock/in"
        try:
            logger.info(f'[HF RFID]       :   [SEND SERVER] {dataHF}')
            rHFServer = await requests.post(URL_SERVERIN, json=dataHF, timeout = 2)
            print(rHFServer.status_code)
            logger.info(f'[HF RFID]       :   [SEND SERVER] SUCCESCFULLY SEND TO {URL_SERVERIN}')            
        except:
            logger.error(f'[HF RIFD]      :   [SEND SERVER] SEND TO SERVER ERROR')
            pullHFERROR = "INSERT INTO send_error (UID, DOCK, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dataEPC, dockCode, URL_SERVERIN, str(now), "TAP START IN"
            cursor.execute(pullHFERROR, valHFERROR)
            logger.error(f'[HF RIFD]      :   [SEND SERVER] SAVE TO DB PULLING')
            app.add_task(trySendHfServer())
    elif UidDb != dataEPC and statusHFLD == "BOOKING":
        #ALARM
        logger.warning(f'[HF RFID]       :   [TAP] NOT MATCH')
        pass


    return text('OK')


@gateway.route("/dock/stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/start/<dockCode>", methods=['GET','POST'])
async def dockStart(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')



@gateway.route("/dock/alarm-stop/<dockCode>", methods=['GET','POST'])
async def dockAlarmStop(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/alarm-start/<num>", methods=['GET','POST'])
async def dockAlarmStart(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

from sanic import Sanic, request, Blueprint
from sanic.response import json, text
from datetime import datetime, date, timedelta
import time
import asyncio
from gateway_dock import cursor, app, mydb, logger
from gateway_dock.config import reconMysql, reconnenctToDbServer, getIPdisplay, getIPServer, statAlarm
from gateway_dock.sendServer import sendErrorDisplay, sendErrorTapIn
from gateway_dock.workStat import Timeshift
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

async def startDurationLoading(dockCode):
    await asyncio.sleep(30)
    timeWork = await Timeshift().timework()
    overTime = await Timeshift().overtime()
    timeNow = datetime.now().time()
    dateTimeNow = datetime.now()
    timeNowTimedelta = timedelta(hours=timeNow.hour, minutes=timeNow.minute, seconds=timeNow.second, microseconds=timeNow.microsecond)
    try:
        getDockCount = "SELECT UID, STATUS, TIME_LAST_COUNT, DURATION, TARGET_DURATION FROM dock_time_count WHERE ID = %s"
        cursor.execute(getDockCount, [dockCode, ])
        GetCount = cursor.fetchone()
        uidCount = GetCount[0]
        statusCount = GetCount[1]
        TimeLastCount = GetCount[2]
        durationCount = GetCount[3]
        TargetDurationCount = int(GetCount[4])
        logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY QUERY DOCK COUNT FROM DOCK {dockCode}')
    except:
        uidCount = "OFF"
        statusCount = "OFF"
        TimeLastCount = timeNow
        durationCount = "OFF"
        TargetDurationCount = "OFF"
        logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [QUERY] ERROR TO GET DATA FORM DOCK COUNT')

    if timeWork[4] == 'WORK_ON' or overTime[2] =='OVERTIME_ON' :
        if TimeLastCount > timeNowTimedelta:
            timeRange =  60
        else:
            timeRange = timeNowTimedelta - TimeLastCount
            timeRange = int(timeRange.total_seconds())
        newDuration = durationCount + timeRange
        try:
            logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [COUNTING] {uidCount} DURATION = {newDuration}')
            updateCount = f"UPDATE dock_time_count SET TIME_LAST_COUNT = %s, DURATION = %s WHERE UID = %s and ID = %s"
            valueCount = [timeNow, newDuration, uidCount, dockCode]
            cursor.execute(updateCount,valueCount)
            mydb.commit()
            logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [COUNTING] SUCCESCFULLY SAVE NEW DURATION DOCK {dockCode}')
        except:
            logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [COUNTING] ERROR TO UPDATE NEW DURATION')

        if newDuration > TargetDurationCount:
            logger.warning(f'[COUNT DOCK]   :   [DOCK {dockCode}] [COUNTING] LOADING HAS EXCEED TARGET')
            logger.warning(f'[COUNT DOCK]   :   [DOCK {dockCode}] [COUNTING] ALARM ON')
            ipDisplay = await getIPdisplay(dockCode)
            statAlarmCount = await statAlarm(dockCode)
            if statAlarmCount == "OFF":
                URL_ALARM_COUNT = f'http://{ipDisplay}'
                dataALARMCOUNT = {'alarm':1}
                try:
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_ALARM_COUNT}')
                    rCOUNT = await requests.post(URL_ALARM_COUNT, json=dataALARMCOUNT, timeout = 2)
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND POST TO DISPLAY')
                except:
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [SEND DISPLAY] SEND TO DISPLAY ERROR')
                    pullCOUNTError = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                    valCOUNTError = dockCode, 'ALARMCOUNT', URL_ALARM_COUNT, str(dateTimeNow), "TO DISPLAY"
                    cursor.execute(pullCOUNTError, valCOUNTError)
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [SEND DISPLAY] SAVE TO DB PULLING')
                    app.add_task(trySendDisplay())
                try:
                    updateStatAlarmCount = "UPDATE dock_alarm SET ALARM = %s, TIME_ALARM = %s, STATUS = %s WHERE ID = %s"
                    valStatAlarmCount = ["OVERTIME", str(dateTimeNow), "ON", int(dockCode)]
                    cursor.execute(updateStatAlarmCount,valStatAlarmCount)
                    mydb.commit()
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE DB DOCK ALARM')
                except:
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [QUERY] ERROR TO UPDATE DB DOCK ALARM')
    else:
        logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [COUNTING] WORK OFF')

    if statusCount == 'START':
        app.add_task(startDurationLoading(dockCode))

@gateway.route("/dock/booking/<dockCode>", methods=['GET','POST'])
async def dockBook(request, dockCode):
    now = datetime.now()
    data_dock = dict(eval(request.body.decode('utf-8')))
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {data_dock}")
    # print(database.is_connected)
    try:
        updateBookingLog = "INSERT INTO log_server (UID, STATUS, DOCK, POLICE_NO, TIME, DATA) VALUES (%s, %s, %s, %s, %s, %s)"
        valBookingLog = data_dock['uidRfid'].upper(), "BOOKING", int(dockCode), data_dock['policeNo'].upper(), str(now), "IN"
        cursor.execute(updateBookingLog, valBookingLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [LOG] INSERT TO LOG ERROR')
    try:
        updateBOOKING = "UPDATE loading_dock SET UID = %s, STATUS = %s, POLICE_NO = %s, LAST_UPDATE = %s  WHERE ID = %s"
        valBOOKING = [data_dock['uidRfid'].upper(), "BOOKING", data_dock['policeNo'].upper(), str(now), int(dockCode)]
        cursor.execute(updateBOOKING,valBOOKING)
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [QUERY] {valBOOKING}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [QUERY] UPDATE TO DOCK {dockCode} ERROR')
    ipDisplay = await getIPdisplay(dockCode)
    policeNumber = data_dock['policeNo'].upper()
    URL_BOOK = f'http://{ipDisplay}'
    dataBook = {'nopol':policeNumber}
    try:
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_BOOK}')
        rBooking = await requests.post(URL_BOOK, json=dataBook, timeout = 2)
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND POST TO DISPLAY')
    except:
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullBookError = "INSERT INTO send_error (DOCK, POLICE_NO, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s, %s)"
        valBookError = dockCode, policeNumber, 'BOOKING', URL_BOOK, str(now), "TO DISPLAY"
        cursor.execute(pullBookError, valBookError)
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay())

    mydb.commit()
    return text('OK')



@gateway.route("/LD/HF/<dockCode>", methods=['GET','POST'])
async def dockHF(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {request.body.decode('utf-8')}")
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
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[HF RFID]      :   [DOCK {dockCode}] [LOG] INSERT TO LOG ERROR')
    try:
        GetUidDock = "SELECT UID, POLICE_NO, STATUS FROM loading_dock WHERE ID = %s"
        cursor.execute(GetUidDock, [dockCode, ])
        GetUid = cursor.fetchone()
        UidDb = GetUid[0]
        PoliceNOHF = GetUid[1]
        statusHFLD = GetUid[2]
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] SELECT UID FROM DOCK {dockCode}')
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] {UidDb}')
    except:
        UidDb = "OFF"
        PoliceNOHF = "OFF"
        statusHFLD = "OFF"
        logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [QUERY] UID NOT FOUND IN DOCK {dockCode}')
    if UidDb == dataEPC and statusHFLD == "BOOKING":
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [TAP] UID MATCH')
        ipDisplayHF = await getIPdisplay(dockCode)
        policeNumberHF = PoliceNOHF
        URL_HF = f'http://{ipDisplayHF}'
        dataStartDisplay = {'State':1}
        try:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_HF}')
            rHF = await requests.post(URL_HF, json=dataStartDisplay, timeout = 2)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [SEND DISPLAY] SEND TO DISPLAY ERROR')
            pullHFERROR = "INSERT INTO send_error (STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s)"
            valHFERROR = 'START', URL_HF, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay())

        dataHF = {'uidRfid':dataEPC,
                'dockCode':dockCode,
                'time':str(now) }
        ipServerHF = await getIPServer(dockCode)
        URL_SERVERIN = f"http://{ipServerHF}/dock/in"
        try:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND SERVER] {dataHF}')
            rHFServer = await requests.post(URL_SERVERIN, json=dataHF, timeout = 2)
            print(rHFServer.status_code)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND SERVER] SUCCESCFULLY SEND TO {URL_SERVERIN}')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [SEND SERVER] SEND TO SERVER ERROR')
            pullHFERROR = "INSERT INTO send_error (UID, DOCK, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dataEPC, dockCode, URL_SERVERIN, str(now), "TAP START IN"
            cursor.execute(pullHFERROR, valHFERROR)
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [SEND SERVER] SAVE TO DB PULLING')
            app.add_task(trySendHfServer())
        try:
            updateDockCount = "UPDATE dock_time_count SET UID = %s WHERE ID = %s"
            valDockCount = [dataEPC, int(dockCode)]
            cursor.execute(updateDockCount,valDockCount)
            mydb.commit()
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK_COUNT')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [QUERY] ERROR TO UPDATE TO DOCK_COUNT')
    elif UidDb != dataEPC and statusHFLD == "BOOKING":
        #ALARM
        logger.warning(f'[HF RFID]       :   [DOCK {dockCode}] [TAP] NOT MATCH')
        pass
    return text('OK')

@gateway.route("/dock/start/<dockCode>", methods=['GET','POST'])
async def dockStart(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {request.body.decode('utf-8')}")
    data_dock = dict(eval(request.body.decode('utf-8')))
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    try:
        updateStartDockLog = "INSERT INTO log_server (STATUS, DOCK, TARGET_TIME, TIME, DATA) VALUES (%s, %s, %s, %s, %s)"
        valStartDockLog = "START", int(dockCode), int(data_dock['targetTime']), str(now), "IN"
        cursor.execute(updateStartDockLog, valStartDockLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[START DOCK]    :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[START DOCK]   :   [DOCK {dockCode}] [LOG] INSERT TO LOG ERROR')
    try:
        updateStartDock = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE ID = %s"
        valStartDock = ["START", str(now), int(dockCode)]
        cursor.execute(updateStartDock,valStartDock)
        mydb.commit()
        updateStartDockCount = "UPDATE dock_time_count SET STATUS = %s, TIME_IN = %s, TIME_LAST_COUNT = %s, DURATION = %s, TARGET_DURATION = %s  WHERE ID = %s"
        valStartDockCount = ["START", str(now), str(time_), 0, data_dock['targetTime'], int(dockCode) ]
        cursor.execute(updateStartDockCount,valStartDockCount)
        mydb.commit()
        updateStatAlarm = "UPDATE dock_alarm SET STATUS = %s WHERE ID = %s"
        valStatAlarm = ["OFF", int(dockCode)]
        cursor.execute(updateStatAlarm,valStatAlarm)
        mydb.commit()
        logger.info(f'[START DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
        app.add_task(startDurationLoading(dockCode))
    except:
        logger.error(f'[START DOCK]   :   [DOCK {dockCode}] [QUERY] UPDATE TO DOCK {dockCode} ERROR')

    return text('OK')

@gateway.route("/dock/stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] /dock/stop/<dockCode>")
    # print(database.is_connected)
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    try:
        getStopCount = "SELECT DURATION FROM dock_time_count WHERE ID = %s"
        cursor.execute(getStopCount, [dockCode, ])
        GetStopCount = cursor.fetchone()
        durationStopCount = GetStopCount[0]
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT DURATION')
    except:
        durationStopCount = "notfound"
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [QUERY] SELECT DURATION ERROR')
    try:
        updateStopDock = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE ID = %s"
        valStopDock = ["STOP", str(now), int(dockCode)]
        cursor.execute(updateStopDock,valStopDock)
        mydb.commit()
        updateStopDockCount = "UPDATE dock_time_count SET STATUS = %s WHERE ID = %s"
        valStopDockCount = ["STOP", int(dockCode) ]
        cursor.execute(updateStopDockCount,valStopDockCount)
        mydb.commit()
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [QUERY] UPDATE ERROR')
    ipStop = await getIPdisplay(dockCode)
    URL_STOP = f'http://{ipStop}'
    dataStop = {'alarm':0}
    try:
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_STOP}')
        rStop = await requests.post(URL_STOP, json=dataStop, timeout = 2)
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        #AWAIT STAT ALARM
    except:
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullHFERROR = "INSERT INTO send_error (STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s)"
        valHFERROR = 'ALARMOFF', URL_STOP, str(now), "TO DISPLAY"
        cursor.execute(pullHFERROR, valHFERROR)
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay())
    try:
        updatedockAlarm = "UPDATE dock_alarm SET ALARM = %s, TIME_ALARM = %s, STATUS = %s WHERE ID = %s"
        valdockAlarm = [None, None, None, int(dockCode)]
        cursor.execute(updatedockAlarm,valdockAlarm)
        mydb.commit()
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [QUERY] UPDATE ERROR')



    return response.json({'totalTime': durationStopCount})




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

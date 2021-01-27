from sanic import Sanic, request, Blueprint
from sanic.response import json, text
from datetime import datetime, date, timedelta
import time
import asyncio
import json
from gateway_dock import cursor, app, mydb, logger
from gateway_dock.config import reconMysql, reconnenctToDbServer, getIPdisplay, getIPServer, statAlarm
from gateway_dock.sendServer import sendErrorDisplay, sendErrorTapIn
from gateway_dock.workStat import Timeshift
from gateway_dock.sendEmail  import sendEmailLog
from sanic_cors import CORS, cross_origin
import requests_async as requests
gateway = Blueprint('gateway', url_prefix='')


async def trySendDisplay(dockNum = None, dockStat = None):
    await asyncio.sleep(30)
    trySend = await sendErrorDisplay(dockNum,dockStat)
    if not trySend:
        app.add_task(trySendDisplay(dockNum, dockStat))

async def trySendHfServer(dockNum = None, dockStat = None):
    await asyncio.sleep(30)
    trySendHF = await sendErrorTapIn(dockNum, dockStat)
    if not trySendHF:
        app.add_task(trySendHfServer(dockNum, dockStat))

# app.add_task(reconnenctToDbServer())
async def reqTimeWork():
    await asyncio.sleep(10)
    try:
        ipServerTime = await getIPServer()
        URL_SERVER_TIME = f"http://{ipServerHF}/workTime"
        rTime = await requests.get(URL_SERVER_TIME, timeout = 5)
    except:
        pass

async def cekCountLoad():
    for x in range(1,25):
        if x < 25:
            if len(str(x)) == 1:
                dockName = f"A0{x}"
            else:
                dockName = f"A{x}"
        app.add_task(startDurationLoading(dockName))

async def bookingSend(dockCode, nopol):
    for i in range(1,11):
        await asyncio.sleep(10)
        ipDisplay = await getIPdisplay(dockCode)
        policeNumber = nopol
        URL_BOOK = f'http://{ipDisplay}'
        dataBook = {"nopol":f"{policeNumber}"}
        try:
            logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST PER : {i}')
            logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_BOOK}')
            rBooking = await requests.post(URL_BOOK, json=dataBook, timeout = 5)
            logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND {dataBook} TO DISPLAY')
        except:
            logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')



async def tapInSend(dockCode):
    for k in range(1,11):
        await asyncio.sleep(10)
        ipDisplayHF = await getIPdisplay(dockCode)
        URL_HF = f'http://{ipDisplayHF}'
        dataStartDisplay = {"state":"1"}
        try:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST PER : {k}')
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_HF}')
            rHF = await requests.post(URL_HF, json=dataStartDisplay, timeout = 5)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] {dataStartDisplay}')
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')

async def tapOutSend(dockCode):
    for o in range(1,11):
        await asyncio.sleep(10)
        ipStateStop = await getIPdisplay(dockCode)
        URL_StateStop = f'http://{ipStateStop}'
        dataStateStop = {"state":"0"}
        try:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST PER : {o}')
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_StateStop}')
            rHF = await requests.post(URL_StateStop, json=dataStateStop, timeout = 5)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] {dataStateStop}')
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')


app.add_task(cekCountLoad())
app.add_task(reconMysql())
app.add_task(reqTimeWork())

async def startDurationLoading(dockCode):
    #BELUM KIRIM DATA KE SERVER KALO ALARM
    await asyncio.sleep(60)
    timeWork = await Timeshift().timework()
    # overTime = await Timeshift().overtime()
    timeNow = datetime.now().time()
    dateTimeNow = datetime.now()
    timeNowTimedelta = timedelta(hours=timeNow.hour, minutes=timeNow.minute, seconds=timeNow.second, microseconds=timeNow.microsecond)
    try:
        getDockCount = "SELECT UID, STATUS, TIME_LAST_COUNT, DURATION, TARGET_DURATION FROM dock_time_count WHERE DOCK = %s"
        cursor.execute(getDockCount, [dockCode, ])
        GetCount = cursor.fetchone()
        uidCount = GetCount[0]
        statusCount = GetCount[1]
        TimeLastCount = GetCount[2]
        durationCount = GetCount[3]
        TargetDurationCount = int(GetCount[4])
        logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY QUERY DOCK COUNT FROM DOCK {dockCode}')
        logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [QUERY] DOCK COUNT STATUS {statusCount}')
    except:
        uidCount = "OFF"
        statusCount = "OFF"
        TimeLastCount = timeNow
        durationCount = "OFF"
        TargetDurationCount = "OFF"
        logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR TO GET DATA FORM DOCK COUNT')

    if timeWork[4] == 'WORK_ON' and statusCount == 'START':
        if TimeLastCount > timeNowTimedelta:
            timeRange =  60
        else:
            timeRange = timeNowTimedelta - TimeLastCount
            timeRange = int(timeRange.total_seconds())
        newDuration = durationCount + timeRange
        try:
            logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [COUNTING] {uidCount} DURATION = {newDuration}')
            updateCount = f"UPDATE dock_time_count SET TIME_LAST_COUNT = %s, DURATION = %s WHERE UID = %s and DOCK = %s"
            valueCount = [timeNow, newDuration, uidCount, dockCode]
            cursor.execute(updateCount,valueCount)
            mydb.commit()
            logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [COUNTING] SUCCESCFULLY SAVE NEW DURATION DOCK {dockCode}')
        except:
            logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [ERROR] [COUNTING] ERROR TO UPDATE NEW DURATION')

        if newDuration > TargetDurationCount:
            logger.warning(f'[COUNT DOCK] :   [DOCK {dockCode}] [WARNING] [COUNTING] LOADING HAS EXCEED TARGET')
            logger.warning(f'[COUNT DOCK] :   [DOCK {dockCode}] [WARNING] [COUNTING] ALARM ON')
            ipDisplay = await getIPdisplay(dockCode)
            statAlarmCount = await statAlarm(dockCode)
            if statAlarmCount == "OFF":
                URL_ALARM_COUNT = f'http://{ipDisplay}'
                dataALARMCOUNT = {'alarm':"1"}
                try:
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [SEND DISPLAY] [ALARM] SEND {dataALARMCOUNT} {URL_ALARM_COUNT}')
                    rCOUNT = await requests.post(URL_ALARM_COUNT, json=dataALARMCOUNT, timeout = 5)
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [SEND DISPLAY] [ALARM] SUCCESCFULLY SEND POST TO DISPLAY')
                except:
                    delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
                    cursor.execute(delpul, [dockCode, "TO DISPLAY"])
                    mydb.commit()
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] [ALARM] SEND TO DISPLAY ERROR')
                    pullCOUNTError = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                    valCOUNTError = dockCode, 'ALARMCOUNT', URL_ALARM_COUNT, str(dateTimeNow), "TO DISPLAY"
                    cursor.execute(pullCOUNTError, valCOUNTError)
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] [ALARM] SAVE TO DB PULLING')
                    app.add_task(trySendDisplay(dockCode, 'ALARMCOUNT'))
                try:
                    updateAlarmLog = "INSERT INTO log_alarm (UID, DOCK, STATUS, NOTE, TIME) VALUES (%s, %s, %s, %s, %s)"
                    valAlarmLog = uidCount, dockCode, 'ALARM ON', "OVERTIME",str(dateTimeNow)
                    cursor.execute(updateAlarmLog, valAlarmLog)
                    # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
                    mydb.commit()
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG ALARM')
                except:
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')

                try:
                    updateStatAlarmCount = "UPDATE dock_alarm SET ALARM = %s, TIME_ALARM = %s, STATUS = %s WHERE DOCK = %s"
                    valStatAlarmCount = ["OVERTIME", str(dateTimeNow), "ON", dockCode]
                    cursor.execute(updateStatAlarmCount,valStatAlarmCount)
                    mydb.commit()
                    logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE DB DOCK ALARM')
                except:
                    logger.error(f'[COUNT DOCK]   :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR TO UPDATE DB DOCK ALARM')

    if timeWork[4] == 'WORK_OFF' and statusCount == 'START':
        updateCount = f"UPDATE dock_time_count SET TIME_LAST_COUNT = %s WHERE UID = %s and DOCK = %s"
        valueCount = [timeNow, uidCount, dockCode]
        cursor.execute(updateCount,valueCount)
        mydb.commit()
        logger.info(f'[COUNT DOCK]    :   [DOCK {dockCode}] [COUNTING] WORK OFF')

    if statusCount == 'START':
        mydb.commit()
        app.add_task(startDurationLoading(dockCode))
    else:
        ipStopp = await getIPdisplay(dockCode)
        URL_STOPp = f'http://{ipStopp}'
        dataStopp = {"alarm":"0"}
        try:
            rStop1 = await requests.post(URL_STOPp, json=dataStopp, timeout = 5)
        except:
            pass

@gateway.route("/dock/booking/<dockCode>", methods=['GET','POST'])
async def dockBook(request, dockCode):
    now = datetime.now()
    data_dock = json.loads(request.body.decode('utf-8'))
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {data_dock}")
    # print(database.is_connected)
    try:
        updateBookingLog = "INSERT INTO log_server (UID, STATUS, DOCK, POLICE_NO, TIME, DATA) VALUES (%s, %s, %s, %s, %s, %s)"
        valBookingLog = data_dock['uid'].upper(), "BOOKING", dockCode, data_dock['policeNo'].upper(), str(now), "IN"
        cursor.execute(updateBookingLog, valBookingLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    try:
        updateBOOKING = "UPDATE loading_dock SET UID = %s, STATUS = %s, POLICE_NO = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
        valBOOKING = [data_dock['uid'].upper(), "BOOKING", data_dock['policeNo'].upper(), str(now), dockCode]
        cursor.execute(updateBOOKING,valBOOKING)
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [QUERY] {valBOOKING}')
        mydb.commit()
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE TO DOCK {dockCode} ERROR')
    ipDisplay = await getIPdisplay(dockCode)
    policeNumber = data_dock['policeNo'].upper()
    URL_BOOK = f'http://{ipDisplay}'
    dataBook = {"nopol":f"{policeNumber}"}
    try:
        app.add_task(bookingSend(dockCode,policeNumber))
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_BOOK}')
        rBooking = await requests.post(URL_BOOK, json=dataBook, timeout = 5)
        logger.info(f'[BOOKING]       :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND {dataBook} TO DISPLAY')
    except:
        delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
        cursor.execute(delpul, [dockCode, "TO DISPLAY"])
        mydb.commit()
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullBookError = "INSERT INTO send_error (DOCK, POLICE_NO, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s, %s)"
        valBookError = dockCode, policeNumber, 'BOOKING', URL_BOOK, str(now), "TO DISPLAY"
        cursor.execute(pullBookError, valBookError)
        logger.error(f'[BOOKING]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay(dockCode, 'BOOKING'))

        # app.add_task(sendEmailLog(f'ERROR SEND TO DISPLAY {dockCode}', 'BOOKING'))

    mydb.commit()
    return text('OK')



@gateway.route("/LD/HF/<dockCode>", methods=['GET','POST'])
async def dockHF(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {request.body.decode('utf-8')}")
    dataEPC = request.body.decode('utf-8').upper()
    now = datetime.now()
    if dataEPC == "OK":
        return text("OK")
    elif dataEPC == "1":
        try:
            getReqActive = "SELECT UID, POLICE_NO, STATUS, TYPE FROM loading_dock WHERE DOCK = %s"
            cursor.execute(getReqActive, [dockCode, ])
            GetActive = cursor.fetchone()
            GetActiveStat = GetActive[3]
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] STATUS DOCK {GetActiveStat}')
        except:
            GetActiveStat = "notfound"
        if GetActiveStat == 'DISABLE':
            dataActive = {"active":"0"}
            ipDisplay = await getIPdisplay(dockCode)
            URL_BOOK = f'http://{ipDisplay}'
            try:
                logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_BOOK} {dataActive} TO DISPLAY')
                rBooking = await requests.post(URL_BOOK, json=dataActive, timeout = 5)
            except:
                pass
        mydb.commit()
        return text("OK")
    try:
        updateHFLog = "INSERT INTO log_rfid (UID, DOCK, TIME) VALUES (%s, %s, %s)"
        valHFLog = dataEPC, dockCode, str(now)
        cursor.execute(updateHFLog, valHFLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[HF RFID]      :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    try:
        GetUidDock = "SELECT UID, POLICE_NO, STATUS, LAST_UPDATE FROM loading_dock WHERE DOCK = %s"
        cursor.execute(GetUidDock, [dockCode, ])
        GetUid = cursor.fetchone()
        UidDb = GetUid[0]
        PoliceNOHF = GetUid[1]
        statusHFLD = GetUid[2]
        LastTime = GetUid[3]
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] SELECT UID FROM DOCK {dockCode}')
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] {UidDb}')
    except:
        UidDb = "OFF"
        PoliceNOHF = "OFF"
        statusHFLD = "OFF"
        logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [QUERY] UID NOT FOUND IN DOCK {dockCode}')
    try:
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] CHECK DOUBLE DOCK')
        GetUidDock2 = "SELECT DOCK, UID, POLICE_NO, STATUS FROM loading_dock WHERE UID = %s AND DOCK != %s"
        cursor.execute(GetUidDock2, [dataEPC, dockCode])
        GetUid2 = cursor.fetchone()
        dockCode2 = GetUid2[0]
        UidDb2 = GetUid2[1]
        PoliceNOHF2 = GetUid2[2]
        statusHFLD2 = GetUid2[3]
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] {UidDb2}')
    except:
        dockCode2 = None
        UidDb2 = "OFF"
        PoliceNOHF2 = "OFF"
        statusHFLD2 = "OFF"
        logger.info(f'[HF RIFD]       :   [DOCK {dockCode}] [QUERY] NO DOUBLE DOCK')

    if UidDb == dataEPC and statusHFLD == "BOOKING":
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [TAP] UID MATCH')
        ipDisplayHF = await getIPdisplay(dockCode)
        policeNumberHF = PoliceNOHF
        URL_HF = f'http://{ipDisplayHF}'
        dataStartDisplay = {"state":"1"}
        dataBookPolice1 = {"nopol":f"{policeNumberHF}"}
        try:
            app.add_task(tapInSend(dockCode))
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_HF}')
            rHF = await requests.post(URL_HF, json=dataStartDisplay, timeout = 5)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] {dataStartDisplay}')
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
            pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dockCode, 'START', URL_HF, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay(dockCode, 'START'))

        dataHF = {'uid':dataEPC,
                'dockCode':dockCode,
                'time':str(now) }
        ipServerHF = await getIPServer(dockCode)
        URL_SERVERIN = f"http://{ipServerHF}/dock/in"
        try:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND SERVER] {dataHF}')
            rHFServer = await requests.post(URL_SERVERIN, json=dataHF, timeout = 5)
            print(rHFServer.status_code)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND SERVER] SUCCESCFULLY SEND TO {URL_SERVERIN}')
        except:
            delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
            cursor.execute(delpul, [dockCode, "TAP START IN"])
            mydb.commit()
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SEND TO SERVER ERROR')
            pullHFERROR = "INSERT INTO send_error (UID, DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s, %s)"
            valHFERROR = dataEPC, dockCode, 'TAP', URL_SERVERIN, str(now), "TAP START IN"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SAVE TO DB PULLING')
            app.add_task(trySendHfServer(dockCode, 'TAP'))
        try:
            updateDockCount = "UPDATE dock_time_count SET UID = %s, STATUS = %s WHERE DOCK = %s"
            valDockCount = [dataEPC, 'TAP', dockCode]
            cursor.execute(updateDockCount,valDockCount)
            mydb.commit()
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK_COUNT')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR TO UPDATE TO DOCK_COUNT')
        try:
            updateDockHF = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valDockHF = ["TAP", str(now), dockCode]
            cursor.execute(updateDockHF,valDockHF)
            mydb.commit()
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE STATUS {dockCode}')
        except:
            logger.error(f'[HF RFID]      :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE STATUS TO DOCK {dockCode} ERROR')
        if UidDb == UidDb2 and PoliceNOHF == PoliceNOHF2:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] DOUBLE DOCK DETECT')
            ipDisplayHF2 = await getIPdisplay(dockCode2)
            policeNumberHF2 = PoliceNOHF2
            URL_HF2 = f'http://{ipDisplayHF2}'
            dataStartDisplay2 = {"state":"1"}
            dataBookPolice = {"nopol":f"{policeNumberHF2}"}
            try:
                app.add_task(tapInSend(dockCode2))
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [SEND DISPLAY] SEND POST {URL_HF2}')
                rHF = await requests.post(URL_HF2, json=dataStartDisplay2, timeout = 5)
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [SEND DISPLAY] {dataStartDisplay2}')
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
            except:
                logger.error(f'[HF RIFD]      :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
                pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                valHFERROR = dockCode2, 'START', URL_HF, str(now), "TO DISPLAY"
                cursor.execute(pullHFERROR, valHFERROR)
                mydb.commit()
                logger.error(f'[HF RIFD]      :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
                app.add_task(trySendDisplay(dockCode2, 'START'))
            try:
                updateDockCount2 = "UPDATE dock_time_count SET UID = %s, STATUS = %s WHERE DOCK = %s"
                valDockCount2 = [UidDb2, 'TAP', dockCode2]
                cursor.execute(updateDockCount2,valDockCount2)
                mydb.commit()
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE TO DOCK_COUNT')
            except:
                logger.error(f'[HF RIFD]      :   [DOCK {dockCode2}] [ERROR] [QUERY] ERROR TO UPDATE TO DOCK_COUNT')
            try:
                updateDockHF2 = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
                valDockHF2 = ["TAP", str(now), dockCode2]
                cursor.execute(updateDockHF2,valDockHF2)
                mydb.commit()
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE STATUS {dockCode2}')
            except:
                logger.error(f'[HF RFID]      :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE STATUS TO DOCK {dockCode2} ERROR')


    elif UidDb == dataEPC and statusHFLD == "STOP":
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [TAP] UID MATCH')
        timeTerpal = int((now-LastTime).total_seconds())
        dataHF = {"uid":dataEPC,
                    "timeTerpal":timeTerpal,
                    "dockCode":dockCode}
                    #"dockSekunder":dockCode2}
        logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [TIME] TERPAL TIME {timeTerpal}')
        ipServerHF = await getIPServer(dockCode)
        URL_SERVEROUT = f"http://{ipServerHF}/dock/out"
        try:
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND SERVER] {dataHF}')
            rHFServer = await requests.post(URL_SERVEROUT, json=dataHF, timeout = 5)
            print(rHFServer.status_code)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND SERVER] SUCCESCFULLY SEND TO {URL_SERVEROUT}')
        except:
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SEND TO SERVER ERROR')
            pullHFERROR = "INSERT INTO send_error (UID, DOCK, STATUS, URL, TOTALTIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s, %s)"
            valHFERROR = dataEPC, dockCode, 'TERPAL', URL_SERVEROUT, timeTerpal, "TAP START IN"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[HF RIFD]      :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SAVE TO DB PULLING')
            app.add_task(trySendHfServer(dockCode, 'TERPAL'))
        try:
            updateTerpalDock = "UPDATE loading_dock SET UID = %s, POLICE_NO = %s, STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valTerpalDock = [None, None, "STOP", str(now), dockCode]
            cursor.execute(updateTerpalDock,valTerpalDock)
            mydb.commit()
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE LOADING DOCK STATUS {dockCode}')
        except:
            logger.error(f'[HF RFID]      :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE TO LOADING DOCK ERROR')
        ipStateStop = await getIPdisplay(dockCode)
        URL_StateStop = f'http://{ipStateStop}'
        dataStateStop = {"state":"0"}
        try:
            app.add_task(tapOutSend(dockCode))
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_StateStop}')
            rHF = await requests.post(URL_StateStop, json=dataStateStop, timeout = 5)
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] {dataStateStop}')
            logger.info(f'[HF RFID]       :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
            cursor.execute(delpul, [dockCode, "TO DISPLAY"])
            mydb.commit()
            logger.error(f'[HF RFID]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
            pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dockCode, 'STOP', URL_StateStop, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[HF RFID]      :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay(dockCode, 'STOP'))
        ipStopp = await getIPdisplay(dockCode)
        URL_STOPp = f'http://{ipStopp}'
        dataStopp = {"alarm":"0"}
        try:
            rStop1 = await requests.post(URL_STOPp, json=dataStopp, timeout = 5)
        except:
            pass
        if UidDb == UidDb2 and PoliceNOHF == PoliceNOHF2:

            try:
                updateTerpalDock = "UPDATE loading_dock SET UID = %s, POLICE_NO = %s, STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
                valTerpalDock = [None, None, "STOP", str(now), dockCode2]
                cursor.execute(updateTerpalDock,valTerpalDock)
                mydb.commit()
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE LOADING DOCK STATUS {dockCode}')
            except:
                logger.error(f'[HF RFID]      :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE TO LOADING DOCK ERROR')
            ipStopp2 = await getIPdisplay(dockCode2)
            URL_STOPp2 = f'http://{ipStopp2}'
            dataStopp2 = {"alarm":"0"}
            try:
                rStop2 = await requests.post(URL_STOPp2, json=dataStopp2, timeout = 5)
            except:
                pass
            ipStateStop2 = await getIPdisplay(dockCode2)
            URL_StateStop2 = f'http://{ipStateStop2}'
            dataStateStop2 = {"state":"0"}
            try:
                app.add_task(tapOutSend(dockCode2))
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [SEND DISPLAY] SEND POST {URL_StateStop2}')
                rHF = await requests.post(URL_StateStop2, json=dataStateStop2, timeout = 5)
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [SEND DISPLAY] {dataStateStop2}')
                logger.info(f'[HF RFID]       :   [DOCK {dockCode2}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
            except:
                delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
                cursor.execute(delpul, [dockCode2, "TO DISPLAY"])
                mydb.commit()
                logger.error(f'[HF RFID]      :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
                pullHFERROR2 = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                valHFERROR2 = dockCode2, 'STOP', URL_StateStop2, str(now), "TO DISPLAY"
                cursor.execute(pullHFERROR2, valHFERROR2)
                mydb.commit()
                logger.error(f'[HF RFID]      :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
                app.add_task(trySendDisplay(dockCode2, "STOP"))

    elif UidDb != dataEPC and statusHFLD == "BOOKING":
        #ALARM
        logger.warning(f'[HF RFID]       :   [DOCK {dockCode}] [TAP] NOT MATCH')

    mydb.commit()
    return text('OK')


@gateway.route("/dock/start/<dockCode>", methods=['GET','POST'])
async def dockStart(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {request.body.decode('utf-8')}")
    data_dock = json.loads(request.body.decode('utf-8'))
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    try:
        getuidCount = "SELECT UID, POLICE_NO, STATUS, LAST_UPDATE FROM loading_dock WHERE DOCK = %s"
        cursor.execute(getuidCount, [dockCode, ])
        GetuidCount = cursor.fetchone()
        uidgetCount = GetuidCount[0]
        policegetCount = GetuidCount[1]
        statusStartDock = GetuidCount[2]
        lastUpdateStartCount = GetuidCount[3]
        logger.info(f'[START DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT UID')
    except:
        uidgetCount = "notfound"
        policegetCount = "notfound"
        statusDockCount = "notfound"
        lastUpdateStartCount = now
        logger.error(f'[START DOCK]   :   [DOCK {dockCode}] [QUERY] [ERROR] SELECT DURATION ERROR')
    try:
        logger.info(f'[START DOCK]    :   [DOCK {dockCode}] CHECK DOUBLE DOCK')
        getuidCount2 = "SELECT DOCK, UID, POLICE_NO, STATUS FROM loading_dock WHERE UID = %s AND POLICE_NO = %s AND DOCK != %s"
        cursor.execute(getuidCount2, [uidgetCount, policegetCount, dockCode])
        GetuidCount2 = cursor.fetchone()
        dockCode2 = GetuidCount2[0]
        uidgetCount2 = GetuidCount2[1]
        policegetCount2 = GetuidCount2[2]
        statusStartDock2 = GetuidCount2[3]
    except:
        dockCode2 = "notfound"
        uidgetCount2 = "notfound"
        policegetCount2 = "notfound"
        statusDockCount2 = "notfound"
        logger.info(f'[START DOCK]    :   [DOCK {dockCode}] NO DOUBLE DOCK')
    try:
        updateStartDockLog = "INSERT INTO log_server (UID, STATUS, DOCK, POLICE_NO, TARGET_TIME, TIME, DATA) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        valStartDockLog = uidgetCount, "START", dockCode, policegetCount, int(data_dock['targetTime']), str(now), "START COUNT"
        cursor.execute(updateStartDockLog, valStartDockLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[START DOCK]    :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[START DOCK]   :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    if statusStartDock == "TAP":
        try:
            updateStartDock = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valStartDock = ["START", str(now), dockCode]
            cursor.execute(updateStartDock,valStartDock)
            mydb.commit()
            updateStartDockCount = "UPDATE dock_time_count SET STATUS = %s, TIME_IN = %s, TIME_LAST_COUNT = %s, DURATION = %s, TARGET_DURATION = %s  WHERE DOCK = %s"
            valStartDockCount = ["START", str(now), str(time_), 0, data_dock['targetTime'], dockCode ]
            cursor.execute(updateStartDockCount,valStartDockCount)
            mydb.commit()
            updateStatAlarm = "UPDATE dock_alarm SET STATUS = %s WHERE DOCK = %s"
            valStatAlarm = ["OFF", dockCode]
            cursor.execute(updateStatAlarm,valStatAlarm)
            mydb.commit()
            logger.info(f'[START DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
            app.add_task(startDurationLoading(dockCode))
        except:
            logger.error(f'[START DOCK]   :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE TO DOCK {dockCode} ERROR')
        if uidgetCount == uidgetCount2 and policegetCount == policegetCount2:
            logger.info(f'[START DOCK]    :   [DOCK {dockCode2}] DOUBLE DOCK DETECT')
            try:
                updateStartDock2 = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
                valStartDock2 = ["START", str(now), dockCode2]
                cursor.execute(updateStartDock2,valStartDock2)
                mydb.commit()
                updateStartDockCount2 = "UPDATE dock_time_count SET STATUS = %s, TIME_IN = %s, TIME_LAST_COUNT = %s, DURATION = %s, TARGET_DURATION = %s  WHERE DOCK = %s"
                valStartDockCount2 = ["START", str(now), str(time_), 0, data_dock['targetTime'], dockCode2 ]
                cursor.execute(updateStartDockCount2,valStartDockCount2)
                mydb.commit()
                updateStatAlarm2 = "UPDATE dock_alarm SET STATUS = %s WHERE DOCK = %s"
                valStatAlarm2 = ["OFF", dockCode2]
                cursor.execute(updateStatAlarm2,valStatAlarm2)
                mydb.commit()
                logger.info(f'[START DOCK]    :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode2}')
                app.add_task(startDurationLoading(dockCode2))
            except:
                logger.error(f'[START DOCK]   :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE TO DOCK {dockCode2} ERROR')
    elif statusStartDock == "STOP":
        try:
            updateStartDock = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valStartDock = ["START", str(now), dockCode]
            cursor.execute(updateStartDock,valStartDock)
            mydb.commit()
            updateStartDockCount = "UPDATE dock_time_count SET STATUS = %s, TIME_IN = %s, TIME_LAST_COUNT = %s, TARGET_DURATION = %s  WHERE DOCK = %s"
            valStartDockCount = ["START", str(now), str(time_), data_dock['targetTime'], dockCode ]
            cursor.execute(updateStartDockCount,valStartDockCount)
            mydb.commit()
            updateStatAlarm = "UPDATE dock_alarm SET STATUS = %s WHERE DOCK = %s"
            valStatAlarm = ["OFF", dockCode]
            cursor.execute(updateStatAlarm,valStatAlarm)
            mydb.commit()
            logger.info(f'[START DOCK]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
            app.add_task(startDurationLoading(dockCode))
        except:
            logger.error(f'[START DOCK]   :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE TO DOCK {dockCode} ERROR')
    mydb.commit()
    timePrepare = int((now-lastUpdateStartCount).total_seconds())
    y = json.dumps({'timePrepare': timePrepare})
    return text(y)


@gateway.route("/dock/stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] /dock/stop/{dockCode}")
    # print(database.is_connected)
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    try:
        getStopCount = "SELECT UID, DURATION, TARGET_DURATION FROM dock_time_count WHERE DOCK = %s"
        cursor.execute(getStopCount, [dockCode, ])
        GetStopCount = cursor.fetchone()
        uidStopCount = GetStopCount[0]
        durationStopCount = GetStopCount[1]
        TargetStopCount = GetStopCount[2]
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT DURATION')
    except:
        durationStopCount = "notfound"
        uidStopCount = "notfound"
        TargetStopCount = "notfound"
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [QUERY] SELECT DURATION ERROR')
    try:
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] CHECK DOUBLE DOCK')
        getStopCount2 = "SELECT DOCK, UID FROM loading_dock WHERE UID = %s AND DOCK != %s"
        cursor.execute(getStopCount2, [uidStopCount, dockCode ])
        GetStopCount2 = cursor.fetchone()
        dockCode2 = GetStopCount2[0]
        uidStopCount2 = GetStopCount2[1]
    except:
        dockCode2 = "notfound"
        uidStopCount2 = "notfound"
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] NO DOUBLE DECK')
    try:
        updateStopDockLog = "INSERT INTO log_server (UID, STATUS, DOCK, TARGET_TIME, TOTAL_TIME, TIME, DATA) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        valStopDockLog = uidStopCount, "STOP", dockCode, TargetStopCount, durationStopCount, str(now), "OUT/STOP"
        cursor.execute(updateStopDockLog, valStopDockLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    try:
        updateStopDock = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
        valStopDock = ["STOP", str(now), dockCode]
        cursor.execute(updateStopDock,valStopDock)
        mydb.commit()
        updateStopDockCount = "UPDATE dock_time_count SET STATUS = %s WHERE DOCK = %s"
        valStopDockCount = ["STOP", dockCode ]
        cursor.execute(updateStopDockCount,valStopDockCount)
        mydb.commit()
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE ERROR')
    try:
        #GET STAT ALARM IF ALARM STATUS ON
        sqlGetAlarmDock = "SELECT STATUS FROM dock_alarm WHERE DOCK = %s"
        cursor.execute(sqlGetAlarmDock, [dockCode,])
        dataStat = cursor.fetchone()
        statAlarmDock = dataStat[0]
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT STAT ALARM')
    except:
        statAlarmDock  = "notfound"
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [QUERY] SELECT STAT ALARM ERROR')
    if statAlarmDock == 'ON':
        ipStop = await getIPdisplay(dockCode)
        URL_STOP = f'http://{ipStop}'
        dataStop = {"alarm":"0"}
        try:
            logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [ALARM] [SEND DISPLAY] SEND {dataStop} {URL_STOP}')
            rStop = await requests.post(URL_STOP, json=dataStop, timeout = 5)
            logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [ALARM] [SEND DISPLAY] SEUCCESFULLY SEND ALARM')
            #AWAIT STAT ALARM
        except:
            delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
            cursor.execute(delpul, [dockCode, "TO DISPLAY"])
            mydb.commit()
            logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [ALARM] [SEND DISPLAY] ERROR')
            pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dockCode, 'ALARMOFF', URL_STOP, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [ALARM] [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay(dockCode, 'ALARMOFF'))
        try:
            updateAlarmENDLog = "INSERT INTO log_alarm (UID, DOCK, STATUS, NOTE, TIME) VALUES (%s, %s, %s, %s, %s)"
            valAlarmENDLog = uidStopCount, dockCode, 'ALARM OFF', "DOCK STOP", str(now)
            cursor.execute(updateAlarmENDLog, valAlarmENDLog)
            # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
            mydb.commit()
            logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG ALARM')
        except:
            logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    try:
        updatedockAlarm = "UPDATE dock_alarm SET ALARM = %s, TIME_ALARM = %s, STATUS = %s WHERE DOCK = %s"
        valdockAlarm = [None, None, None, dockCode]
        cursor.execute(updatedockAlarm,valdockAlarm)
        mydb.commit()
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode}')
    except:
        logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE ERROR')

    # ipStateStop = await getIPdisplay(dockCode)
    # URL_StateStop = f'http://{ipStateStop}'
    # dataStateStop = {"state":"0"}
    # try:
    #     logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_StateStop}')
    #     rHF = await requests.post(URL_StateStop, json=dataStateStop, timeout = 5)
    #     logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [SEND DISPLAY] {dataStateStop}')
    #     logger.info(f'[STOP DOCK]     :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
    # except:
    #     delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
    #     cursor.execute(delpul, [dockCode, "TO DISPLAY"])
    #     mydb.commit()
    #     logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
    #     pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
    #     valHFERROR = dockCode, 'STOP', URL_StateStop, str(now), "TO DISPLAY"
    #     cursor.execute(pullHFERROR, valHFERROR)
    #     mydb.commit()
    #     logger.error(f'[STOP DOCK]    :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
    #     app.add_task(trySendDisplay(dockCode, 'STOP'))

    if uidStopCount == uidStopCount2:
        logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] DOUBLE DECK DETECT')
        try:
            updateStopDock2 = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valStopDock2 = ["STOP", str(now), dockCode2]
            cursor.execute(updateStopDock2,valStopDock2)
            mydb.commit()
            updateStopDockCount2 = "UPDATE dock_time_count SET STATUS = %s WHERE DOCK = %s"
            valStopDockCount2 = ["STOP", dockCode2 ]
            cursor.execute(updateStopDockCount2,valStopDockCount2)
            mydb.commit()
            logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode2}')
        except:
            logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE ERROR')
        try:
            #GET STAT ALARM IF ALARM STATUS ON
            sqlGetAlarmDock2 = "SELECT STATUS FROM dock_alarm WHERE DOCK = %s"
            cursor.execute(sqlGetAlarmDock2, [dockCode2,])
            dataStat2 = cursor.fetchone()
            statAlarmDock2 = dataStat2[0]
            logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY SELECT STAT ALARM')
        except:
            statAlarmDock2  = "notfound"
            logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [QUERY] SELECT STAT ALARM ERROR')
        if statAlarmDock2 == 'ON':
            ipStop2 = await getIPdisplay(dockCode2)
            URL_STOP2 = f'http://{ipStop2}'
            dataStop2 = {"alarm":"0"}
            try:
                logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [ALARM] [SEND DISPLAY] SEND {dataStop2} {URL_STOP2}')
                rStop = await requests.post(URL_STOP2, json=dataStop2, timeout = 5)
                logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [ALARM] [SEND DISPLAY] SEUCCESFULLY SEND ALARM OFF')
                #AWAIT STAT ALARM
            except:
                delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
                cursor.execute(delpul, [dockCode2, "TO DISPLAY"])
                mydb.commit()
                logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
                pullHFERROR2 = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                valHFERROR2 = dockCode2, 'ALARMOFF', URL_STOP2, str(now), "TO DISPLAY"
                cursor.execute(pullHFERROR2, valHFERROR2)
                logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
                app.add_task(trySendDisplay(dockCode2, 'ALARMOFF'))
        try:
            updatedockAlarm2 = "UPDATE dock_alarm SET ALARM = %s, TIME_ALARM = %s, STATUS = %s WHERE DOCK = %s"
            valdockAlarm2 = [None, None, None, dockCode2]
            cursor.execute(updatedockAlarm2,valdockAlarm2)
            mydb.commit()
            logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE TO DOCK {dockCode2}')
        except:
            logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE ERROR')

        ipStateStop2 = await getIPdisplay(dockCode2)
        URL_StateStop2 = f'http://{ipStateStop2}'
        dataStateStop2 = {"state":"0"}
        # try:
        #     logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [SEND DISPLAY] SEND POST {URL_StateStop2}')
        #     rHF = await requests.post(URL_StateStop2, json=dataStateStop2, timeout = 5)
        #     logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [SEND DISPLAY] {dataStateStop2}')
        #     logger.info(f'[STOP DOCK]     :   [DOCK {dockCode2}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        # except:
        #     delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
        #     cursor.execute(delpul, [dockCode2, "TO DISPLAY"])
        #     mydb.commit()
        #     logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        #     pullHFERROR2 = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
        #     valHFERROR2 = dockCode2, 'STOP', URL_StateStop2, str(now), "TO DISPLAY"
        #     cursor.execute(pullHFERROR2, valHFERROR2)
        #     mydb.commit()
        #     logger.error(f'[STOP DOCK]    :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
        #     app.add_task(trySendDisplay(dockCode2, "STOP"))
    mydb.commit()
    y = json.dumps({'totalTime': durationStopCount})
    return text(y)




@gateway.route("/dock/alarm-stop/<dockCode>", methods=['GET','POST'])
async def dockAlarmStop(request, dockCode):
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)
    ###kudu tanya fahmi/mas sigit
    try:
        updateAlarmStopLog = "INSERT INTO log_alarm (DOCK, STATUS, NOTE, TIME) VALUES (%s, %s, %s, %s, %s)"
        valAlarmStopLog = dockCode, 'ALARM OFF', "END ALARM FROM SERVER", str(now)
        cursor.execute(updateAlarmStopLog, valAlarmStopLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[STOP ALARM]    :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG ALARM')
    except:
        logger.error(f'[STOP ALARM]   :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    ipStopAlarm = await getIPdisplay(dockCode)
    URL_STOPAlarm = f'http://{ipStop}'
    dataStopAlarm = {"alarm":"0"}
    try:
        logger.info(f'[STOP ALARM]    :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_STOP}')
        rStopAlarm = await requests.post(URL_STOPALARM, json=dataStopAlarm, timeout = 5)
        logger.info(f'[STOP ALARM]    :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        #AWAIT STAT ALARM
    except:
        logger.error(f'[STOP ALARM]   :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
        valHFERROR = dockCode, 'ALARMOFF', URL_STOP, str(now), "TO DISPLAY"
        cursor.execute(pullHFERROR, valHFERROR)
        mydb.commit()
        logger.error(f'[STOP ALARM]   :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay(dockCode, 'ALARMOFF'))
    mydb.commit()
    return text('OK')

@gateway.route("/dock/alarm-start/<dockCode>", methods=['GET','POST'])
async def dockAlarmStart(request, dockCode):
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    # print(database.is_connected)

    return text('OK')

@gateway.route("/dock/disable/<dockCode>", methods=['GET','POST'])
async def dockDisable(request, dockCode):
    #{'active':"0"}
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    try:
        dockCondition = "OFF"
        logger.info(f'[DISABLE DOCK]  :   [DOCK {dockCode}] [QUERY] SELECT CONDITION FROM LOADING_DOCK')
        sqlDisable ="SELECT TYPE FROM loading_dock WHERE DOCK = %s"
        cursor.execute(sqlDisable, [dockCode, ])
        dataDisable = cursor.fetchone()
        dockCondition = dataDisable[0]
        logger.info(f'[DISABLE DOCK]  :   [DOCK {dockCode}] [QUERY] DOCK CONDITION : {dockCondition}')
    except:
        dockCondition = "OFF"
        logger.error(f'[DISABLE DOCK] :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR SELECT FROM LOADING_DOCK')

    try:
        updateDisableDock = "UPDATE loading_dock SET TYPE = %s WHERE DOCK = %s"
        valDisableDock = ["DISABLE", dockCode]
        cursor.execute(updateDisableDock,valDisableDock)
        mydb.commit()
        logger.info(f'[DISABLE DOCK]  :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE CONDITION DOCK')
    except:
        logger.error(f'[DISABLE DOCK] :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR UPDATE LOADING DOCK')
    ipDisable = await getIPdisplay(dockCode)
    URL_Disable = f'http://{ipDisable}'
    dataDisable = {"active":"0"}
    try:
        logger.info(f'[DISABLE DOCK]  :   [DOCK {dockCode}] [SEND DISPLAY] SEND GET {URL_Disable}')
        rDisable = await requests.post(URL_Disable, json=dataDisable, timeout = 5)
        logger.info(f'[DISABLE DOCK]  :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND GET TO DISPLAY')
        #AWAIT STAT ALARM
    except:
        delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
        cursor.execute(delpul, [dockCode, "TO DISPLAY"])
        mydb.commit()
        logger.error(f'[DISABLE DOCK] :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullDISABLEERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
        valDISABLEERROR = dockCode, 'DISABLE', URL_Disable, str(now), "TO DISPLAY"
        cursor.execute(pullDISABLEERROR, valDISABLEERROR)
        mydb.commit()
        logger.error(f'[DISABLE DOCK] :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay(dockCode, 'DISABLE'))
    mydb.commit()
    return text('OK')


@gateway.route("/dock/enable/<dockCode>", methods=['GET','POST'])
async def dockEnable(request, dockCode):
    now = datetime.now()
    date_ = now.strftime("%Y%m%d")
    time_ = now.strftime("%H:%M:%S")
    try:
        dockConditionEn = "OFF"
        logger.info(f'[ENABLE DOCK]   :   [DOCK {dockCode}] [QUERY] SELECT CONDITION FROM LOADING_DOCK')
        sqlEnable ="SELECT TYPE FROM loading_dock WHERE DOCK = %s"
        cursor.execute(sqlEnable, [dockCode, ])
        dataEnable = cursor.fetchone()
        dockConditionEn = dataEnable[0]
        logger.info(f'[ENABLE DOCK]   :   [DOCK {dockCode}] [QUERY] DOCK CONDITION : {dockConditionEn}')
    except:
        dockConditionEn = "OFF"
        logger.error(f'[ENABLE DOCK]  :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR SELECT FROM LOADING_DOCK')

    try:
        updateEnableDock = "UPDATE loading_dock SET TYPE = %s WHERE DOCK = %s"
        valEnableDock = ["ENABLE", dockCode ]
        cursor.execute(updateEnableDock,valEnableDock)
        mydb.commit()
        logger.info(f'[ENABLE DOCK]   :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE CONDITION DOCK')
    except:
        logger.error(f'[ENABLE DOCK]  :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR UPDATE LOADING DOCK')
    ipEnable = await getIPdisplay(dockCode)
    URL_Enable = f'http://{ipEnable}'
    dataEnable = {"active":"1"}
    try:
        logger.info(f'[ENABLE DOCK]   :   [DOCK {dockCode}] [SEND DISPLAY] SEND GET {URL_Enable}')
        rEnable = await requests.post(URL_Enable, json=dataEnable, timeout = 5)
        logger.info(f'[ENABLE DOCK]   :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND GET TO DISPLAY')
        #AWAIT STAT ALARM
    except:
        delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
        cursor.execute(delpul, [dockCode, "TO DISPLAY"])
        mydb.commit()
        logger.error(f'[ENABLE DOCK]  :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
        pullENABLEERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
        valENABLEERROR = dockCode, 'ENABLE', URL_Enable, str(now), "TO DISPLAY"
        cursor.execute(pullENABLEERROR, valENABLEERROR)
        mydb.commit()
        logger.error(f'[ENABLE DOCK]  :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
        app.add_task(trySendDisplay(dockCode, 'ENABLE'))
    mydb.commit()
    return text('OK')


@gateway.route("/workTime", methods=['GET','POST'])
async def dockSchedule(request):
    now = datetime.now()
    logger.info(f"[DATA IN]       :  {request.body.decode('utf-8')}")
    #schedule = dict(eval(request.body.decode('utf-8')))
    schedule = request.body.decode('utf-8')
    schedule = json.loads(schedule)
    cursor.execute('TRUNCATE fasting')
    cursor.execute('TRUNCATE timetype')
    cursor.execute('TRUNCATE worktime')
    mydb.commit()

    try:
        for a in range (len(schedule['fasting'])):
            dateFrom = schedule['fasting'][a]['date_from'].split("T")[0]
            dateTo = schedule['fasting'][a]['date_to'].split("T")[0]
            try:
                sqlDateFast = "INSERT INTO fasting (dateFrom, dateTo) VALUES (%s, %s)"
                valueDateFast = str(dateFrom), str(dateTo)
                cursor.execute(sqlDateFast, valueDateFast)
                mydb.commit()
            except:
                pass
    except:
        pass
    try:
        for b in range (len(schedule['timeType'])):
            timeId = schedule['timeType'][b]['id']
            codeId = schedule['timeType'][b]['code']
            try:
                sqltimeType = "INSERT INTO timetype (id, code) VALUES (%s, %s)"
                valtimeType = int(timeId), codeId
                cursor.execute(sqltimeType, valtimeType)
                mydb.commit()
            except:
                pass
    except:
        pass

    try:
        for c in range (len(schedule['workTime'])):
            timeWorkId = schedule['workTime'][c]['time_type_id']
            timeWorkFrom = schedule['workTime'][c]['time_from']
            timeWorkTo = schedule['workTime'][c]['time_to']
            workBreakFlag = schedule['workTime'][c]['break_flag']
            try:
                sqltimeWork = "INSERT INTO worktime (timeTypeId, timeFrom, timeTo, breakFlag) VALUES (%s, %s, %s, %s)"
                valtimeWork = int(timeWorkId), str(timeWorkFrom), str(timeWorkTo), workBreakFlag
                cursor.execute(sqltimeWork, valtimeWork)
                mydb.commit()
            except:
                pass
    except:
        pass

    return text('OK')

@gateway.route("/<number>/Nopol", methods=['GET','POST'])
async def reqNopol(request, number):
    if int(number) < 25:
        if len(str(number)) == 1:
            dockCode = f"A0{number}"
        else:
            dockCode = f"A{number}"
    elif int(number) > 24:
        number = int(number)
        if number == 25:
            number = 1
        elif number == 26:
            number = 2
        elif number == 27:
            number = 3
        elif number == 28:
            number = 4
        dockCode = f"B0{number}"
    try:
        getReqNopol = "SELECT UID, POLICE_NO, STATUS FROM loading_dock WHERE DOCK = %s"
        cursor.execute(getReqNopol, [dockCode, ])
        GetNopol = cursor.fetchone()
        policeNopol = GetNopol[1]
        logger.info(f'[REQ NOPOL]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT NOPOL')
    except:
        policeNopol = "notfound"
        logger.error(f'[REQ NOPOL]    :   [DOCK {dockCode}] [QUERY] [ERROR] SELECT DURATION ERROR')
    if policeNopol != "notfound" and policeNopol:
        ipDisplay = await getIPdisplay(dockCode)
        try:
            policeNumber = policeNopol.upper()
            URL_BOOK = f'http://{ipDisplay}'
            dataBook = {"nopol":f"{policeNumber}"}
        except:
            pass
        try:
            logger.info(f'[REQ NOPOL]     :   [DOCK {dockCode}] [SEND DISPLAY] SEND {dataBook} {URL_BOOK}')
            rBooking = await requests.post(URL_BOOK, json=dataBook, timeout = 5)
            logger.info(f'[REQ NOPOL]     :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND {dataBook} TO DISPLAY')
        except:
            logger.error(f'[REQ NOPOL]    :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY]')
        mydb.commit()
    return text('OK')

@gateway.route("/<number>/Active", methods=['GET','POST'])
async def reqActive(request, number):
    if int(number) < 25:
        if len(str(number)) == 1:
            dockCode = f"A0{number}"
        else:
            dockCode = f"A{number}"
    elif int(number) > 24:
        number = int(number)
        if number == 25:
            number = 1
        elif number == 26:
            number = 2
        elif number == 27:
            number = 3
        elif number == 28:
            number = 4
        dockCode = f"B0{number}"
    try:
        getReqActive = "SELECT UID, POLICE_NO, STATUS, TYPE FROM loading_dock WHERE DOCK = %s"
        cursor.execute(getReqActive, [dockCode, ])
        GetActive = cursor.fetchone()
        GetActiveStat = GetActive[3]
        logger.info(f'[REQ ACTIVE]    :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT ACTIVE')
    except:
        GetActiveStat = "notfound"
        logger.error(f'[REQ ACTIVE]   :   [DOCK {dockCode}] [QUERY] [ERROR] SELECT DURATION ERROR')
    if GetActiveStat != "notfound" and GetActiveStat:
        if GetActiveStat == 'ENABLE':
            dataActive = {"active":"1"}
        else:
            dataActive = {"active":"0"}
        ipDisplay = await getIPdisplay(dockCode)
        URL_BOOK = f'http://{ipDisplay}'
        try:
            logger.info(f'[REQ ACTIVE]    :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {dataActive} {URL_BOOK}')
            rBooking = await requests.post(URL_BOOK, json=dataActive, timeout = 5)
            logger.info(f'[REQ ACTIVE]    :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND {dataActive} TO DISPLAY')
        except:
            logger.error(f'[REQ ACTIVE]   :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] ')
        mydb.commit()
    return text('OK')

@gateway.route("/<number>/State", methods=['GET','POST'])
async def reqState(request, number):
    if int(number) < 25:
        if len(str(number)) == 1:
            dockCode = f"A0{number}"
        else:
            dockCode = f"A{number}"
    elif int(number) > 24:
        number = int(number)
        if number == 25:
            number = 1
        elif number == 26:
            number = 2
        elif number == 27:
            number = 3
        elif number == 28:
            number = 4
        dockCode = f"B0{number}"
    try:
        getReqState = "SELECT UID, STATUS FROM dock_time_count WHERE DOCK = %s"
        cursor.execute(getReqState, [dockCode, ])
        GetState = cursor.fetchone()
        GetStateStat = GetState[1]
        logger.info(f'[REQ STATE]     :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY SELECT STATUS')
    except:
        GetStateStat = "notfound"
        logger.error(f'[REQ STATE]    :   [DOCK {dockCode}] [QUERY] [ERROR] SELECT DURATION ERROR')
    if GetStateStat != "notfound" and GetStateStat :
        if GetStateStat == 'START' or GetStateStat == 'TAP':
            dataState = {"state":"1"}
        else:
            dataState = {"state":"0"}
        ipDisplay = await getIPdisplay(dockCode)
        URL_BOOK = f'http://{ipDisplay}'
        try:
            logger.info(f'[REQ STATE]     :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {dataState} {URL_BOOK}')
            rBooking = await requests.post(URL_BOOK, json=dataState, timeout = 5)
            logger.info(f'[REQ STATE]     :   [DOCK {dockCode}] [SEND DISPLAY] SUCCESCFULLY SEND {dataState} TO DISPLAY')
        except:
            logger.error(f'[REQ STATE]    :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY]')
        mydb.commit()
    return text('OK')


@gateway.route("/mitigasi_HF/<dockCode>", methods=['GET', 'POST'])
@cross_origin(gateway)
async def mitigasiHF(request, dockCode):
    logger.info(f"[DATA IN]       :  [DOCK {dockCode}] {request.body.decode('utf-8')}")
    dataEPC = request.body.decode('utf-8').upper()
    now = datetime.now()
    if dataEPC == "OK":
        return text("OK")
    elif dataEPC == "1":
        try:
            getReqActive = "SELECT UID, POLICE_NO, STATUS, TYPE FROM loading_dock WHERE DOCK = %s"
            cursor.execute(getReqActive, [dockCode, ])
            GetActive = cursor.fetchone()
            GetActiveStat = GetActive[3]
            logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] STATUS DOCK {GetActiveStat}')
        except:
            GetActiveStat = "notfound"
        if GetActiveStat == 'DISABLE':
            dataActive = {"active":"0"}
            ipDisplay = await getIPdisplay(dockCode)
            URL_BOOK = f'http://{ipDisplay}'
            try:
                logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_BOOK} {dataActive} TO DISPLAY')
                rBooking = await requests.post(URL_BOOK, json=dataActive, timeout = 5)
            except:
                pass
        mydb.commit()
        return text("OK")
    try:
        updateHFLog = "INSERT INTO log_rfid (UID, DOCK, TIME) VALUES (%s, %s, %s)"
        valHFLog = dataEPC, dockCode, str(now)
        cursor.execute(updateHFLog, valHFLog)
        # logger.info(f'[BOOKING]       :   [LOG] {valBookingLog}')
        mydb.commit()
        logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [LOG] SUCCESCFULLY UPDATE TO LOG DB DOCK {dockCode}')
    except:
        logger.error(f'[MITIGASI]     :   [DOCK {dockCode}] [ERROR] [LOG] INSERT TO LOG ERROR')
    try:
        GetUidDock = "SELECT UID, POLICE_NO, STATUS, LAST_UPDATE FROM loading_dock WHERE DOCK = %s"
        cursor.execute(GetUidDock, [dockCode, ])
        GetUid = cursor.fetchone()
        UidDb = GetUid[0]
        PoliceNOHF = GetUid[1]
        statusHFLD = GetUid[2]
        LastTime = GetUid[3]
        logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [QUERY] SELECT UID FROM DOCK {dockCode}')
        logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [QUERY] {UidDb}')
    except:
        UidDb = "OFF"
        PoliceNOHF = "OFF"
        statusHFLD = "OFF"
        logger.error(f'[MITIGASI      :   [DOCK {dockCode}] [ERROR] [QUERY] UID NOT FOUND IN DOCK {dockCode}')
    try:
        logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [QUERY] CHECK DOUBLE DOCK')
        GetUidDock2 = "SELECT DOCK, UID, POLICE_NO, STATUS FROM loading_dock WHERE UID = %s AND DOCK != %s"
        cursor.execute(GetUidDock2, [dataEPC, dockCode])
        GetUid2 = cursor.fetchone()
        dockCode2 = GetUid2[0]
        UidDb2 = GetUid2[1]
        PoliceNOHF2 = GetUid2[2]
        statusHFLD2 = GetUid2[3]
        logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [QUERY] {UidDb2}')
    except:
        dockCode2 = None
        UidDb2 = "OFF"
        PoliceNOHF2 = "OFF"
        statusHFLD2 = "OFF"
        logger.info(f'[MITIGASI]      :   [DOCK {dockCode}] [QUERY] NO DOUBLE DOCK')

    if UidDb == dataEPC and statusHFLD == "BOOKING":
        logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [TAP] UID MATCH')
        ipDisplayHF = await getIPdisplay(dockCode)
        policeNumberHF = PoliceNOHF
        URL_HF = f'http://{ipDisplayHF}'
        dataStartDisplay = {"state":"1"}
        dataBookPolice1 = {"nopol":f"{policeNumberHF}"}
        try:
            app.add_task(tapInSend(dockCode))
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_HF}')
            rHF = await requests.post(URL_HF, json=dataStartDisplay, timeout = 5)
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [SEND DISPLAY] {dataStartDisplay}')
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
            pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dockCode, 'START', URL_HF, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay(dockCode, 'START'))

        dataHF = {'uid':dataEPC,
                'dockCode':dockCode,
                'time':str(now) }
        ipServerHF = await getIPServer(dockCode)
        URL_SERVERIN = f"http://{ipServerHF}/dock/in"
        try:
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [SEND SERVER] {dataHF}')
            rHFServer = await requests.post(URL_SERVERIN, json=dataHF, timeout = 5)
            print(rHFServer.status_code)
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [SEND SERVER] SUCCESCFULLY SEND TO {URL_SERVERIN}')
        except:
            delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
            cursor.execute(delpul, [dockCode, "TAP START IN"])
            mydb.commit()
            logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SEND TO SERVER ERROR')
            pullHFERROR = "INSERT INTO send_error (UID, DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s, %s)"
            valHFERROR = dataEPC, dockCode, 'TAP', URL_SERVERIN, str(now), "TAP START IN"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SAVE TO DB PULLING')
            app.add_task(trySendHfServer(dockCode, 'TAP'))
        try:
            updateDockCount = "UPDATE dock_time_count SET UID = %s, STATUS = %s WHERE DOCK = %s"
            valDockCount = [dataEPC, 'TAP', dockCode]
            cursor.execute(updateDockCount,valDockCount)
            mydb.commit()
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE TO DOCK_COUNT')
        except:
            logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode}] [ERROR] [QUERY] ERROR TO UPDATE TO DOCK_COUNT')
        try:
            updateDockHF = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valDockHF = ["TAP", str(now), dockCode]
            cursor.execute(updateDockHF,valDockHF)
            mydb.commit()
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE STATUS {dockCode}')
        except:
            logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE STATUS TO DOCK {dockCode} ERROR')
        if UidDb == UidDb2 and PoliceNOHF == PoliceNOHF2:
            logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode2}] DOUBLE DOCK DETECT')
            ipDisplayHF2 = await getIPdisplay(dockCode2)
            policeNumberHF2 = PoliceNOHF2
            URL_HF2 = f'http://{ipDisplayHF2}'
            dataStartDisplay2 = {"state":"1"}
            dataBookPolice = {"nopol":f"{policeNumberHF2}"}
            try:
                app.add_task(tapInSend(dockCode2))
                logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode2}] [SEND DISPLAY] SEND POST {URL_HF2}')
                rHF = await requests.post(URL_HF2, json=dataStartDisplay2, timeout = 5)
                logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode2}] [SEND DISPLAY] {dataStartDisplay2}')
                logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode2}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
            except:
                logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
                pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                valHFERROR = dockCode2, 'START', URL_HF, str(now), "TO DISPLAY"
                cursor.execute(pullHFERROR, valHFERROR)
                mydb.commit()
                logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
                app.add_task(trySendDisplay(dockCode2, 'START'))
            try:
                updateDockCount2 = "UPDATE dock_time_count SET UID = %s, STATUS = %s WHERE DOCK = %s"
                valDockCount2 = [UidDb2, 'TAP', dockCode2]
                cursor.execute(updateDockCount2,valDockCount2)
                mydb.commit()
                logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE TO DOCK_COUNT')
            except:
                logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode2}] [ERROR] [QUERY] ERROR TO UPDATE TO DOCK_COUNT')
            try:
                updateDockHF2 = "UPDATE loading_dock SET STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
                valDockHF2 = ["TAP", str(now), dockCode2]
                cursor.execute(updateDockHF2,valDockHF2)
                mydb.commit()
                logger.info(f'[MITIGASI IN]   :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE STATUS {dockCode2}')
            except:
                logger.error(f'[MITIGASI IN]  :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE STATUS TO DOCK {dockCode2} ERROR')


    elif UidDb == dataEPC and statusHFLD == "STOP":
        logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [TAP] UID MATCH')
        timeTerpal = int((now-LastTime).total_seconds())
        dataHF = {"uid":dataEPC,
                    "timeTerpal":timeTerpal,
                    "dockCode":dockCode}
                    #"dockSekunder":dockCode2}
        logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [TIME] TERPAL TIME {timeTerpal}')
        ipServerHF = await getIPServer(dockCode)
        URL_SERVEROUT = f"http://{ipServerHF}/dock/out"
        try:
            logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [SEND SERVER] {dataHF}')
            rHFServer = await requests.post(URL_SERVEROUT, json=dataHF, timeout = 5)
            print(rHFServer.status_code)
            logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [SEND SERVER] SUCCESCFULLY SEND TO {URL_SERVEROUT}')
        except:
            logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SEND TO SERVER ERROR')
            pullHFERROR = "INSERT INTO send_error (UID, DOCK, STATUS, URL, TOTALTIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s, %s)"
            valHFERROR = dataEPC, dockCode, 'TERPAL', URL_SERVEROUT, timeTerpal, "TAP START IN"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode}] [ERROR] [SEND SERVER] SAVE TO DB PULLING')
            app.add_task(trySendHfServer(dockCode, 'TERPAL'))
        try:
            updateTerpalDock = "UPDATE loading_dock SET UID = %s, POLICE_NO = %s, STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
            valTerpalDock = [None, None, "STOP", str(now), dockCode]
            cursor.execute(updateTerpalDock,valTerpalDock)
            mydb.commit()
            logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [QUERY] SUCCESCFULLY UPDATE LOADING DOCK STATUS {dockCode}')
        except:
            logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode}] [ERROR] [QUERY] UPDATE TO LOADING DOCK ERROR')
        ipStateStop = await getIPdisplay(dockCode)
        URL_StateStop = f'http://{ipStateStop}'
        dataStateStop = {"state":"0"}
        try:
            app.add_task(tapOutSend(dockCode))
            logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [SEND DISPLAY] SEND POST {URL_StateStop}')
            rHF = await requests.post(URL_StateStop, json=dataStateStop, timeout = 5)
            logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [SEND DISPLAY] {dataStateStop}')
            logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
        except:
            delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
            cursor.execute(delpul, [dockCode, "TO DISPLAY"])
            mydb.commit()
            logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
            pullHFERROR = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
            valHFERROR = dockCode, 'STOP', URL_StateStop, str(now), "TO DISPLAY"
            cursor.execute(pullHFERROR, valHFERROR)
            mydb.commit()
            logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
            app.add_task(trySendDisplay(dockCode, 'STOP'))
        ipStopp = await getIPdisplay(dockCode)
        URL_STOPp = f'http://{ipStopp}'
        dataStopp = {"alarm":"0"}
        try:
            rStop1 = await requests.post(URL_STOPp, json=dataStopp, timeout = 5)
        except:
            pass
        if UidDb == UidDb2 and PoliceNOHF == PoliceNOHF2:

            try:
                updateTerpalDock = "UPDATE loading_dock SET UID = %s, POLICE_NO = %s, STATUS = %s, LAST_UPDATE = %s  WHERE DOCK = %s"
                valTerpalDock = [None, None, "STOP", str(now), dockCode2]
                cursor.execute(updateTerpalDock,valTerpalDock)
                mydb.commit()
                logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode2}] [QUERY] SUCCESCFULLY UPDATE LOADING DOCK STATUS {dockCode}')
            except:
                logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode2}] [ERROR] [QUERY] UPDATE TO LOADING DOCK ERROR')
            ipStopp2 = await getIPdisplay(dockCode2)
            URL_STOPp2 = f'http://{ipStopp2}'
            dataStopp2 = {"alarm":"0"}
            try:
                rStop2 = await requests.post(URL_STOPp2, json=dataStopp2, timeout = 5)
            except:
                pass
            ipStateStop2 = await getIPdisplay(dockCode2)
            URL_StateStop2 = f'http://{ipStateStop2}'
            dataStateStop2 = {"state":"0"}
            try:
                app.add_task(tapOutSend(dockCode2))
                logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode2}] [SEND DISPLAY] SEND POST {URL_StateStop2}')
                rHF = await requests.post(URL_StateStop2, json=dataStateStop2, timeout = 5)
                logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode2}] [SEND DISPLAY] {dataStateStop2}')
                logger.info(f'[MITIGASI OUT]  :   [DOCK {dockCode2}] [SEND DISPLAY] SEUCCESFULLY SEND POST TO DISPLAY')
            except:
                delpul = "DELETE FROM send_error WHERE DOCK = %s AND SEND_STATUS = %s"
                cursor.execute(delpul, [dockCode2, "TO DISPLAY"])
                mydb.commit()
                logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SEND TO DISPLAY ERROR')
                pullHFERROR2 = "INSERT INTO send_error (DOCK, STATUS, URL, TIME, SEND_STATUS) VALUES (%s, %s, %s, %s, %s)"
                valHFERROR2 = dockCode2, 'STOP', URL_StateStop2, str(now), "TO DISPLAY"
                cursor.execute(pullHFERROR2, valHFERROR2)
                mydb.commit()
                logger.error(f'[MITIGASI OUT] :   [DOCK {dockCode2}] [ERROR] [SEND DISPLAY] SAVE TO DB PULLING')
                app.add_task(trySendDisplay(dockCode2, "STOP"))

    elif UidDb != dataEPC and statusHFLD == "BOOKING":
        #ALARM
        logger.warning(f'[HF RFID]       :   [DOCK {dockCode}] [TAP] NOT MATCH')

    mydb.commit()
    return text('OK')


@gateway.route("/<number>", methods=['GET','POST'])
async def reqRandom(request, number):
    return text('OK')

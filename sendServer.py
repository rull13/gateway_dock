import asyncio
from gateway_dock import cursor, mydb, app, logger
from datetime import datetime, date, timedelta
import MySQLdb
import requests_async as requests

async def sendErrorDisplay(dock=None, dockStatus=None):
    if dock and dockStatus:
        try:
            errorBooking = "SELECT ID, DOCK, POLICE_NO, STATUS, URL FROM send_error WHERE SEND_STATUS = %s and DOCK = %s and STATUS = %s ORDER BY ID ASC LIMIT 1"
            cursor.execute(errorBooking, ["TO DISPLAY", dock, dockStatus])
            valErrorBooking = cursor.fetchone()
            idErrorBook = valErrorBooking[0]
            DockErrorBook = valErrorBooking[1]
            ErrorNoPol = valErrorBooking[2]
            statErrorBook = valErrorBooking[3]
            urlErrorBook = valErrorBooking[4]
            sendErrorBookStat = True
        except:
            idErrorBook = 'OFF'
            DockErrorBook = 'OFF'
            urlErrorBook = 'OFF'
            ErrorNoPol = "OFF"
            statErrorBook = "OFF"
            sendErrorBookStat = False
    else:
        try:
            errorBooking = "SELECT ID, DOCK, POLICE_NO, STATUS, URL FROM send_error WHERE SEND_STATUS = %s ORDER BY ID ASC LIMIT 1"
            cursor.execute(errorBooking, ["TO DISPLAY"])
            valErrorBooking = cursor.fetchone()
            idErrorBook = valErrorBooking[0]
            DockErrorBook = valErrorBooking[1]
            ErrorNoPol = valErrorBooking[2]
            statErrorBook = valErrorBooking[3]
            urlErrorBook = valErrorBooking[4]
            sendErrorBookStat = True
        except:
            idErrorBook = 'OFF'
            DockErrorBook = 'OFF'
            urlErrorBook = 'OFF'
            ErrorNoPol = "OFF"
            statErrorBook = "OFF"
            sendErrorBookStat = False
    if sendErrorBookStat:
        if statErrorBook == 'BOOKING':
            #ada dockCode
            try:
                dataErrorBook = {"nopol":f"{ErrorNoPol}"}
                logger.info(f'[PULL BOOKING]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL BOOKING]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL BOOKING]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] SUCCESCFULLY SEND GET TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL BOOKING] : [SEND DISPLAY]  [DOCK {DockErrorBook}] [ERROR] SEND TO DISPLAY ERROR')
        elif statErrorBook == 'START':
            #ada dockCode
            try:
                dataErrorBook = {"state":"1"}
                logger.info(f'[PULL START]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL START]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL START]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL START]   : [SEND DISPLAY]  [DOCK {DockErrorBook}] [ERROR] SEND TO DISPLAY ERROR')
        elif statErrorBook == 'STOP':
            #ada dockCode
            try:
                dataErrorBook = {"state":"0"}
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL STOP]     : [SEND DISPLAY] [DOCK {DockErrorBook}]  SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL STOP]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] [ERROR] SEND TO DISPLAY ERROR')
        elif statErrorBook == 'ALARMCOUNT':
            #udah ada dock code nya
            try:
                dataErrorBook = {"alarm":"1"}
                logger.info(f'[PULL COUNT]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL COUNT]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL COUNT]    : [SEND DISPLAY]  [DOCK {DockErrorBook}] SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL COUNT]   : [SEND DISPLAY] [DOCK {DockErrorBook}]  [ERROR] SEND TO DISPLAY ERROR')
        elif statErrorBook == 'ALARMOFF':
            #ada dock code
            try:
                dataErrorBook = {"alarm":"0"}
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  [DOCK {DockErrorBook}] SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL COUNT]   : [SEND DISPLAY]  [DOCK {DockErrorBook}] [ERROR] SEND TO DISPLAY ERROR')
        elif statErrorBook == 'DISABLE':
            try:
                dataErrorBook = {"active":"0"}
                logger.info(f'[PULL DISABLE]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL DISABLE]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL DISABLE]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL DISBALE] : [SEND DISPLAY]  [DOCK {DockErrorBook}] [ERROR] SEND TO DISPLAY ERROR')
        elif statErrorBook == 'ENABLE':
            try:
                dataErrorBook = {"active":"1"}
                logger.info(f'[PULL ENABLE]   : [SEND DISPLAY] [DOCK {DockErrorBook}] SEND POST {dataErrorBook}')
                logger.info(f'[PULL ENABLE]   : [SEND DISPLAY] [DOCK {DockErrorBook}] SEND TO URL {urlErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 5)
                logger.info(f'[PULL ENABLE]   : [SEND DISPLAY] [DOCK {DockErrorBook}] SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL ENABLE]  : [SEND DISPLAY]  [DOCK {DockErrorBook}] [ERROR] SEND TO DISPLAY ERROR')
    if idErrorBook != 'OFF':
        mydb.commit()
        return False
    else:
        mydb.commit()
        return True

async def sendErrorTapIn(dock = None, dockStatus = None):
    if dock and dockStatus:
        try:
            errorHFServer = "SELECT ID, UID, DOCK,  STATUS, URL, TIME, TOTALTIME FROM send_error WHERE SEND_STATUS = %s  and DOCK = %s and STATUS = %s ORDER BY ID ASC LIMIT 1"
            cursor.execute(errorHFServer, ["TAP START IN", dock, dockStatus])
            valErrorHFServer = cursor.fetchone()
            idErrorHF = valErrorHFServer[0]
            uidErrorHF = valErrorHFServer[1]
            DockErrorHF = valErrorHFServer[2]
            statErrorHF = valErrorHFServer[3]
            TimeErrorHF = valErrorHFServer[5]
            urlErrorHF = valErrorHFServer[4]
            totalTImeErrorHF = valErrorHFServer[6]
            sendErrorHF = True
        except:
            idErrorHF = 'OFF'
            uidErrorHF = 'OFF'
            DockErrorHF = 'OFF'
            TimeErrorHF = 'OFF'
            urlErrorHF = 'OFF'
            statErrorHF = 'OFF'
            totalTImeErrorHF = 'OFF'
            sendErrorHF = False
    else:
        try:
            errorHFServer = "SELECT ID, UID, DOCK,  STATUS, URL, TIME, TOTALTIME FROM send_error WHERE SEND_STATUS = %s ORDER BY ID ASC LIMIT 1"
            cursor.execute(errorHFServer, ["TAP START IN"])
            valErrorHFServer = cursor.fetchone()
            idErrorHF = valErrorHFServer[0]
            uidErrorHF = valErrorHFServer[1]
            DockErrorHF = valErrorHFServer[2]
            statErrorHF = valErrorHFServer[3]
            TimeErrorHF = valErrorHFServer[5]
            urlErrorHF = valErrorHFServer[4]
            totalTImeErrorHF = valErrorHFServer[6]
            sendErrorHF = True
        except:
            idErrorHF = 'OFF'
            uidErrorHF = 'OFF'
            DockErrorHF = 'OFF'
            TimeErrorHF = 'OFF'
            urlErrorHF = 'OFF'
            statErrorHF = 'OFF'
            totalTImeErrorHF = 'OFF'
            sendErrorHF = False
    if sendErrorHF:
        if statErrorHF == 'TAP':
            dataErrorHF = {'uid':uidErrorHF,
                    'dockCode':DockErrorHF,
                    'time':str(TimeErrorHF) }
            try:
                logger.info(f'[PULL HF]       :   [SEND SERVER] [DOCK {DockErrorHF}] {dataErrorHF}')
                logger.info(f'[PULL HF]       :   [SEND SERVER] [DOCK {DockErrorHF}] {urlErrorHF}')
                rHFError = await requests.post(urlErrorHF, json=dataErrorHF,timeout = 5)
                logger.info(f'[PULL HF]       :   [SEND SERVER] [DOCK {DockErrorHF}] SUCCESCFULLY SEND TO SERVER')

                sqldelErrorHF = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelErrorHF, [idErrorHF,])
                mydb.commit()
            except:
                logger.error(f'[PULL HF]      :   [SEND SERVER] [DOCK {DockErrorHF}] [ERROR] SEND TO SERVER ERROR')
        elif statErrorHF == 'TERPAL':
            dataErrorHF = {'timeTerpal':totalTImeErrorHF }
            try:
                logger.info(f'[PULL HF]       :   [SEND SERVER] [DOCK {DockErrorHF}] {dataErrorHF}')
                logger.info(f'[PULL HF]       :   [SEND SERVER] [DOCK {DockErrorHF}] {urlErrorHF}')
                rHFError = await requests.post(urlErrorHF, json=dataErrorHF,timeout = 5)
                logger.info(f'[PULL HF]       :   [SEND SERVER] [DOCK {DockErrorHF}] SUCCESCFULLY SEND TO SERVER')

                sqldelErrorHF = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelErrorHF, [idErrorHF,])
                mydb.commit()
            except:
                logger.error(f'[PULL HF]      :   [SEND SERVER] [DOCK {DockErrorHF}] [ERROR] SEND TO SERVER ERROR')
    if idErrorHF != 'OFF':
        mydb.commit()
        return False
    else:
        mydb.commit()
        return True

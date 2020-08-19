import asyncio
from gateway_dock import cursor, mydb, app, conn, cursorsql, logger
from datetime import datetime, date, timedelta
import MySQLdb
import requests_async as requests

async def sendErrorDisplay():
    try:
        errorBooking = "SELECT ID, POLICE_NO, STATUS, URL FROM send_error WHERE SEND_STATUS = %s ORDER BY ID ASC LIMIT 1"
        cursor.execute(errorBooking, ["TO DISPLAY"])
        valErrorBooking = cursor.fetchone()
        idErrorBook = valErrorBooking[0]
        ErrorNoPol = valErrorBooking[1]
        statErrorBook = valErrorBooking[2]
        urlErrorBook = valErrorBooking[3]
        sendErrorBookStat = True
    except:
        idErrorBook = 'OFF'
        urlErrorBook = 'OFF'
        ErrorNoPol = "OFF"
        statErrorBook = "OFF"
        sendErrorBookStat = False
    if sendErrorBookStat:
        if statErrorBook == 'BOOKING':
            try:
                dataErrorBook = {'nopol':ErrorNoPol}
                logger.info(f'[PULL BOOKING]  : [SEND DISPLAY]  SEND POST {dataErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 2)
                logger.info(f'[PULL BOOKING]  : [SEND DISPLAY]  SUCCESCFULLY SEND GET TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL BOOKING] : [SEND DISPLAY]  SEND TO DISPLAY ERROR')
        elif statErrorBook == 'START':
            try:
                dataErrorBook = {'State':1}
                logger.info(f'[PULL START]    : [SEND DISPLAY]  SEND POST {dataErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 2)
                logger.info(f'[PULL START]    : [SEND DISPLAY]  SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL START]   : [SEND DISPLAY]  SEND TO DISPLAY ERROR')
        elif statErrorBook == 'ALARMCOUNT':
            try:
                dataErrorBook = {'alarm':1}
                logger.info(f'[PULL COUNT]    : [SEND DISPLAY]  SEND POST {dataErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 2)
                logger.info(f'[PULL COUNT]    : [SEND DISPLAY]  SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL COUNT]   : [SEND DISPLAY]  SEND TO DISPLAY ERROR')
        elif statErrorBook == 'ALARMOFF':
            try:
                dataErrorBook = {'alarm':0}
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  SEND POST {dataErrorBook}')
                rBookingError = await requests.post(urlErrorBook, json=dataErrorBook, timeout = 2)                
                logger.info(f'[PULL STOP]     : [SEND DISPLAY]  SUCCESCFULLY SEND POST TO DISPLAY')
                sqldelBook = 'DELETE FROM send_error WHERE id = %s'
                cursor.execute(sqldelBook, [idErrorBook,])
                mydb.commit()
            except:
                logger.error(f'[PULL COUNT]   : [SEND DISPLAY]  SEND TO DISPLAY ERROR')
    if idErrorBook != 'OFF':
        return False
    else:
        return True

async def sendErrorTapIn():
    try:
        errorHFServer = "SELECT ID, UID, DOCK, URL, TIME FROM send_error WHERE SEND_STATUS = %s ORDER BY ID ASC LIMIT 1"
        cursor.execute(errorHFServer, ["TAP START IN"])
        valErrorHFServer = cursor.fetchone()
        idErrorHF = valErrorHFServer[0]
        uidErrorHF = valErrorHFServer[1]
        DockErrorHF = valErrorHFServer[2]
        TimeErrorHF = valErrorHFServer[4]
        urlErrorHF = valErrorHFServer[3]
        sendErrorHF = True
    except:
        idErrorHF = 'OFF'
        uidErrorHF = 'OFF'
        DockErrorHF = 'OFF'
        TimeErrorHF = 'OFF'
        urlErrorHF = 'OFF'
        sendErrorHF = False
    if sendErrorHF:
        dataErrorHF = {'uidRfid':uidErrorHF,
                'dockCode':DockErrorHF,
                'time':str(TimeErrorHF) }
        try:
            logger.info(f'[PULL HF]       :   [SEND SERVER] {dataErrorHF}')
            rHFError = await requests.post(urlErrorHF, json=dataErrorHF,timeout = 2)
            logger.info(f'[PULL HF]       :   [SEND SERVER] SUCCESCFULLY SEND TO SERVER')

            sqldelErrorHF = 'DELETE FROM send_error WHERE id = %s'
            cursor.execute(sqldelErrorHF, [idErrorHF,])
            mydb.commit()
        except:
            logger.error(f'[PULL HF]      :   SEND TO SERVER ERROR')
    if idErrorHF != 'OFF':
        return False
    else:
        return True

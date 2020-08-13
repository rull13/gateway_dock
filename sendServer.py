import asyncio
from gateway_dock import cursor, mydb, app, conn, cursorsql, logger
from datetime import datetime, date, timedelta
import MySQLdb
import requests_async as requests

async def sendErrorBook():
    try:
        errorBooking = "SELECT ID, URL FROM send_error WHERE SEND_STATUS = %s ORDER BY ID ASC LIMIT 1"
        cursor.execute(errorBooking, ["BOOKING"])
        valErrorBooking = cursor.fetchone()
        idErrorBook = valErrorBooking[0]
        urlErrorBook = valErrorBooking[1]
        sendErrorBookStat = True
    except:
        idErrorBook = 'OFF'
        urlErrorBook = 'OFF'
        sendErrorBookStat = False
    if sendErrorBookStat:
        try:
            logger.info(f'[PULL BOOKING]  :   SEND GET {urlErrorBook}')
            rBookingError = await requests.get(urlErrorBook, timeout = 2)
            logger.info(f'[PULL BOOKING]  :   SUCCESCFULLY SEND GET TO DISPLAY')
            sqldelBook = 'DELETE FROM send_error WHERE id = %s'
            cursor.execute(sqldelBook, [idErrorBook,])
            mydb.commit()
        except:
            logger.error(f'[PULL BOOKING] :   SEND TO DISPLAY ERROR')
    if idErrorBook != 'OFF':
        return False
    else:
        return True

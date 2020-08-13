import asyncio
from gateway_dock import cursor, mydb, app, conn, cursorsql, logger
import pyodbc
from datetime import datetime, date, timedelta
import MySQLdb
async def dbServer():
    global cursorsql, conn
    sqlDbServer = "SELECT ip, port, dbname, dbport, dbuid, dbpass FROM ipserver"
    cursor.execute(sqlDbServer)
    datDbServer = cursor.fetchone()
    conn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}',
                                   server=f'{datDbServer[0]},{datDbServer[3]}',
                                   database=f'{datDbServer[2]}',
                                   uid=f'{datDbServer[4]}',pwd=f'{datDbServer[5]}')
    cursorsql = conn.cursor()
    logger.info("[SQL SERVER]   :   SUCCESCFULLY CONNECTED to SQL SERVER")


async def reconnenctToDbServer():
    await asyncio.sleep(60)
    '''
    CHECKING IF GATEWAY CONNECTED TO DATABASE SERVER
    AND RECONNECTING IF DISCONNENCTED
    '''
    try:
        testping = "SELECT NAME FROM TIME_TYPE WHERE ID = 1"
        cursorsql.execute(testping)
        testype = cursorsql.fetchone()
        tstp = testype
        logger.info("[DB SERVER]     :   CONNECTED to DB SERVER")
    except:
        try:
            app.add_task(dbServer())
        except:
            logger.warning("[DB SERVER]    :   ERROR NOT CONNECTED")
    app.add_task(reconnenctToDbServer())

async def reconMysql():
    await asyncio.sleep(60)
    try:
        mydb.ping(True)
    except:
        cursor = mydb.cursor()
    app.add_task(reconMysql())

async def getIPdisplay(dock):
    try:
        sqlGetIpDisplay = "SELECT IP FROM dock_alarm WHERE ID = %s"
        cursor.execute(sqlGetIpDisplay, dock)
        dataIpDisplay = cursor.fetchone()
        ip = dataIpDisplay[0]
        return ip
    except:
        logger.error(f'[CONFIG]       :   GETTING IP {dock} ERROR')
        return 0

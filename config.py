import asyncio
from gateway_dock import database, app
import pyodbc
from datetime import datetime, date, timedelta

async def dbServer():
    global cursorsql, conn
    query = "SELECT ip, port, dbname, dbport, dbuid, dbpass FROM ipserver"
    dat = await database.fetch_one(query=query)
    SERVER = f'{dat[0]},{dat[3]}'
    dbname = f'{dat[2]}'
    dbuid = f'{dat[4]}'
    dbpwd = f'{dat[5]}'
    conn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}',
                                   server=SERVER,
                                   database=dbname,
                                   uid=dbuid,pwd=dbpwd)
    cursorsql = conn.cursor()
    print("[SQL SERVER]                :   SUCCESCFULLY CONNECTED to SQL SERVER")


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
        print("[DB SERVER]                 :   CONNECTED to DB SERVER")
    except:
        try:
            app.add_task(dbServer())
            print("[SQL SERVER]               :   SUCCESCFULLY CONNECTED to SQL SERVER")
        except:
            print("[DB SERVER]                :   ERROR")
    app.add_task(reconnenctToDbServer())

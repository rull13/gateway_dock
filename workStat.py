from datetime import datetime, date, timedelta
import datetime as dt
import asyncio
from  gateway_dock import cursor, app, mydb

async def timetypeid():
    '''
    SEARCH ID DAY IN SERVER
    WILL RETURN TIME START WORK, TIME END WORK, AND SHIFT ID
    '''
    now = datetime.now()
    # now = datetime(2020, 6, 15, 12, 15, 59)
    datenow = now.date()
    timenow = now.time()
    udn = datenow.weekday()
    flag = "ACTIVE"
    timeid = 'OFF'
    if 0 <= udn <= 3:
        udn = "R"
    else:
        udn = "NR"
    datefrom = "0000-00-00"
    dateto = "0000-00-00"
    try:
        sqlfasting = "SELECT dateFrom, dateTo FROM fasting WHERE %s BETWEEN dateFrom AND dateTo"
        cursor.execute(sqlfasting,[str(datenow),])
        fasting = cursor.fetchone()
        mydb.commit()
        datefrom = str(fasting[0])
        dateto = str(fasting[1])
    except:
        pass
    if datefrom != dateto:
        if datefrom <= str(datenow) <= dateto:
            udn = udn + 'F'
    try:
        sqltimetype = "SELECT id FROM timetype WHERE CODE = %s"
        value = [udn,]
        cursor.execute(sqltimetype, (value))
        timetype = cursor.fetchone()
        timeid = timetype[0]
        mydb.commit()
    except:
        pass

    return [timeid, timenow, now]


class Timeshift():
    async def timework(self):
        '''
        THIS CODE WILL EXCEUTE WHEN
        SHIFT 1 TIME IS OVER
        COMPRAING TIME REAL AND TIME SHIFT
        AND MAKE THIS GATEWAY CANT SAVE THE DATA
        '''

        typeid = await timetypeid()
        timeid = typeid[0]
        timenow = typeid[1]
        timefrom ="OFF"
        timeto = "OFF"
        breakflag = "OFF"
        if timeid != 'OFF':
            try:
                '''
                WIIL TRY SEARCHING IF TIME NOW BETWEEN TIME WORK
                '''
                sqlsequen = "SELECT timeFrom, timeTo, breakFlag FROM worktime WHERE timeTypeId = %s"
                sqlsequen2 = " AND %s BETWEEN timeFrom AND timeTo"
                sql = sqlsequen+sqlsequen2
                value = [timeid, timenow]
                cursor.execute(sql, (value))
                timeseq = cursor.fetchone()
                mydb.commit()
                timefrom = timeseq[0]
                timeto = timeseq[1]
                breakflag = timeseq[2]
            except:
                pass
            try:
                '''
                WILL TRY SEARCHING IF END TIME WORK BETWEEN TIME NOW AND TIME START WORK
                THIS LINE WORKING IF TIME START AND TIME END HAVE A DIFFERENT DAY
                TIME NOW HAS A SAME DAY WITH TIME END WORK
                '''
                sqlsequen = "SELECT timeFrom, timeTo, breakFlag FROM worktime WHERE timeTypeId = %s"
                sqlsequen2 = " AND timeFrom BETWEEN timeTo AND %s"
                sql = sqlsequen+sqlsequen2
                value = [timeid, timenow]
                cursor.execute(sql, (value))
                timeseq = cursor.fetchone()
                mydb.commit()
                timefrom = timeseq[0]
                timeto = timeseq[1]
                breakflag = timeseq[2]
            except:
                pass
            try:
                '''
                WILL TRY SEARCHING IF END TIME WORK BETWEEN TIME NOW AND TIME START WORK
                THIS LINE WORKING IF TIME START AND TIME END HAVE A DIFFERENT DAY
                TIME NOW HAS A SAME DAY WITH TIME START WORK
                '''
                sqlsequen = "SELECT timeFrom, timeTo, breakFlag FROM worktime WHERE timeTypeId = %s"
                sqlsequen2 = " AND timeTo BETWEEN %s AND timeFrom"
                sql = sqlsequen+sqlsequen2
                value = [timeid, timenow]
                cursor.execute(sql, (value))
                timeseq = cursor.fetchone()
                mydb.commit()
                timefrom = timeseq[0]
                timeto = timeseq[1]
                breakflag = timeseq[2]
            except:
                pass
        # print(f"TIME START WORK: {timefrom}")
        # print(f"TIME END WORK: {timeto}")
        if timefrom != timeto and breakflag.upper() != 'Y':
            '''
            IF TIME WORK START
            '''
            return [breakflag, timefrom, timeto, timeid, 'WORK_ON']
        else:
            '''
            IF TIME WORK END
            '''
            return [breakflag, timefrom, timeto, timeid, 'WORK_OFF']
    #
    # async def overtime(self):
    #     '''
    #     THIS CODE WILL EXCEUTE WHEN
    #     SHIFT 2 TIME IS OVER
    #     COMPRAING TIME REAL AND TIME SHIFT
    #     AND MAKE THIS GATEWAY CANT SAVE THE DATA
    #     '''
    #     from gateway_dock.config import cursorsql, conn
    #     typeid = await timetypeid()
    #     timeid = typeid[0]
    #     timenow = typeid[1]
    #     timedatetime = typeid[2]
    #     timefrom ="OFF"
    #     timeto = "OFF"
    #     if timeid != 'OFF':
    #
    #         try:
    #             sqlbreak = "SELECT DATETIME_FROM, DATETIME_TO FROM OVERTIME WHERE "
    #             sqlbreak2 = "? BETWEEN DATETIME_FROM AND DATETIME_TO"
    #             sql = sqlbreak+sqlbreak2
    #             value = [timedatetime]
    #             cursorsql.execute(sql, (value))
    #             timeseq = cursorsql.fetchone()
    #             conn.commit()
    #             timefrom = timeseq[0]
    #             timeto = timeseq[1]
    #         except:
    #             pass
    #     # print(f"TIME START REST: {timefrom}")
    #     # print(f"TIME END REST: {timeto}")
    #     if timefrom != timeto:
    #         '''
    #         OVERTIME START
    #         '''
    #         return [timefrom.time(), timeto.time(), 'OVERTIME_ON']
    #     else:
    #         '''
    #         OVERTIME END
    #         '''
    #         return [timefrom, timeto, 'OVERTIME_OFF']


import MySQLdb
mydb = MySQLdb.connect(host="127.0.0.1", user="root", db="polytama_dev", port=3306)

# logger.info("[MYSQL]         :   SUCCESCFULLY CONNECTED to MYSQL")
cursor = mydb.cursor()
dockCode = 1
GetUidDock = "SELECT UID, POLICE_NO, STATUS FROM loading_dock WHERE ID = 1"
cursor.execute(GetUidDock)
GetUid = cursor.fetchone()
UidDb = GetUid[0]
PoliceNOHF = GetUid[1]
statusHFLD = GetUid[2]
logger.info(f'[HF RFID]       :   [QUERY] SELECT UID FROM DOCK {dockCode}')
logger.info(f'[HF RFID]       :   [QUERY] {UidDb}')

print(idErrorBook)

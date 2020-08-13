
import MySQLdb
mydb = MySQLdb.connect(host="127.0.0.1", user="root", db="polytama_dev", port=3306)

# logger.info("[MYSQL]         :   SUCCESCFULLY CONNECTED to MYSQL")
cursor = mydb.cursor()
try:
    errorBooking = "SELECT ID, URL FROM send_error WHERE SEND_STATUS = %s ORDER BY ID ASC LIMIT 1"
    cursor.execute(errorBooking, ["BOOKING"])
    valErrorBooking = cursor.fetchone()
    idErrorBook = valErrorBooking[0]
    urlErrorBook = valErrorBooking[1]
except:
    idErrorBook = 'OFF'
    urlErrorBook = 'OFF'


print(idErrorBook)

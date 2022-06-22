import mysql.connector
import time

while True:
    try:
        with mysql.connector.connect(
            host='db',
            user='estronnom',
            password='1234567890',
            port='3306'
        ) as conn:
            print(conn)
    except Exception as e:
        print(e)
    else:
        time.sleep(600)


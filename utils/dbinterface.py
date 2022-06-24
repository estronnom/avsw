import time
import mysql.connector


class Database:
    def __init__(self, **params):
        self.conn = self.__get_connection(params)

    def __get_connection(self, params):
        print('Trying to connect to database...')
        try:
            with mysql.connector.connect(**params) as conn:
                print('Database connection established')
                return conn
        except Exception as exc:
            print('Connection to database failed')
            print(exc)
            print('Waiting 3 seconds to retry')
            time.sleep(3)
            return self.__get_connection(params)

    def execute(self, query, params):
        pass

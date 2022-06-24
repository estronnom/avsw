import time
import mysql.connector


class Database:
    def __init__(self, **params):
        self.__params = params
        self.conn = self.__get_connection(self.__params)
        self.cur = self.conn.cursor()

    def __get_connection(self, params):
        print('Trying to connect to database...')
        try:
            conn = mysql.connector.connect(**params)
            print('Database connection established')
            return conn
        except Exception as exc:
            print('Connection to database failed')
            print(exc)
            print('Waiting 3 seconds to retry')
            time.sleep(3)
            return self.__get_connection(params)

    def execute(self, query, params=None, retry=False):
        print('Executing query...')
        print(query)
        try:
            self.cur.execute(
                query, params
            )
        except Exception as exc:
            self.conn.rollback()
            print('Query failed')
            print(query)
            print(exc)
            if not retry:
                print('Reestablishing connection...')
                self.__init__(**self.__params)
                print('Trying to execute query one more time')
                return self.execute(query, params, True)
        else:
            self.conn.commit()
            return tuple(self.cur)

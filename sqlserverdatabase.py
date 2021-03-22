import pyodbc
from config import Config

class Connection():
    HOST=None
    DATABASE=None
    USR=None
    PWD=None
    conn=None
    #DRIVER="{ODBC Driver 17 for SQL Server}"
    DRIVER="{ODBC Driver 17 for SQL Server}"
    #DRIVER="{SQL Server}"

    def __init__(self,host,db,usr,pwd):
        self.HOST=host
        self.DATABASE=db
        self.USR=usr
        self.PWD=pwd

        try:
            #print(f'DRIVER={self.DRIVER};SERVER={self.HOST};DATABASE={self.DATABASE};UID={self.USR};PWD={self.PWD}')
            cnx=pyodbc.connect(f'DRIVER={self.DRIVER};SERVER={self.HOST};DATABASE={self.DATABASE};UID={self.USR};PWD={self.PWD}')
            #print("SQL Connection done!")
            self.conn=cnx

        except Exception as err:
            print(err)

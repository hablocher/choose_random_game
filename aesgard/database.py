# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 00:29:48 2021

@author: Marcelo
"""
import pymssql  
import pymysql
import sqlite3 as sl
from aesgard.util import LogException
from pythonping import ping

SERVER    = ""
USER      = ""
PASSWORD  = ""
DATABASE  = ""
DBTYPE    = ""

sqlINSERT = """
              INSERT INTO GamesChoosed (gameFolder, timesPlayed, lastTimePlayed) VALUES ('{}', 1, CURRENT_TIMESTAMP)
            """
            
sqlSELECT = """
              SELECT * FROM GamesChoosed WHERE gameFolder = '{}' AND finished = 0 AND timesPlayed < (SELECT MAX(timesPlayed) FROM GamesChoosed)
            """

#sqlSELECT = """
#             SELECT TOP 1 * FROM GamesChoosed WHERE gameFolder = %s AND finished = 0 AND timesPlayed <= (SELECT MAX(timesPlayed) FROM GamesChoosed)ORDER BY NEWID()
#            """

sqlUPDATE = """
              UPDATE GamesChoosed SET timesPlayed = timesPlayed + 1 WHERE gameFolder = '{}'
            """

def insertGameInfo(choosedGame):
    global DBTYPE   
    try:
        if (not "sqlite" == DBTYPE):
            response = ping(SERVER)
            if (not response.success()):
                print("Database connection not available! Switching to sqlite!")            
                DBTYPE = "sqlite"
        conn = opencon()
        cursor = conn.cursor()
        if not findGameInfo(choosedGame):
            cursor.execute(sqlINSERT.format(choosedGame))  
        else:
            cursor.execute(sqlUPDATE.format(choosedGame))  
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        LogException("Database connection not available!", e)
        return    
    
def findGameInfo(choosedGame):
    global DBTYPE   
    try:
        if (not "sqlite" == DBTYPE):
            response = ping(SERVER)
            if (not response.success()):
                print("Database connection not available! Switching to sqlite!")            
                DBTYPE = "sqlite"
        conn = opencon()
        cursor = conn.cursor()
        cursor.execute(sqlSELECT.format(choosedGame))  
        cursor.fetchall()
        rowcount = cursor.rowcount
        cursor.close()
        conn.close()
        return rowcount==1
    except Exception as e:
        LogException("Database connection not available!", e)
        return False

def init(server, user, password, database, dbtype):
    global SERVER   
    global USER     
    global PASSWORD 
    global DATABASE 
    global DBTYPE   
    SERVER   = server
    USER     = user
    PASSWORD = password
    DATABASE = database
    DBTYPE   = dbtype    

def opencon():
    con = None
    if ("mysql"  == DBTYPE):
        con = pymysql.connect(host=SERVER,
                               user=USER,
                               password=PASSWORD,
                               database=DATABASE,
                               cursorclass=pymysql.cursors.DictCursor)

    if ("mssql"  == DBTYPE):
        con = pymssql.connect(server=SERVER, 
                               user=USER, 
                               password=PASSWORD, 
                               database=DATABASE)  

    if ("sqlite" == DBTYPE):
        con = sl.connect('Games.db')
        if (not tablesExists(con)):
            con.execute("""
                CREATE TABLE GamesChoosed (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    gameFolder TEXT,
                    timesPlayed INTEGER,
                    lastTimePlayed DATETIME,
                    finished INTEGER
                );
                """)
                
    return con

def tablesExists(con):
    cursor = con.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM GamesChoosed")
        return True
    except Exception:
        return False
    finally:
        cursor.close()

        
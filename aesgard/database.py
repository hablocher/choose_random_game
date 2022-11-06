# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 00:29:48 2021

@author: Marcelo
"""
import pymssql  
import pymysql
from aesgard.util import LogException
from pythonping import ping

SERVER    = ""
USER      = ""
PASSWORD  = ""
DATABASE  = ""
DBTYPE    = ""

sqlINSERT = """
              INSERT INTO GamesChoosed (gameFolder, timesPlayed, lastTimePlayed) VALUES (%s, 1, CURRENT_TIMESTAMP)
            """
            
sqlSELECT = """
              SELECT * FROM GamesChoosed WHERE gameFolder = %s AND finished = 0 AND timesPlayed < (SELECT MAX(timesPlayed) FROM GamesChoosed)
            """

#sqlSELECT = """
#             SELECT TOP 1 * FROM GamesChoosed WHERE gameFolder = %s AND finished = 0 AND timesPlayed <= (SELECT MAX(timesPlayed) FROM GamesChoosed)ORDER BY NEWID()
#            """

sqlUPDATE = """
              UPDATE GamesChoosed SET timesPlayed = timesPlayed + 1 WHERE gameFolder = %s
            """

def insertGameInfo(choosedGame):
    try:
        response = ping(SERVER)
        if (not response.success()):
            print("Database connection not available!")            
            return
        conn = opencon()
        cursor = conn.cursor()
        if not findGameInfo(choosedGame):
            cursor.execute(sqlINSERT, (choosedGame))  
        else:
            cursor.execute(sqlUPDATE, (choosedGame))  
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        LogException("Database connection not available!", e)
        return    
    
def findGameInfo(choosedGame):
    try:
        response = ping(SERVER)
        if (not response.success()):
            print("Database connection not available!")            
            return
        conn = opencon()
        cursor = conn.cursor()
        cursor.execute(sqlSELECT, (choosedGame))  
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
    return con

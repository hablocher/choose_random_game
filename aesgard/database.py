# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 00:29:48 2021

@author: Marcelo
"""
import pymssql  
import pymysql

SERVER    = ""
USER      = ""
PASSWORD  = ""
DATABASE  = ""
DBTYPE    = ""

sqlINSERT = """
              INSERT INTO GamesChoosed (gameFolder, timesPlayed, lastTimePlayed) VALUES (%s, 1, CURRENT_TIMESTAMP)
            """
            
sqlSELECT = """
              SELECT * FROM GamesChoosed WHERE gameFolder = %s AND finished = 0 AND timesPlayed <= (SELECT MAX(timesPlayed) FROM GamesChoosed)
            """

#sqlSELECT = """
#             SELECT TOP 1 * FROM GamesChoosed WHERE gameFolder = %s AND finished = 0 AND timesPlayed <= (SELECT MAX(timesPlayed) FROM GamesChoosed)ORDER BY NEWID()
#            """

sqlUPDATE = """
              UPDATE GamesChoosed SET timesPlayed = timesPlayed + 1 WHERE gameFolder = %s
            """

def insertGameInfo(choosedGame):
    conn = opencon()
    cursor = conn.cursor()
    if not findGameInfo(choosedGame):
        cursor.execute(sqlINSERT, (choosedGame))  
    else:
        cursor.execute(sqlUPDATE, (choosedGame))  
    conn.commit()
    cursor.close()
    conn.close()
    
    
def findGameInfo(choosedGame):
    conn = opencon()
    cursor = conn.cursor()
    cursor.execute(sqlSELECT, (choosedGame))  
    cursor.fetchall()
    rowcount = cursor.rowcount
    cursor.close()
    conn.close()
    return rowcount==1

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
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 00:29:48 2021

@author: Marcelo
"""
import pymssql 

sqlINSERT = """
              INSERT INTO GamesChoosed (gameFolder, timesPlayed, lastTimePlayed) VALUES (%s, 1, CURRENT_TIMESTAMP)
            """
            
sqlSELECT = """
              SELECT * FROM GamesChoosed WHERE gameFolder = %s AND finished = 0 AND timesPlayed <= (SELECT MAX(timesPlayed) FROM GamesChoosed)
            """

sqlUPDATE = """
              UPDATE GamesChoosed SET timesPlayed = timesPlayed + 1 WHERE gameFolder = %s
            """


def insertGameInfo(choosedGame):
    conn = pymssql.connect(server=__SERVER__, user=__USER__, password=__PASSWORD__, database=__DATABASE__)  
    cursor = conn.cursor()
    if not findGameInfo(choosedGame):
        cursor.execute(sqlINSERT, (choosedGame))  
    else:
        cursor.execute(sqlUPDATE, (choosedGame))  
    conn.commit()
    cursor.close()
    conn.close()
    
    
def findGameInfo(choosedGame):
    conn = pymssql.connect(server=__SERVER__, user=__USER__, password=__PASSWORD__, database=__DATABASE__)  
    cursor = conn.cursor()
    cursor.execute(sqlSELECT, (choosedGame))  
    cursor.fetchall()
    rowcount = cursor.rowcount
    cursor.close()
    conn.close()
    return rowcount==1

def init(server, user, password, database):
    global __SERVER__
    global __USER__
    global __PASSWORD__
    global __DATABASE__
    __SERVER__   = server
    __USER__     = user
    __PASSWORD__ = password
    __DATABASE__ = database
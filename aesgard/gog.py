# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 06:31:32 2023

@author: Marcelo
"""

import sqlite3

def getGOGGames(url):
    content = []
    _connection = sqlite3.connect(url)
    _cursor = _connection.cursor()

    _exception = None
    try:
        yield _cursor
    except Exception as e:
        _exception = e
        
	# Create a view of ProductPurchaseDates (= purchased/added games) joined on GamePieces for a full owned game data DB
    owned_game_database = """CREATE TEMP VIEW MasterList AS
            SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM ProductPurchaseDates
            JOIN GamePieces ON ProductPurchaseDates.gameReleaseKey = GamePieces.releaseKey;"""

	# Set up default queries and processing metadata, and always extract the game title along with any parameters
    positions = Positions({'releaseKey': 0, 'title': 1})
    fieldnames = ['title']
    og_fields = ["""CREATE TEMP VIEW MasterDB AS SELECT DISTINCT(MasterList.releaseKey) AS releaseKey, MasterList.value AS title, PLATFORMS.value AS platformList"""]
    og_references = [""" FROM MasterList, MasterList AS PLATFORMS"""]
    og_joins = []
    og_conditions = [""" WHERE MasterList.gamePieceTypeId={} AND PLATFORMS.releaseKey=MasterList.releaseKey AND PLATFORMS.gamePieceTypeId={}""".format(
                	id('title'),
				id('allGameReleases')
			)]
    og_order = """ ORDER BY title;"""
    og_resultFields = ['GROUP_CONCAT(DISTINCT MasterDB.releaseKey)', 'MasterDB.title']
    og_resultGroupBy = ['MasterDB.platformList']

    # Close the DB connection
    _cursor.close()
    _connection.close()

    	# Re-raise the unhandled exception if needed
    if _exception:
       raise _exception
        
    return content

class Positions(dict):
	""" small dictionary to avoid errors while parsing non-exported field positions """
	def __getitem__(self, key):
		try:
			return dict.__getitem__(self, key)
		except KeyError:
			return None

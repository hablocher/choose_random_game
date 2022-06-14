# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""

import json
import webbrowser

from urllib.request import urlopen

def get_steam_game_ids(steamOwnedGames):
    return {game['appid']: game['name'] for game in steamOwnedGames}

def getownedgames(url, apikey, steamid):
    url = (url.format(apikey, steamid))
    return json.loads(urlopen(url).read().decode())['response']['games']

def playgame(url, game):
    webbrowser.open(url.format(game['appid']))
    
def playgameid(url, id):
    webbrowser.open(url.format(id))

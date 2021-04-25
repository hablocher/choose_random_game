# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 18:56:44 2021

@author: Marcelo
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET
import json
import webbrowser

from urllib.request import urlopen

def get_steam_xml(url, username):
    xml_url = url.format(username)
    return urllib.request.urlopen(xml_url)

def get_steam_game_ids(url, username):
    tree = ET.parse(get_steam_xml(url, username))
    root = tree.getroot()
    if root.find('error') is not None:
        print(root.find('error').text)
        sys.exit(0)
    return {game.find('appID').text: game.find('name').text for game in root.iter('game')}

def getownedgames(url, apikey, steamid):
    url = (url.format(apikey, steamid))
    return json.loads(urlopen(url).read().decode())['response']['games']

def playgame(url, game):
    webbrowser.open(url.format(game['appid']))
    

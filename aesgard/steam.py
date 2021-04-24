import sys
import urllib.request
import xml.etree.ElementTree as ET
import json
import webbrowser
import configparser 

from urllib.request import urlopen

config = configparser.ConfigParser()

config.read('choose_random_game.ini')

def get_steam_xml(username):
    xml_url = config['STEAM']['gamesInfoURL'].format(
        username)
    return urllib.request.urlopen(xml_url)

def get_steam_game_ids(username):
    tree = ET.parse(get_steam_xml(username))
    root = tree.getroot()

    if root.find('error') is not None:
        print(root.find('error').text)
        sys.exit(0)

    return {game.find('appID').text: game.find('name').text for game in root.iter('game')}

def getownedgames(apikey, steamid):
    url = (config['STEAM']['ownedGamesURL'].format(apikey, steamid))

    return json.loads(urlopen(url).read().decode())['response']['games']

def playgame(game):
    webbrowser.open('steam://rungameid/{}'.format(game['appid']))
    

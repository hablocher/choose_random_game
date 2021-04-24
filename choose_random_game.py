import random
import os
import io
import sys
import jellyfish
import configparser 

from aesgard.steam import getownedgames
from aesgard.steam import get_steam_game_ids
from aesgard.steam import playgame
from aesgard.util  import normalizeString
from aesgard.util  import checkExeFile

def run():
    config = configparser.ConfigParser()
    config.read("choose_random_game.ini")
    
    content = []
    linksList = []

    apikey        = config['STEAM']['apikey']
    steamid       = config['STEAM']['steamid']
    steamUserName = config['STEAM']['username']

    steamGames = getownedgames(config['STEAM']['ownedGamesURL'], apikey, steamid)
    
    baseLink = config['CONFIG']['baseLinks']
    for key, link in config.items("FOLDERSWITHLINKS"):
        if baseLink:
            linksList = linksList + [s for s in next(os.walk(baseLink + link))[2]]
        else:
            linksList = linksList + [s for s in next(os.walk(link))[2]]
    
    for key, gameFolder in config.items("GAMEFOLDERS"):
        for key, common in config.items("GAMECOMMONFOLDERS"):
            folder = str(gameFolder) + str(common)
            if os.path.isdir(folder):
                for game in next(os.walk(folder))[1]:
                    if game not in linksList:
                        content = content + [folder + "/" + game]
    
    for key, steamFolder in config.items("STEAMFOLDERS"):
        if os.path.isdir(steamFolder):
            content = content + [steamFolder + "/"+ s for s in next(os.walk(steamFolder))[1]]
    
    for key, removal in config.items("REMOVALS"):
        linksList = [g.replace(removal, '') for g in linksList]
    
    content = list(set(content))
    content.sort()
    
    with io.open(config['FILES']['pathToSave'] + config['FILES']['gamesFoundFileName'], 'w+', encoding="utf-8") as filehandle:  
        for listitem in content:
            filehandle.write('%s\n' % listitem)
    		
    random.shuffle(content)
    
    choosedGame = random.choice(content)

    posLastBar = choosedGame.rfind("/")+1
    
    print("You have " + str(len(content)) + " games to play!")

    print("CHOOSED -----------> " + choosedGame + " <-----------")
    
    with open(config['FILES']['pathToSave'] + config['FILES']['gamesOwnedFileName'], 'w', encoding='utf-8') as f:
        for id, name in get_steam_game_ids(config['STEAM']['gamesInfoURL'], steamUserName).items():
            f.write("{},{}\n".format(id, name))
    
    for launch in next(os.walk(choosedGame))[2]:
        for key, prefix in config.items("LAUCHERPREFIXES"):
            if (launch.lower().startswith(prefix)): 
               print("Calling '" + launch + "'")
               os.chdir(choosedGame)
               os.startfile(launch)
               sys.exit() 
            
    for steamGame in steamGames:  
        name = normalizeString(steamGame['name'])
        choosed = normalizeString(choosedGame[posLastBar:])
        if (name == choosed  or jellyfish.levenshtein_distance(name, choosed) == 2):
           print("Calling STEAM app ID " + str(steamGame['appid']) + " (" + steamGame['name'] + ")")
           playgame(config['STEAM']['playGameURL'], steamGame)
           sys.exit() 
           
    if "DOSBOX" in choosedGame:
        os.startfile(config['CONFIG']['DOSBOXshortcut'])
        sys.exit() 
   
    exeCount = 0
    exeFolder = ""
    exeFile = ""
    for launch in next(os.walk(choosedGame))[2]:
        if launch.lower().endswith('.exe'):
            exeCount += 1
            exeFolder = choosedGame
            exeFile = launch
            if checkExeFile(launch.lower(), choosedGame[posLastBar:].lower()):
                print("Calling EXE '" + launch + "'")
                os.chdir(choosedGame)
                os.startfile(launch)
                sys.exit() 
               
    if (exeCount == 1):
        print("Calling EXE '" + exeFile + "'")
        os.chdir(exeFolder)
        os.startfile(exeFile)
        sys.exit() 
    
    print("Opening folder '" + choosedGame + "'")
    os.startfile(choosedGame)
    sys.exit() 
    #Mbox(str(len(content)) + ' jogos!!!! JOGUE UM ',  game , 0)

if __name__ == '__main__':
    run()

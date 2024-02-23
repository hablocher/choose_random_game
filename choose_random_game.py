import sys

from aesgard.steam     import getownedgames
from aesgard.steam     import get_steam_game_ids
from aesgard.gog       import getGOGGames
from aesgard.gameutil  import prepareContent
from aesgard.gameutil  import preparelinksList
from aesgard.gameutil  import chooseGame
from aesgard.util      import writeListToFile
from aesgard.util      import writeTupleToFile
from aesgard.util      import LogException
from aesgard.database  import init as databaseInit
from aesgard.ui        import showChoosedGame
from aesgard.config    import Config

def run(argv):
    conf = Config()
    conf.read_config(argv)
    
    try:
        databaseInit(conf.DatabaseServer, 
                     conf.DatabaseUser, 
                     conf.DatabasePassword, 
                     conf.DatabaseName, 
                     conf.DatabaseType)
    except Exception as e:
        LogException("Error initializing database!", e)
        return
    
    try:
        steamOwnedGames = getownedgames(conf.ownedGamesURL, conf.apikey, conf.steamid)
        steamGamesIds = get_steam_game_ids(steamOwnedGames).items();
    except Exception as e:
        LogException("Steam API not available!", e)
        steamOwnedGames = {}
        steamGamesIds = {}
        
    gogGames = getGOGGames(conf.GOGDatabase)
        
    linksList = preparelinksList(conf.foldersWithLinks, conf.baseLinks)
    
    # Create game list from all sources
    content = list(set(
        prepareContent(
            conf.gameFolders, 
            conf.gameCommonFolders, 
            conf.steamGameFolders, 
            linksList,
            steamGamesIds,
            conf.chooseNotInstalled,
            conf.removals,
            conf.endswith)
        ))    
    
    # Writing files    
    if conf.createFiles:
        writeListToFile(conf.pathToSave + conf.gamesFoundFileName, content)
        writeTupleToFile(conf.pathToSave + conf.steamGamesOwnedFileName, steamGamesIds)

    choosedGame = chooseGame(content)
        
    print("You have " + str(len(content)) + " games to play!")
    print("CHOOSED -----------> " + choosedGame + " <-----------")
    showChoosedGame(choosedGame, steamOwnedGames)

if __name__ == '__main__':
    run(sys.argv)

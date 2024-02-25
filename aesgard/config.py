# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 11:20:48 2024

@author: Marcelo
"""
from aesgard.util      import readConfigFile

class Config:
    
    def read_config(self, argv):
        self.config = readConfigFile(argv)

        self.apikey                  = self.config['STEAM']['apikey']
        self.steamid                 = self.config['STEAM']['steamid']
        self.ownedGamesURL           = self.config['STEAM']['ownedGamesURL']
        self.imageURL                = self.config['STEAM']['imageGameURL']
        self.playGameURL             = self.config['STEAM']['playGameURL']
        self.chooseNotInstalled      = self.config.getboolean('STEAM','chooseNotInstalled')
    
        self.baseLinks               = self.config['CONFIG']['baseLinks']
        self.onlyFavorites           = self.config['CONFIG']['onlyFavorites']
        self.shortcutExt             = self.config['CONFIG']['shortcutExt']
        self.importContentToDatabase = self.config.getboolean('CONFIG','importContentToDatabase')
    
        self.createFiles             = self.config.getboolean('FILES','createFiles')
        self.pathToSave              = self.config['FILES']['pathToSave']
        self.gamesFoundFileName      = self.config['FILES']['gamesFoundFileName']
        self.steamGamesOwnedFileName = self.config['FILES']['gamesOwnedFileName']
    
        self.gameFolders             = self.config.items("GAMEFOLDERS")
        self.foldersWithLinks        = self.config.items("FOLDERSWITHLINKS")
        self.gameCommonFolders       = self.config.items("GAMECOMMONFOLDERS")
        self.steamGameFolders        = self.config.items("STEAMGAMEFOLDERS")
        self.removals                = self.config.items("REMOVALS")
        self.endswith                = self.config.items("ENDSWITH")
        
        self.DatabaseServer          = self.config['DATABASE']['server']
        self.DatabaseUser            = self.config['DATABASE']['user']
        self.DatabasePassword        = self.config['DATABASE']['password']
        self.DatabaseName            = self.config['DATABASE']['name']
        self.DatabaseType            = self.config['DATABASE']['type']
        
        self.GOGDatabase             = self.config['GOG']['database']

        self.launcherPrefixes        = self.config.items("LAUNCHERPREFIXES")    
        self.otherClients            = self.config.items("OTHERCLIENTS")    

        self.DOSBOXLocation          = self.config['DOSBOX']['DOSBOXLocation']
        self.DOSBOXParameters        = self.config['DOSBOX']['DOSBOXParameters']
        self.DOSBOXExecutable        = self.config['DOSBOX']['DOSBOXExecutable']

        self.EXODOSLocation          = self.config['EXODOS']['EXODOSLocation']
        self.EXODOSImageURL          = self.config['EXODOS']['EXODOSImageURL']

        


# -*- coding: utf-8 -*-
"""
Configuration manager for Choose Random Game.
All parameters, paths, thresholds, and UI options are read from the .ini file.
"""
import os
from aesgard.util import readConfigFile

class Config:
    
    def read_config(self, argv):
        self.config = readConfigFile(argv)

        # -------------------------------------------------------------
        # [CONFIG] General Options
        # -------------------------------------------------------------
        self.baseLinks               = self.config.get('CONFIG', 'baseLinks', fallback='')
        self.shortcutExt             = self.config.get('CONFIG', 'shortcutExt', fallback='.lnk')
        self.includeDesktop          = self.config.getboolean('CONFIG', 'includeDesktop', fallback=True)
        self.desktopPath             = self.config.get('CONFIG', 'desktopPath', fallback=os.path.join(os.path.expanduser("~"), "Desktop"))
        self.onlyFavorites           = self.config.getboolean('CONFIG', 'onlyFavorites', fallback=False)
        self.importContentToDatabase = self.config.getboolean('CONFIG', 'importContentToDatabase', fallback=True)
        self.randomSampleSize        = self.config.getint('CONFIG', 'randomSampleSize', fallback=25)
        self.levenshteinMaxDistance  = self.config.getint('CONFIG', 'levenshteinMaxDistance', fallback=2)
        self.jaroWinklerThreshold    = self.config.getfloat('CONFIG', 'jaroWinklerThreshold', fallback=0.85)
        self.linkPrefix              = self.config.get('CONFIG', 'linkPrefix', fallback='link::')
        self.coversCacheDir          = self.config.get('CONFIG', 'coversCacheDir', fallback='covers_cache')
        self.fetchOnlineCovers       = self.config.getboolean('CONFIG', 'fetchOnlineCovers', fallback=True)
    
        # -------------------------------------------------------------
        # [FILES] Debug & Export Logs
        # -------------------------------------------------------------
        self.createFiles             = self.config.getboolean('FILES', 'createFiles', fallback=False)
        self.pathToSave              = self.config.get('FILES', 'pathToSave', fallback='')
        self.gamesFoundFileName      = self.config.get('FILES', 'gamesFoundFileName', fallback='GameFoldersFound.txt')
    
        # -------------------------------------------------------------
        # Directory Collections & Filters
        # -------------------------------------------------------------
        self.gameFolders             = self.config.items("GAMEFOLDERS") if self.config.has_section("GAMEFOLDERS") else []
        self.foldersWithLinks        = self.config.items("FOLDERSWITHLINKS") if self.config.has_section("FOLDERSWITHLINKS") else []
        self.gameCommonFolders       = self.config.items("GAMECOMMONFOLDERS") if self.config.has_section("GAMECOMMONFOLDERS") else []
        self.removals                = self.config.items("REMOVALS") if self.config.has_section("REMOVALS") else []
        self.endswith                = self.config.items("ENDSWITH") if self.config.has_section("ENDSWITH") else []
        
        # -------------------------------------------------------------
        # [DATABASE] Connection & Table
        # -------------------------------------------------------------
        self.DatabaseServer          = self.config.get('DATABASE', 'server', fallback='localhost')
        self.DatabaseUser            = self.config.get('DATABASE', 'user', fallback='sa')
        self.DatabasePassword        = self.config.get('DATABASE', 'password', fallback='')
        self.DatabaseName            = self.config.get('DATABASE', 'name', fallback='Games.db')
        self.DatabaseType            = self.config.get('DATABASE', 'type', fallback='sqlite')
        self.DatabaseTableName       = self.config.get('DATABASE', 'tableName', fallback='GamesChoosed')

        # -------------------------------------------------------------
        # [LAUNCHERPREFIXES] & [OTHERCLIENTS]
        # -------------------------------------------------------------
        self.launcherPrefixes        = self.config.items("LAUNCHERPREFIXES") if self.config.has_section("LAUNCHERPREFIXES") else []
        self.otherClients            = self.config.items("OTHERCLIENTS") if self.config.has_section("OTHERCLIENTS") else []

        # -------------------------------------------------------------
        # [DOSBOX]
        # -------------------------------------------------------------
        self.DOSBOXLocation          = self.config.get('DOSBOX', 'DOSBOXLocation', fallback='')
        self.DOSBOXParameters        = self.config.get('DOSBOX', 'DOSBOXParameters', fallback='-userconf -c {} -c _run.bat')
        self.DOSBOXExecutable        = self.config.get('DOSBOX', 'DOSBOXExecutable', fallback='DOSBox.exe')

        # -------------------------------------------------------------
        # [EXODOS]
        # -------------------------------------------------------------
        self.EXODOSLocation          = self.config.get('EXODOS', 'EXODOSLocation', fallback='')
        self.EXODOSImageURL          = self.config.get('EXODOS', 'EXODOSImageURL', fallback='')
        self.imageURL                = self.EXODOSImageURL
        self.EXODOSMetadataFolder    = self.config.get('EXODOS', 'metadataFolder', fallback='!dos')
        self.EXODOSInstallBat        = self.config.get('EXODOS', 'installBat', fallback='install.bat')
        self.EXODOSOnlyInstalled     = self.config.getboolean('EXODOS', 'onlyInstalled', fallback=True)
        self.exodosPrefix            = self.config.get('EXODOS', 'exodosPrefix', fallback='exodos:')

        # -------------------------------------------------------------
        # [PLAYNITE] Integration (Unifies Steam, GOG, Epic, etc.)
        # -------------------------------------------------------------
        self.playniteEnabled         = self.config.getboolean('PLAYNITE', 'enabled', fallback=True)
        self.playnitePath            = self.config.get('PLAYNITE', 'path', fallback='')
        self.playniteOnlyInstalled   = self.config.getboolean('PLAYNITE', 'onlyInstalled', fallback=True)
        self.playniteExportJson      = self.config.get('PLAYNITE', 'exportJson', fallback='playnite_games.json')
        self.playniteUriPrefix       = self.config.get('PLAYNITE', 'uriPrefix', fallback='playnite://playnite/start/')
        self.playniteLibraryFilesDir = self.config.get('PLAYNITE', 'libraryFilesDir', fallback='library/files')
        self.playnitePrefix          = self.config.get('PLAYNITE', 'playnitePrefix', fallback='playnite:')

        # -------------------------------------------------------------
        # [GOG] Integration & Cover Database
        # -------------------------------------------------------------
        self.gogEnabled              = self.config.getboolean('GOG', 'enabled', fallback=True)
        self.gogGalaxyDbPath         = self.config.get('GOG', 'galaxyDbPath', fallback='')

        # -------------------------------------------------------------
        # [STEAM] Integration & Cover Database
        # -------------------------------------------------------------
        self.steamEnabled            = self.config.getboolean('STEAM', 'enabled', fallback=True)
        self.steamPath               = self.config.get('STEAM', 'steamPath', fallback=r'C:\Program Files (x86)\Steam')

        # -------------------------------------------------------------
        # [UI] Dashboard & Display Settings
        # -------------------------------------------------------------
        self.uiWindowWidth           = self.config.getint('UI', 'windowWidth', fallback=1180)
        self.uiWindowHeight          = self.config.getint('UI', 'windowHeight', fallback=740)
        self.uiMinWidth              = self.config.getint('UI', 'minWidth', fallback=960)
        self.uiMinHeight             = self.config.getint('UI', 'minHeight', fallback=600)
        self.uiTableLimit            = self.config.getint('UI', 'tableLimit', fallback=400)
        self.uiCoverWidth            = self.config.getint('UI', 'coverWidth', fallback=160)
        self.uiCoverHeight           = self.config.getint('UI', 'coverHeight', fallback=160)

        # -------------------------------------------------------------
        # [STREAMER] YouTube Live & Stream Assistant Settings
        # -------------------------------------------------------------
        self.streamerRouletteEnabled       = self.config.getboolean('STREAMER', 'rouletteEnabled', fallback=True)
        self.streamerRouletteDurationMs    = self.config.getint('STREAMER', 'rouletteDurationMs', fallback=2600)
        self.streamerOverlayChromaKey      = self.config.get('STREAMER', 'overlayChromaKey', fallback='dark')
        self.streamerYouTubeMainChannel    = self.config.get('STREAMER', 'youtubeMainChannel', fallback='')
        self.streamerYouTubeLiveChannel    = self.config.get('STREAMER', 'youtubeLiveChannel', fallback='')
        self.streamerYouTubeChannel        = self.config.get('STREAMER', 'youtubeChannel', fallback=self.streamerYouTubeLiveChannel)

        # -------------------------------------------------------------
        # [THEME] Caninos Brancos Wilderness Visual Identity & Backgrounds
        # -------------------------------------------------------------
        self.themeBackgroundImage          = self.config.get('THEME', 'backgroundImage', fallback='assets/backgrounds/caninos_brancos_lpm.png')
        self.themeBackgroundOpacity        = self.config.getfloat('THEME', 'backgroundOpacity', fallback=0.22)
        self.themeSounds                   = self.config.getboolean('THEME', 'themeSounds', fallback=True)

    def save_theme_setting(self, background_path: str = None, opacity: float = None, theme_sounds: bool = None):
        """Saves updated background image, opacity, and sound theme to choose_random_game.ini."""
        import configparser
        ini_path = "choose_random_game.ini"
        if not os.path.exists(ini_path):
            return
        try:
            parser = configparser.ConfigParser()
            parser.read(ini_path, encoding='utf-8')
            if not parser.has_section("THEME"):
                parser.add_section("THEME")
            if background_path is not None:
                parser.set("THEME", "backgroundImage", str(background_path))
                self.themeBackgroundImage = str(background_path)
            if opacity is not None:
                parser.set("THEME", "backgroundOpacity", f"{opacity:.2f}")
                self.themeBackgroundOpacity = float(opacity)
            if theme_sounds is not None:
                parser.set("THEME", "themeSounds", "True" if theme_sounds else "False")
                self.themeSounds = bool(theme_sounds)
            with open(ini_path, 'w', encoding='utf-8') as f:
                parser.write(f)
        except Exception as e:
            pass

    def save_all_settings(self, settings: dict) -> bool:
        """
        Saves a dictionary of {section: {key: value}} into choose_random_game.ini
        and reloads configuration into memory.
        """
        import configparser
        ini_path = "choose_random_game.ini"
        if not os.path.exists(ini_path):
            return False
        try:
            parser = configparser.ConfigParser()
            parser.read(ini_path, encoding='utf-8')
            for section, kvs in settings.items():
                if not parser.has_section(section):
                    parser.add_section(section)
                for k, v in kvs.items():
                    parser.set(section, k, str(v))
            with open(ini_path, 'w', encoding='utf-8') as f:
                parser.write(f)
            self.read_config([])
            return True
        except Exception as e:
            return False



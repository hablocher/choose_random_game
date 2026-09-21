# -*- coding: utf-8 -*-
"""
Database persistence module for Choose Random Game.
Supports SQLite, MySQL, and Microsoft SQL Server with parameterized queries.
"""
import logging
import sqlite3 as sl

logger = logging.getLogger(__name__)

SERVER = ""
USER = ""
PASSWORD = ""
DATABASE = ""
DBTYPE = "sqlite"
TABLE_NAME = "GamesChoosed"

FIELD_ID = 0
FIELD_GAMENAME = 1
FIELD_TIMESPLAYED = 2
FIELD_LASTTIMEPLAYED = 3
FIELD_FINISHED = 4
FIELD_FAVORITE = 5

def init(server, user, password, database, dbtype, table_name="GamesChoosed"):
    global SERVER, USER, PASSWORD, DATABASE, DBTYPE, TABLE_NAME
    SERVER = server or ""
    USER = user or ""
    PASSWORD = password or ""
    DATABASE = database or "Games.db"
    DBTYPE = (dbtype or "sqlite").lower()
    # Sanitize table name to alphanumeric/underscore
    cleaned_table = "".join(c for c in (table_name or "GamesChoosed") if c.isalnum() or c == "_")
    TABLE_NAME = cleaned_table or "GamesChoosed"

def opencon():
    """Opens a database connection according to the configured DBTYPE."""
    if "mysql" == DBTYPE:
        import pymysql
        return pymysql.connect(
            host=SERVER,
            user=USER,
            password=PASSWORD,
            database=DATABASE,
            autocommit=True
        )

    if "mssql" == DBTYPE:
        import pymssql
        return pymssql.connect(
            server=SERVER,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )

    # Default to sqlite
    conn = sl.connect(DATABASE if DATABASE.endswith(".db") else "Games.db")
    if not tablesExists(conn):
        with conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    gameName TEXT UNIQUE,
                    timesPlayed INTEGER DEFAULT 0,
                    lastTimePlayed DATETIME,
                    finished INTEGER DEFAULT 0,
                    favorite INTEGER DEFAULT 0
                );
            """)
            conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_gameName ON {TABLE_NAME}(LOWER(gameName));")
    else:
        ensureDatabaseIntegrity(conn)
    return conn

def ensureDatabaseIntegrity(conn):
    """
    Consolidates any historical duplicates in the database and ensures 
    a UNIQUE index on gameName so that duplicates can never occur again.
    """
    if DBTYPE != "sqlite":
        return
    try:
        cursor = conn.cursor()
        # 1. Check if duplicate records exist
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM (
                SELECT LOWER(gameName) 
                FROM {TABLE_NAME} 
                GROUP BY LOWER(gameName) 
                HAVING COUNT(*) > 1
            )
        """)
        has_dups = cursor.fetchone()[0] > 0

        if has_dups:
            logger.info(f"Consolidating duplicate records in {TABLE_NAME}...")
            # Update winner records with max stats
            cursor.execute(f"""
                UPDATE {TABLE_NAME}
                SET timesPlayed = sub.max_played,
                    lastTimePlayed = sub.max_last,
                    favorite = sub.max_fav,
                    finished = sub.max_fin
                FROM (
                    SELECT LOWER(gameName) as l_name,
                           MAX(timesPlayed) as max_played,
                           MAX(lastTimePlayed) as max_last,
                           MAX(favorite) as max_fav,
                           MAX(finished) as max_fin
                    FROM {TABLE_NAME}
                    GROUP BY LOWER(gameName)
                ) sub
                WHERE LOWER({TABLE_NAME}.gameName) = sub.l_name
            """)
            # Delete duplicate rows, keeping only one primary row per gameName
            cursor.execute(f"""
                DELETE FROM {TABLE_NAME}
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM {TABLE_NAME}
                    GROUP BY LOWER(gameName)
                )
            """)
            conn.commit()
            logger.info("Successfully consolidated historical duplicates.")

        # 2. Ensure unique index on LOWER(gameName)
        cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_gameName ON {TABLE_NAME}(LOWER(gameName));")
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.warning(f"Database integrity check warning: {e}")

def tablesExists(con):
    cursor = con.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        return True
    except Exception:
        return False
    finally:
        cursor.close()

def _get_placeholder():
    """Returns parameter placeholder based on DBTYPE (? for SQLite, %s for MySQL/MSSQL)."""
    return "%s" if DBTYPE in ("mysql", "mssql") else "?"

def findGameInfo(choosedGame):
    """
    Finds a game row in the database.
    Returns the row dictionary/tuple or None.
    """
    ph = _get_placeholder()
    sql = f"SELECT id, gameName, timesPlayed, lastTimePlayed, finished, favorite FROM {TABLE_NAME} WHERE gameName = {ph}"
    conn = None
    try:
        conn = opencon()
        cursor = conn.cursor()
        cursor.execute(sql, (choosedGame,))
        row = cursor.fetchone()
        cursor.close()
        return row
    except Exception as e:
        logger.error(f"Error querying game info: {e}")
        return None
    finally:
        if conn:
            conn.close()

def insertGameInfo(choosedGame):
    """
    Inserts or updates play count and last played timestamp for the chosen game.
    """
    ph = _get_placeholder()
    conn = None
    try:
        conn = opencon()
        cursor = conn.cursor()
        
        # Check if already exists
        row = findGameInfo(choosedGame)
        if row is None:
            if DBTYPE == "sqlite":
                insert_sql = f"INSERT OR IGNORE INTO {TABLE_NAME} (gameName, timesPlayed, finished, lastTimePlayed, favorite) VALUES (?, 1, 0, CURRENT_TIMESTAMP, 0)"
                cursor.execute(insert_sql, (choosedGame,))
            else:
                insert_sql = f"INSERT INTO {TABLE_NAME} (gameName, timesPlayed, finished, lastTimePlayed, favorite) VALUES ({ph}, 1, 0, CURRENT_TIMESTAMP, 0)"
                cursor.execute(insert_sql, (choosedGame,))
        else:
            update_sql = f"UPDATE {TABLE_NAME} SET timesPlayed = timesPlayed + 1, lastTimePlayed = CURRENT_TIMESTAMP WHERE gameName = {ph}"
            cursor.execute(update_sql, (choosedGame,))
            
        if hasattr(conn, 'commit'):
            conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error updating game info in database: {e}")
    finally:
        if conn:
            conn.close()

def setFinished(choosedGame, finished=1):
    """Sets the finished (completed) flag for a game."""
    ph = _get_placeholder()
    sql = f"UPDATE {TABLE_NAME} SET finished = {ph} WHERE gameName = {ph}"
    conn = None
    try:
        conn = opencon()
        cursor = conn.cursor()
        cursor.execute(sql, (finished, choosedGame))
        if cursor.rowcount == 0:
            insert_sql = f"INSERT INTO {TABLE_NAME} (gameName, timesPlayed, finished, lastTimePlayed, favorite) VALUES ({ph}, 0, {ph}, NULL, 0)"
            cursor.execute(insert_sql, (choosedGame, finished))
        if hasattr(conn, 'commit'):
            conn.commit()
        cursor.close()
        logger.info(f"Marked game '{choosedGame}' finished={finished}")
    except Exception as e:
        logger.error(f"Error updating finished status: {e}")
    finally:
        if conn:
            conn.close()

def setFavorite(choosedGame, favorite=1):
    """Sets the favorite flag for a game."""
    ph = _get_placeholder()
    sql = f"UPDATE {TABLE_NAME} SET favorite = {ph} WHERE gameName = {ph}"
    conn = None
    try:
        conn = opencon()
        cursor = conn.cursor()
        cursor.execute(sql, (favorite, choosedGame))
        if cursor.rowcount == 0:
            insert_sql = f"INSERT INTO {TABLE_NAME} (gameName, timesPlayed, finished, lastTimePlayed, favorite) VALUES ({ph}, 0, 0, NULL, {ph})"
            cursor.execute(insert_sql, (choosedGame, favorite))
        if hasattr(conn, 'commit'):
            conn.commit()
        cursor.close()
        logger.info(f"Marked game '{choosedGame}' favorite={favorite}")
    except Exception as e:
        logger.error(f"Error updating favorite status: {e}")
    finally:
        if conn:
            conn.close()

def importContentToDatabase(content):
    """
    Efficiently batch-imports a list of games into the database.
    """
    if not content:
        return
        
    ph = _get_placeholder()
    conn = None
    try:
        conn = opencon()
        cursor = conn.cursor()
        
        if DBTYPE == "sqlite":
            sql = f"INSERT OR IGNORE INTO {TABLE_NAME} (gameName, timesPlayed, finished, lastTimePlayed, favorite) VALUES (?, 0, 0, NULL, 0)"
            cursor.executemany(sql, [(g,) for g in content])
        else:
            for game in content:
                check_sql = f"SELECT id FROM {TABLE_NAME} WHERE gameName = {ph}"
                cursor.execute(check_sql, (game,))
                if cursor.fetchone() is None:
                    ins_sql = f"INSERT INTO {TABLE_NAME} (gameName, timesPlayed, finished, lastTimePlayed, favorite) VALUES ({ph}, 0, 0, NULL, 0)"
                    cursor.execute(ins_sql, (game,))
                    
        if hasattr(conn, 'commit'):
            conn.commit()
        cursor.close()
        logger.info(f"Batch imported {len(content)} games into database.")
    except Exception as e:
        if conn and hasattr(conn, 'rollback'):
            conn.rollback()
        logger.error(f"Error in importContentToDatabase: {e}")
    finally:
        if conn:
            conn.close()

def getDatabaseStats():
    """
    Returns aggregated statistics from database:
    total_games, total_played, finished_count, favorite_count, unplayed_count
    """
    stats = {
        "total_games": 0,
        "total_played": 0,
        "finished_count": 0,
        "favorite_count": 0,
        "unplayed_count": 0,
        "completion_rate": 0.0
    }
    conn = None
    try:
        conn = opencon()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*), COALESCE(SUM(timesPlayed), 0) FROM {TABLE_NAME}")
        row = cursor.fetchone()
        if row:
            stats["total_games"] = row[0] or 0
            stats["total_played"] = row[1] or 0

        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE finished = 1")
        row = cursor.fetchone()
        if row:
            stats["finished_count"] = row[0] or 0

        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE favorite = 1")
        row = cursor.fetchone()
        if row:
            stats["favorite_count"] = row[0] or 0

        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE timesPlayed = 0")
        row = cursor.fetchone()
        if row:
            stats["unplayed_count"] = row[0] or 0

        if stats["total_games"] > 0:
            stats["completion_rate"] = round((stats["finished_count"] / stats["total_games"]) * 100, 1)

        cursor.close()
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
    finally:
        if conn:
            conn.close()
    return stats

def getGamesList(searchQuery="", statusFilter="all", limit=1000, offset=0, filterText=None):
    """
    Retrieves filtered games from database.
    statusFilter: 'all', 'unplayed', 'played', 'finished', 'favorite'
    """
    if filterText is not None:
        searchQuery = filterText
    ph = _get_placeholder()
    conditions = []
    params = []

    if searchQuery and searchQuery.strip():
        conditions.append(f"gameName LIKE {ph}")
        params.append(f"%{searchQuery.strip()}%")

    # Normalize statusFilter to handle both internal keys and UI strings (English/Portuguese)
    sf = (statusFilter or "all").strip().lower()
    if sf in ("unplayed", "não jogados", "nao jogados", "nao_jogados"):
        conditions.append("timesPlayed = 0")
    elif sf in ("played", "jogados"):
        conditions.append("timesPlayed > 0")
    elif sf in ("finished", "zerados", "zerado"):
        conditions.append("finished = 1")
    elif sf in ("favorite", "favorites", "favoritos", "favorito", "⭐ favoritos"):
        conditions.append("favorite = 1")

    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT id, gameName, timesPlayed, lastTimePlayed, finished, favorite
        FROM {TABLE_NAME}
        {where_clause}
        ORDER BY favorite DESC, timesPlayed ASC, gameName ASC
        LIMIT {limit} OFFSET {offset}
    """

    conn = None
    results = []
    try:
        conn = opencon()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        cursor.close()
    except Exception as e:
        logger.error(f"Error querying games list: {e}")
    finally:
        if conn:
            conn.close()
    return results

def cleanOrphanGames(con, config, check_installed_func=None, progress_callback=None):
    """
    Cleans up orphan game records from the database table.
    Calls check_installed_func(game_name) -> (is_installed, folder_not_empty, warning_message)
    Returns:
        dict with keys: 'total_checked', 'removed_count', 'warnings_not_empty'
    """
    summary = {
        "total_checked": 0,
        "removed_count": 0,
        "warnings_not_empty": []
    }
    
    conn = con if con is not None else opencon()
    should_close = con is None

    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, gameName FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        total_rows = len(rows)
        summary["total_checked"] = total_rows

        ids_to_remove = []
        for idx, row in enumerate(rows):
            record_id, game_name = row[0], row[1]
            try:
                is_installed, folder_not_empty, warning_msg = check_installed_func(game_name)
                if not is_installed:
                    ids_to_remove.append(record_id)
                    if folder_not_empty and warning_msg:
                        summary["warnings_not_empty"].append(warning_msg)
            except Exception as ex:
                logger.warning(f"Error checking status of '{game_name}': {ex}")

            if progress_callback and (idx % 200 == 0 or idx == total_rows - 1):
                progress_callback(idx + 1, total_rows)

        # Delete orphan records in batches
        if ids_to_remove:
            ph = _get_placeholder()
            batch_size = 500
            for i in range(0, len(ids_to_remove), batch_size):
                batch = ids_to_remove[i:i + batch_size]
                placeholders = ",".join([ph] * len(batch))
                del_sql = f"DELETE FROM {TABLE_NAME} WHERE id IN ({placeholders})"
                cursor.execute(del_sql, tuple(batch))
            
            if hasattr(conn, 'commit'):
                conn.commit()

        summary["removed_count"] = len(ids_to_remove)
        cursor.close()
        logger.info(f"Cleaned {summary['removed_count']} orphan games from database.")
    except Exception as e:
        if conn and hasattr(conn, 'rollback'):
            conn.rollback()
        logger.error(f"Error cleaning orphan games from database: {e}")
    finally:
        if should_close and conn:
            conn.close()
            
    return summary

def syncGotyGames(userGamesList=None):
    """Initializes and syncs the GotyGames table with current installed games."""
    from aesgard.goty import initGotyDatabase
    conn = None
    try:
        conn = opencon()
        initGotyDatabase(conn, userGamesList=userGamesList)
    except Exception as e:
        logger.error(f"Error syncing GOTY games: {e}")
    finally:
        if conn:
            conn.close()

def getRandomGoty():
    """Gets a random Game of the Year from the database."""
    from aesgard.goty import getRandomGoty as fetchRandomGoty
    conn = None
    try:
        conn = opencon()
        return fetchRandomGoty(conn)
    except Exception as e:
        logger.error(f"Error fetching random GOTY: {e}")
        return None
    finally:
        if conn:
            conn.close()

def getAllGotys():
    """Gets all Game of the Year entries from the database."""
    from aesgard.goty import getAllGotys as fetchAllGotys
    conn = None
    try:
        conn = opencon()
        return fetchAllGotys(conn)
    except Exception as e:
        logger.error(f"Error fetching all GOTYs: {e}")
        return []
    finally:
        if conn:
            conn.close()


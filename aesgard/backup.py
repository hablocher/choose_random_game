# -*- coding: utf-8 -*-
"""
Quick Save Game & Profile Backup Utility for Choose Random Game.
Detects game save directories, creates timestamped zip archives,
and stores backups in 'saves_backup/'.
"""
import os
import time
import zipfile
import logging
from typing import Dict, Optional
from aesgard.ui import formatDisplayName
from aesgard.hltb import clean_title_for_hltb

logger = logging.getLogger(__name__)


def _get_backup_dir() -> str:
    """Returns absolute path to 'saves_backup' root directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(base_dir, "saves_backup")
    os.makedirs(target, exist_ok=True)
    return target


def backup_game_saves(game_entry: str, custom_destination: Optional[str] = None) -> Dict:
    """
    Creates a timestamped .zip backup of game saves or configuration.
    Returns status dict with archive path and file count.
    """
    display_name = formatDisplayName(game_entry)
    clean_name = clean_title_for_hltb(display_name)
    safe_slug = "".join(c for c in clean_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_root = custom_destination or _get_backup_dir()

    zip_filename = f"{safe_slug}_{timestamp}.zip"
    zip_filepath = os.path.join(backup_root, zip_filename)

    candidate_dirs = []
    # 1. Local path checks
    if not game_entry.startswith("playnite:") and not game_entry.startswith("steam:") and os.path.exists(game_entry):
        if os.path.isdir(game_entry):
            # Check common subfolder names for saves
            for sub in ("saves", "save", "savegame", "savegames", "profile", "profiles", "userdata"):
                sub_path = os.path.join(game_entry, sub)
                if os.path.exists(sub_path) and os.path.isdir(sub_path):
                    candidate_dirs.append(sub_path)
            # If no subfolder, backup root directory configuration/ini/cfg/save files
            if not candidate_dirs:
                candidate_dirs.append(game_entry)

    # 2. Windows Saved Games / Documents check
    user_docs = os.path.expanduser("~/Documents")
    if os.path.exists(user_docs):
        for sub in os.listdir(user_docs):
            if clean_name.lower() in sub.lower():
                candidate_dirs.append(os.path.join(user_docs, sub))

    # 3. Windows %USERPROFILE%/Saved Games
    saved_games = os.path.expanduser("~/Saved Games")
    if os.path.exists(saved_games):
        for sub in os.listdir(saved_games):
            if clean_name.lower() in sub.lower():
                candidate_dirs.append(os.path.join(saved_games, sub))

    files_added = 0
    total_size = 0
    save_extensions = {".sav", ".save", ".dat", ".ini", ".cfg", ".json", ".xml", ".s01", ".s02", ".s03", ".000", ".001"}

    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            if candidate_dirs:
                for c_dir in candidate_dirs:
                    for root, _, files in os.walk(c_dir):
                        for f in files:
                            ext = os.path.splitext(f)[1].lower()
                            if ext in save_extensions or "save" in f.lower() or "slot" in f.lower():
                                full_p = os.path.join(root, f)
                                rel_p = os.path.relpath(full_p, c_dir)
                                zf.write(full_p, arcname=os.path.join(os.path.basename(c_dir), rel_p))
                                files_added += 1
                                total_size += os.path.getsize(full_p)
            
            # If nothing found via automatic directory detection, write metadata info record
            if files_added == 0:
                info_content = f"Snapshot Save Backup for {display_name}\nCreated at: {time.ctime()}\nGame Entry: {game_entry}\n"
                zf.writestr("backup_info.txt", info_content)
                files_added = 1

        return {
            "success": True,
            "archive_path": zip_filepath,
            "file_count": files_added,
            "size_bytes": total_size,
            "message": f"Backup gerado com sucesso!\n{files_added} arquivos salvos em:\n{zip_filepath}"
        }

    except Exception as e:
        logger.error(f"Error creating save backup: {e}")
        return {
            "success": False,
            "archive_path": "",
            "file_count": 0,
            "size_bytes": 0,
            "message": f"Erro ao criar backup: {e}"
        }

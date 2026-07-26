# hetsi/core/diskinfo.py
"""Tailles de dossiers, espace disque et liste des lecteurs."""
import ctypes
import os
import shutil
import stat
import string

DRIVE_FIXED = 3


def _est_point_reparse(chemin):
    """Vrai si `chemin` est un point de reparse (jonction ou lien symbolique)."""
    try:
        infos = os.stat(chemin, follow_symlinks=False)
    except OSError:
        return False
    attributs = getattr(infos, "st_file_attributes", 0)
    return bool(attributs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def taille_dossier(chemin):
    """Somme récursive des tailles de fichiers (octets). Ne suit pas les jonctions."""
    total = 0
    for racine, dirs, fichiers in os.walk(chemin):
        # Ne pas descendre dans les points de reparse (jonctions/symlinks)
        dirs[:] = [d for d in dirs if not _est_point_reparse(os.path.join(racine, d))]
        fichiers = [f for f in fichiers if not _est_point_reparse(os.path.join(racine, f))]
        for f in fichiers:
            chemin_f = os.path.join(racine, f)
            try:
                total += os.path.getsize(chemin_f)
            except OSError:
                pass
    return total


def espace_libre(lecteur):
    """Octets libres sur le lecteur contenant `lecteur`."""
    return shutil.disk_usage(lecteur).free


def lettre_lecteur(chemin):
    """Racine du lecteur d'un chemin, ex. 'C:\\Program Files' -> 'C:\\'."""
    lecteur = os.path.splitdrive(os.path.abspath(chemin))[0]
    return lecteur + "\\"


def lecteurs_disponibles():
    """Racines des lecteurs fixes prêts à l'emploi."""
    trouves = []
    for lettre in string.ascii_uppercase:
        racine = f"{lettre}:\\"
        if os.path.exists(racine) and ctypes.windll.kernel32.GetDriveTypeW(racine) == DRIVE_FIXED:
            trouves.append(racine)
    return trouves

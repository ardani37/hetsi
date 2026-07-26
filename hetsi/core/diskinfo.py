# hetsi/core/diskinfo.py
"""Tailles de dossiers, espace disque et liste des lecteurs."""
import os
import shutil
import string


def taille_dossier(chemin):
    """Somme récursive des tailles de fichiers (octets). Ne suit pas les jonctions."""
    total = 0
    for racine, dirs, fichiers in os.walk(chemin):
        # Ne pas descendre dans les points de reparse (jonctions/symlinks)
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(racine, d))]
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
        if os.path.exists(racine):
            trouves.append(racine)
    return trouves

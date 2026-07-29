"""Élévation administrateur et chemin des données applicatives."""
import ctypes
import os
import sys


def est_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relancer_en_admin():
    """Relance le processus courant élevé. Renvoie True si relancé (quitter alors)."""
    if est_admin():
        return False
    if getattr(sys, "frozen", False):
        # .exe autonome : relancer l'exe lui-même, sans arguments
        cible, params = sys.executable, ""
        dossier = None
    else:
        # Lancé en module : relancer `python -m hetsi.run` depuis la racine projet
        import hetsi
        cible, params = sys.executable, "-m hetsi.run"
        dossier = os.path.dirname(os.path.dirname(os.path.abspath(hetsi.__file__)))
    ctypes.windll.shell32.ShellExecuteW(None, "runas", cible, params, dossier, 1)
    return True


def _dossier_appdata():
    """Dossier %APPDATA%\\hetsi (créé si absent)."""
    base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "hetsi")
    os.makedirs(base, exist_ok=True)
    return base


def chemin_donnees():
    """%APPDATA%\\hetsi\\history.json (dossier créé si absent)."""
    return os.path.join(_dossier_appdata(), "history.json")


def chemin_log():
    """%APPDATA%\\hetsi\\hetsi.log (dossier créé si absent)."""
    return os.path.join(_dossier_appdata(), "hetsi.log")

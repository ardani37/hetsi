# hetsi/core/risques.py
"""Analyse de risque avant un déplacement."""
import ctypes
import json
import os
from dataclasses import dataclass

from hetsi.core import diskinfo
from hetsi.core.processus import _powershell

DRIVE_REMOVABLE = 2
DRIVE_REMOTE = 4

_RACINES_PROGRAMMES = ("c:\\program files", "c:\\program files (x86)")


@dataclass
class Risque:
    niveau: str
    code: str
    message: str


def _type_lecteur(racine):
    """Code GetDriveTypeW du lecteur (2 amovible, 3 fixe, 4 réseau)."""
    try:
        return int(ctypes.windll.kernel32.GetDriveTypeW(racine))
    except Exception:
        return 0


def _services_du_dossier(dossier):
    """Noms des services Windows dont l'exécutable est dans `dossier`."""
    motif = dossier.rstrip("\\").replace("'", "''") + "\\*"
    script = (
        "Get-CimInstance Win32_Service | Where-Object { $_.PathName -like '*" + motif + "*' } "
        "| Select-Object Name | ConvertTo-Json -Compress"
    )
    sortie = (_powershell(script) or "").strip()
    if not sortie:
        return []
    try:
        donnees = json.loads(sortie)
    except ValueError:
        return []
    if isinstance(donnees, dict):
        donnees = [donnees]
    noms = []
    for item in donnees:
        if isinstance(item, dict) and item.get("Name"):
            noms.append(str(item["Name"]))
    return noms


def _est_dossier_systeme(source):
    chemin = os.path.normpath(source).rstrip("\\").lower()
    racine_lecteur = os.path.splitdrive(chemin)[0]
    if chemin == racine_lecteur:  # racine nue : "c:" après normalisation
        return True
    dossier_windows = os.environ.get("SystemRoot", "C:\\Windows").rstrip("\\").lower()
    if chemin == dossier_windows or chemin.startswith(dossier_windows + "\\"):
        return True
    if chemin in _RACINES_PROGRAMMES:
        return True
    return False


def analyser(source, destination):
    """Liste les risques du déplacement `source` -> `destination`."""
    trouves = []

    if _est_dossier_systeme(source):
        trouves.append(Risque(
            niveau="bloquant", code="dossier_systeme",
            message="Ce dossier fait partie de Windows : le déplacer rendrait "
                    "le système instable.",
        ))
        return trouves  # inutile d'analyser plus loin, le déplacement est refusé

    type_cible = _type_lecteur(diskinfo.lettre_lecteur(destination))
    if type_cible == DRIVE_REMOVABLE:
        trouves.append(Risque(
            niveau="eleve", code="cible_amovible",
            message="Le disque cible est amovible : si tu le débranches, "
                    "le logiciel ne démarrera plus.",
        ))
    elif type_cible == DRIVE_REMOTE:
        trouves.append(Risque(
            niveau="eleve", code="cible_amovible",
            message="Le disque cible est un lecteur réseau : le logiciel ne "
                    "démarrera plus si le réseau est indisponible.",
        ))

    for nom in _services_du_dossier(source):
        trouves.append(Risque(
            niveau="eleve", code="service_windows",
            message=f"Un service Windows ({nom}) utilise ce dossier : il "
                    "pourrait ne pas redémarrer correctement.",
        ))

    if diskinfo.lettre_lecteur(source).lower() == diskinfo.lettre_lecteur(destination).lower():
        trouves.append(Risque(
            niveau="moyen", code="meme_disque",
            message="Source et cible sont sur le même disque : ce déplacement "
                    "ne libérera aucun espace.",
        ))

    return trouves

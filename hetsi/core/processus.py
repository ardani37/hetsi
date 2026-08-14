"""Détection et fermeture des programmes lancés depuis un dossier."""
import json
import subprocess
import time
from dataclasses import dataclass


@dataclass
class Processus:
    pid: int
    nom: str
    chemin: str


def _powershell(script):
    """Exécute un script PowerShell, renvoie sa sortie standard (vide si échec)."""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, encoding="oem", errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def _charger_json(sortie):
    """PowerShell renvoie un objet seul ou une liste : normaliser en liste."""
    sortie = (sortie or "").strip()
    if not sortie:
        return []
    try:
        donnees = json.loads(sortie)
    except ValueError:
        return []
    if isinstance(donnees, dict):
        return [donnees]
    if isinstance(donnees, list):
        return donnees
    return []


def processus_du_dossier(dossier):
    """Programmes dont l'exécutable se trouve dans `dossier` (récursivement)."""
    motif_ps = (dossier.rstrip("\\")
                .replace("'", "''")
                .replace("[", "`[")
                .replace("]", "`]")) + "\\*"
    script = (
        "Get-Process | Where-Object { $_.Path -like '" + motif_ps + "' } "
        "| Select-Object Id,ProcessName,Path | ConvertTo-Json -Compress"
    )
    trouves = []
    for item in _charger_json(_powershell(script)):
        try:
            trouves.append(Processus(
                pid=int(item["Id"]),
                nom=str(item.get("ProcessName", "")),
                chemin=str(item.get("Path", "")),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    return trouves


def _existe(pid):
    """True si le processus tourne. En cas d'échec de vérification, on suppose
    qu'il tourne encore : mieux vaut un faux « toujours là » qu'un faux « fermé »."""
    sortie = _powershell(
        f"if (Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue) "
        "{ 'oui' } else { 'non' }"
    )
    if "oui" in sortie:
        return True
    if "non" in sortie:
        return False
    return True  # vérification impossible : prudence


def fermer(pid, force=False, attente=3.0):
    """Ferme le processus `pid`. Renvoie True s'il a disparu avant `attente`."""
    pid = int(pid)
    if force:
        _powershell(f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue")
    else:
        _powershell(
            f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
            "if ($p) { $null = $p.CloseMainWindow() }"
        )
    limite = time.monotonic() + attente
    while time.monotonic() < limite:
        if not _existe(pid):
            return True
        time.sleep(0.25)
    return not _existe(pid)

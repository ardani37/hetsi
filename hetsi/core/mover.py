# hetsi/core/mover.py
"""Cœur : détection de jonction et copie robocopy."""
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass

from hetsi.core import diskinfo


@dataclass
class ResultatCopie:
    succes: bool
    code: int
    message: str


def est_jonction(chemin):
    """True si le chemin est un point de reparse (jonction ou symlink)."""
    try:
        return bool(os.lstat(chemin).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except OSError:
        return False


def creer_jonction(lien, cible):
    """Crée une jonction `lien` -> `cible` (mklink /J)."""
    proc = subprocess.run(
        ["cmd", "/c", "mklink", "/J", lien, cible],
        capture_output=True, text=True, encoding="oem", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"mklink a échoué : {proc.stderr or proc.stdout}")


def supprimer_jonction(lien):
    """Supprime UNIQUEMENT le lien de jonction, jamais son contenu."""
    if not est_jonction(lien):
        raise ValueError(
            f"'{lien}' n'est pas une jonction ; suppression refusée par sécurité."
        )
    proc = subprocess.run(
        ["cmd", "/c", "rmdir", lien],
        capture_output=True, text=True, encoding="oem", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"rmdir a échoué : {proc.stderr or proc.stdout}")


def copier(source, destination):
    """Copie source -> destination via robocopy, sans supprimer la source."""
    args = [
        "robocopy", source, destination,
        "/E", "/COPY:DATS", "/DCOPY:DAT", "/R:1", "/W:1",
    ]
    proc = subprocess.run(args, capture_output=True, text=True, encoding="oem", errors="replace")
    code = proc.returncode
    succes = code < 8
    return ResultatCopie(succes=succes, code=code, message=proc.stdout)


def _supprimer_arbre(chemin):
    """rmtree robuste : force la suppression des fichiers en lecture seule (Windows)."""
    def _forcer(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(chemin, onexc=_forcer)


class ErreurDeplacement(Exception):
    pass


def valider(source, destination, marge=100 * 1024 * 1024):
    if not os.path.isdir(source):
        raise ErreurDeplacement(f"La source n'existe pas ou n'est pas un dossier : {source}")
    if est_jonction(source):
        raise ErreurDeplacement(f"La source est déjà une jonction : {source}")
    if os.path.exists(destination):
        raise ErreurDeplacement(f"La destination existe déjà : {destination}")
    besoin = diskinfo.taille_dossier(source) + marge
    libre = diskinfo.espace_libre(diskinfo.lettre_lecteur(destination))
    if libre < besoin:
        raise ErreurDeplacement(
            f"Espace insuffisant sur la cible : {libre} octets libres, {besoin} requis."
        )


def deplacer(source, destination, progression=None):
    def _dire(msg):
        if progression:
            progression(msg)

    _dire("Validation…")
    valider(source, destination)

    _dire("Copie en cours…")
    res = copier(source, destination)
    if not res.succes:
        # Nettoyage de la copie partielle, original intact
        if os.path.exists(destination):
            shutil.rmtree(destination, ignore_errors=True)
        raise ErreurDeplacement(f"La copie a échoué (code robocopy {res.code}). Original intact.")

    _dire("Suppression de l'original…")
    _supprimer_arbre(source)

    _dire("Création de la jonction…")
    creer_jonction(source, destination)
    _dire("Terminé.")

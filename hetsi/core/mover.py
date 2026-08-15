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
        creationflags=subprocess.CREATE_NO_WINDOW,
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
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"rmdir a échoué : {proc.stderr or proc.stdout}")


def copier(source, destination):
    """Copie source -> destination via robocopy, sans supprimer la source."""
    args = [
        "robocopy", source, destination,
        "/E", "/COPY:DATS", "/DCOPY:DAT", "/R:1", "/W:1",
    ]
    proc = subprocess.run(
        args, capture_output=True, text=True, encoding="oem", errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
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


def valider(source, destination, marge=100 * 1024 * 1024, fusion=False):
    """Vérifie que le déplacement source -> destination est possible, sinon lève ErreurDeplacement.

    Quand `fusion` est vrai, une destination existante est acceptée (reprise
    d'un déplacement interrompu).
    """
    if not os.path.isdir(source):
        raise ErreurDeplacement(f"La source n'existe pas ou n'est pas un dossier : {source}")
    if est_jonction(source):
        raise ErreurDeplacement(f"La source est déjà une jonction : {source}")
    src_abs = os.path.abspath(source)
    dst_abs = os.path.abspath(destination)
    src_cmp = os.path.normcase(src_abs)
    dst_cmp = os.path.normcase(dst_abs)
    if dst_cmp == src_cmp or dst_cmp.startswith(src_cmp + os.sep):
        raise ErreurDeplacement(
            f"La destination est à l'intérieur de la source : {destination}"
        )
    if src_cmp.startswith(dst_cmp + os.sep):
        raise ErreurDeplacement(
            f"La source est à l'intérieur de la destination : {destination}"
        )
    if os.path.exists(destination) and not fusion:
        raise ErreurDeplacement(f"La destination existe déjà : {destination}")
    besoin = diskinfo.taille_dossier(source) + marge
    if fusion and os.path.isdir(destination):
        besoin = max(0, diskinfo.taille_dossier(source)
                     - diskinfo.taille_dossier(destination)) + marge
    libre = diskinfo.espace_libre(diskinfo.lettre_lecteur(destination))
    if libre < besoin:
        raise ErreurDeplacement(
            f"Espace insuffisant sur la cible : {libre} octets libres, {besoin} requis."
        )


def deplacer(source, destination, progression=None, apres_copie=None, fusion=False):
    """Orchestre le déplacement complet : valide, copie, supprime l'original, crée la jonction.

    En mode `fusion`, la destination préexiste : elle n'est jamais supprimée,
    même si la copie échoue. Robocopy écrase toutefois les fichiers de même
    nom qu'il recopie ; seule la suppression de l'arborescence est exclue,
    pas la réécriture fichier par fichier.
    """
    def _dire(msg):
        if progression:
            progression(msg)

    _dire("Validation…")
    valider(source, destination, fusion=fusion)

    _dire("Copie en cours…")
    res = copier(source, destination)
    if not res.succes:
        if not fusion:
            # Nettoyage de la copie partielle que nous venons de créer.
            # En fusion la destination appartient à l'utilisateur : on n'y touche pas.
            try:
                if os.path.exists(destination):
                    _supprimer_arbre(destination)
            except OSError:
                pass  # ne pas masquer l'erreur de copie d'origine
        raise ErreurDeplacement(f"La copie a échoué (code robocopy {res.code}). Original intact.")

    _dire("Suppression de l'original…")
    _supprimer_arbre(source)

    if apres_copie is not None:
        apres_copie(source, destination)

    _dire("Création de la jonction…")
    creer_jonction(source, destination)
    _dire("Terminé.")

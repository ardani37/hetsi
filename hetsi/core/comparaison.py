"""Compare une source et une destination existante (reprise de déplacement)."""
import os
import stat
from dataclasses import dataclass, field


@dataclass
class Comparaison:
    identiques: list = field(default_factory=list)
    manquants: list = field(default_factory=list)
    differents: list = field(default_factory=list)
    en_trop: list = field(default_factory=list)
    verdict: str = "vide"


def _est_point_reparse(chemin):
    try:
        return bool(
            os.lstat(chemin).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        )
    except OSError:
        return False


def _fichiers_relatifs(racine):
    """Chemin relatif normalisé -> taille. Ne suit pas les points de reparse."""
    trouves = {}
    if not os.path.isdir(racine):
        return trouves
    for dossier, sous_dossiers, fichiers in os.walk(racine):
        sous_dossiers[:] = [
            d for d in sous_dossiers if not _est_point_reparse(os.path.join(dossier, d))
        ]
        fichiers = [
            f for f in fichiers if not _est_point_reparse(os.path.join(dossier, f))
        ]
        for f in fichiers:
            complet = os.path.join(dossier, f)
            relatif = os.path.relpath(complet, racine).replace("/", "\\").lower()
            try:
                trouves[relatif] = os.path.getsize(complet)
            except OSError:
                pass
    return trouves


def comparer(source, destination):
    """Compare `source` et `destination` par chemin relatif et taille."""
    fichiers_src = _fichiers_relatifs(source)
    fichiers_dst = _fichiers_relatifs(destination)

    c = Comparaison()
    for relatif, taille in fichiers_src.items():
        if relatif not in fichiers_dst:
            c.manquants.append(relatif)
        elif fichiers_dst[relatif] != taille:
            c.differents.append(relatif)
        else:
            c.identiques.append(relatif)
    for relatif in fichiers_dst:
        if relatif not in fichiers_src:
            c.en_trop.append(relatif)

    if not fichiers_dst:
        c.verdict = "vide"
    elif c.en_trop:
        c.verdict = "etrangere"
    elif c.manquants or c.differents:
        c.verdict = "partielle"
    else:
        c.verdict = "complete"
    return c

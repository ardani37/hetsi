# hetsi/core/mover.py
"""Cœur : détection de jonction et copie robocopy."""
import os
import stat
import subprocess
from dataclasses import dataclass


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


def copier(source, destination):
    """Copie source -> destination via robocopy, sans supprimer la source."""
    args = [
        "robocopy", source, destination,
        "/E", "/COPY:DATS", "/DCOPY:DAT", "/R:1", "/W:1",
    ]
    proc = subprocess.run(args, capture_output=True, text=True)
    code = proc.returncode
    succes = code < 8
    return ResultatCopie(succes=succes, code=code, message=proc.stdout)

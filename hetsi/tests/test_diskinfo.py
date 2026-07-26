# hetsi/tests/test_diskinfo.py
import os
from hetsi.core import diskinfo


def test_taille_dossier_somme_les_fichiers(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"12345")       # 5 octets
    sub = tmp_path / "sous"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"6789")             # 4 octets
    assert diskinfo.taille_dossier(str(tmp_path)) == 9


def test_taille_dossier_vide(tmp_path):
    assert diskinfo.taille_dossier(str(tmp_path)) == 0


def test_espace_libre_positif(tmp_path):
    assert diskinfo.espace_libre(str(tmp_path)) > 0


def test_lettre_lecteur():
    assert diskinfo.lettre_lecteur(r"C:\Program Files\X") == "C:\\"


def test_lecteurs_disponibles_contient_un_lecteur():
    lecteurs = diskinfo.lecteurs_disponibles()
    assert isinstance(lecteurs, list)
    assert len(lecteurs) >= 1
    assert all(l.endswith(":\\") for l in lecteurs)

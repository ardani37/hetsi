import json
import os
from hetsi.core import mover
from hetsi.core.history import Historique


def test_ajouter_et_lire(tmp_path):
    h = Historique(str(tmp_path / "history.json"))
    h.ajouter("C:\\src", "D:\\dst", 123, "2026-07-26 10:00")
    entrees = h.entrees()
    assert len(entrees) == 1
    assert entrees[0]["source"] == "C:\\src"
    assert entrees[0]["taille"] == 123


def test_persistance_sur_disque(tmp_path):
    chemin = str(tmp_path / "history.json")
    Historique(chemin).ajouter("C:\\a", "D:\\a", 1, "2026-07-26 10:00")
    # Relecture par une nouvelle instance
    assert len(Historique(chemin).entrees()) == 1


def test_annuler_restaure_le_dossier(tmp_path):
    # Prépare un déplacement réel via le moteur
    src = tmp_path / "app"; src.mkdir()
    (src / "bin.exe").write_bytes(b"programme")
    dst = tmp_path / "cible" / "app"
    mover.deplacer(str(src), str(dst))
    assert mover.est_jonction(str(src)) is True

    h = Historique(str(tmp_path / "history.json"))
    h.ajouter(str(src), str(dst), 9, "2026-07-26 10:00")

    h.annuler(0)

    # La jonction a disparu, le dossier est redevenu réel avec son contenu
    assert mover.est_jonction(str(src)) is False
    assert (src / "bin.exe").read_bytes() == b"programme"
    # La copie sur la cible a été supprimée
    assert not os.path.exists(str(dst))
    # L'entrée d'historique a été retirée
    assert h.entrees() == []

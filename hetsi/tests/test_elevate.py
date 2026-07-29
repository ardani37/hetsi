import os
from hetsi.core import elevate


def test_est_admin_renvoie_bool():
    assert isinstance(elevate.est_admin(), bool)


def test_chemin_donnees(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    chemin = elevate.chemin_donnees()
    assert chemin.endswith(os.path.join("hetsi", "history.json"))
    # Le dossier parent a été créé
    assert os.path.isdir(os.path.dirname(chemin))


def test_chemin_log(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    chemin = elevate.chemin_log()
    assert chemin.endswith(os.path.join("hetsi", "hetsi.log"))
    assert os.path.isdir(os.path.dirname(chemin))


def test_racine_projet_contient_le_paquet_hetsi():
    import hetsi
    racine = os.path.dirname(os.path.dirname(os.path.abspath(hetsi.__file__)))
    # le paquet hetsi doit se trouver directement sous la racine
    assert os.path.isdir(os.path.join(racine, "hetsi"))
    assert os.path.isfile(os.path.join(racine, "hetsi", "run.py")) or os.path.isdir(os.path.join(racine, "hetsi", "core"))

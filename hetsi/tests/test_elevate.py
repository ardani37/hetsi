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

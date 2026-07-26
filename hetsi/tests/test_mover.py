# hetsi/tests/test_mover.py
import os
import pytest
from hetsi.core import mover


def test_est_jonction_faux_pour_dossier_normal(tmp_path):
    assert mover.est_jonction(str(tmp_path)) is False


def test_est_jonction_vrai_pour_jonction(tmp_path):
    import subprocess
    cible = tmp_path / "cible"; cible.mkdir()
    lien = tmp_path / "lien"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(lien), str(cible)], check=True, capture_output=True)
    assert mover.est_jonction(str(lien)) is True


def test_copier_reussit(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello")
    dst = tmp_path / "dst"
    res = mover.copier(str(src), str(dst))
    assert res.succes is True
    assert res.code < 8
    assert (dst / "a.txt").read_bytes() == b"hello"


def test_copier_arborescence(tmp_path):
    src = tmp_path / "src"
    (src / "sous").mkdir(parents=True)
    (src / "sous" / "b.txt").write_bytes(b"x")
    dst = tmp_path / "dst"
    res = mover.copier(str(src), str(dst))
    assert res.succes is True
    assert (dst / "sous" / "b.txt").exists()


def test_copier_renvoie_un_message(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    (src / "a.txt").write_bytes(b"x")
    res = mover.copier(str(src), str(tmp_path / "dst"))
    assert res.succes is True
    assert res.message.strip() != ""


def test_creer_puis_supprimer_jonction(tmp_path):
    cible = tmp_path / "cible"
    cible.mkdir()
    (cible / "a.txt").write_bytes(b"data")
    lien = tmp_path / "lien"

    mover.creer_jonction(str(lien), str(cible))
    assert mover.est_jonction(str(lien)) is True
    # Le contenu est visible à travers la jonction
    assert (lien / "a.txt").read_bytes() == b"data"

    mover.supprimer_jonction(str(lien))
    assert not os.path.exists(str(lien))
    # La cible et son contenu sont intacts
    assert (cible / "a.txt").read_bytes() == b"data"


def test_supprimer_jonction_refuse_dossier_normal(tmp_path):
    normal = tmp_path / "normal"
    normal.mkdir()
    (normal / "important.txt").write_bytes(b"ne pas perdre")
    with pytest.raises(ValueError):
        mover.supprimer_jonction(str(normal))
    # Rien n'a été supprimé
    assert (normal / "important.txt").exists()

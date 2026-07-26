# hetsi/tests/test_mover.py
import os
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

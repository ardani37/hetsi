# hetsi/tests/test_mover.py
import os
from hetsi.core import mover


def test_est_jonction_faux_pour_dossier_normal(tmp_path):
    assert mover.est_jonction(str(tmp_path)) is False


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

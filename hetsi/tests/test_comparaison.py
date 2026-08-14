import os
import subprocess

from hetsi.core import comparaison


def _ecrire(chemin, contenu=b"x"):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as f:
        f.write(contenu)


def test_destination_absente_verdict_vide(tmp_path):
    src = tmp_path / "src"
    _ecrire(str(src / "a.txt"), b"12345")
    c = comparaison.comparer(str(src), str(tmp_path / "absente"))
    assert c.verdict == "vide"


def test_destination_sans_fichier_verdict_vide(tmp_path):
    src = tmp_path / "src"
    _ecrire(str(src / "a.txt"), b"12345")
    dst = tmp_path / "dst"
    dst.mkdir()
    assert comparaison.comparer(str(src), str(dst)).verdict == "vide"


def test_copie_complete(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _ecrire(str(src / "a.txt"), b"12345")
    _ecrire(str(src / "sous" / "b.txt"), b"67")
    _ecrire(str(dst / "a.txt"), b"12345")
    _ecrire(str(dst / "sous" / "b.txt"), b"67")

    c = comparaison.comparer(str(src), str(dst))
    assert c.verdict == "complete"
    assert c.manquants == []
    assert c.differents == []
    assert c.en_trop == []
    assert len(c.identiques) == 2


def test_copie_partielle(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _ecrire(str(src / "a.txt"), b"12345")
    _ecrire(str(src / "b.txt"), b"67")
    _ecrire(str(dst / "a.txt"), b"12345")

    c = comparaison.comparer(str(src), str(dst))
    assert c.verdict == "partielle"
    assert [os.path.basename(m) for m in c.manquants] == ["b.txt"]
    assert c.en_trop == []


def test_fichier_de_taille_differente(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _ecrire(str(src / "a.txt"), b"12345")
    _ecrire(str(dst / "a.txt"), b"1")

    c = comparaison.comparer(str(src), str(dst))
    assert c.verdict == "partielle"
    assert len(c.differents) == 1
    assert c.identiques == []


def test_fichier_etranger_dans_la_cible(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    _ecrire(str(src / "a.txt"), b"12345")
    _ecrire(str(dst / "a.txt"), b"12345")
    _ecrire(str(dst / "inconnu.txt"), b"???")

    c = comparaison.comparer(str(src), str(dst))
    assert c.verdict == "etrangere"
    assert len(c.en_trop) == 1


def test_ne_suit_pas_les_jonctions(tmp_path):
    src = tmp_path / "src"
    _ecrire(str(src / "a.txt"), b"12345")
    ailleurs = tmp_path / "ailleurs"
    _ecrire(str(ailleurs / "gros.bin"), b"y" * 500)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(src / "lien"), str(ailleurs)],
        check=True, capture_output=True,
    )
    dst = tmp_path / "dst"
    _ecrire(str(dst / "a.txt"), b"12345")

    # Le contenu derrière la jonction ne doit pas compter comme manquant
    c = comparaison.comparer(str(src), str(dst))
    assert c.verdict == "complete"

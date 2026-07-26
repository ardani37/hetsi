# hetsi/tests/test_mover.py
import os
import stat
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


def test_valider_refuse_source_absente(tmp_path):
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(tmp_path / "inexistant"), str(tmp_path / "dst"))


def test_valider_refuse_destination_existante(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    dst = tmp_path / "dst"; dst.mkdir()
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), str(dst))


def test_valider_refuse_source_deja_jonction(tmp_path):
    cible = tmp_path / "cible"; cible.mkdir()
    lien = tmp_path / "lien"
    mover.creer_jonction(str(lien), str(cible))
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(lien), str(tmp_path / "dst"))


def test_deplacer_complet(tmp_path):
    src = tmp_path / "app"; src.mkdir()
    (src / "bin.exe").write_bytes(b"programme")
    dst = tmp_path / "autre" / "app"

    mover.deplacer(str(src), str(dst))

    # Contenu déplacé sur la cible
    assert (dst / "bin.exe").read_bytes() == b"programme"
    # Source est maintenant une jonction
    assert mover.est_jonction(str(src)) is True
    # Le programme reste accessible via l'ancien chemin
    assert (src / "bin.exe").read_bytes() == b"programme"


def test_deplacer_avec_fichier_lecture_seule(tmp_path):
    src = tmp_path / "app"; src.mkdir()
    fichier = src / "readonly.dat"
    fichier.write_bytes(b"protege")
    os.chmod(str(fichier), stat.S_IREAD)
    dst = tmp_path / "autre" / "app"

    try:
        mover.deplacer(str(src), str(dst))

        # Déplacement réussi malgré le fichier en lecture seule
        assert mover.est_jonction(str(src)) is True
        assert (dst / "readonly.dat").read_bytes() == b"protege"
        assert (src / "readonly.dat").read_bytes() == b"protege"
    finally:
        # Nettoyage : rétablir les droits d'écriture pour permettre la suppression par pytest
        cible = dst / "readonly.dat"
        if cible.exists():
            os.chmod(str(cible), stat.S_IWRITE)


def test_deplacer_copie_echoue_source_intacte(tmp_path, monkeypatch):
    src = tmp_path / "app"; src.mkdir()
    (src / "bin.exe").write_bytes(b"programme")
    dst = tmp_path / "autre" / "app"

    def faux_copier(source, destination):
        os.makedirs(destination, exist_ok=True)
        with open(os.path.join(destination, "partiel.tmp"), "wb") as f:
            f.write(b"incomplet")
        return mover.ResultatCopie(succes=False, code=8, message="echec simule")

    monkeypatch.setattr(mover, "copier", faux_copier)

    with pytest.raises(mover.ErreurDeplacement):
        mover.deplacer(str(src), str(dst))

    assert mover.est_jonction(str(src)) is False
    assert (src / "bin.exe").read_bytes() == b"programme"
    assert not os.path.exists(str(dst))


def test_valider_refuse_espace_insuffisant(tmp_path, monkeypatch):
    src = tmp_path / "src"; src.mkdir()
    (src / "a.txt").write_bytes(b"x" * 10)
    monkeypatch.setattr(mover.diskinfo, "espace_libre", lambda lecteur: 0)
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), str(tmp_path / "dst"))

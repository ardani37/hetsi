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


def test_deplacer_appelle_apres_copie_avant_jonction(tmp_path, monkeypatch):
    src = tmp_path / "app"; src.mkdir()
    (src / "bin.exe").write_bytes(b"programme")
    dst = tmp_path / "cible" / "app"
    appels = []

    def apres(source, destination):
        appels.append((source, destination))
        # à ce stade l'original est déjà supprimé et la copie faite
        assert os.path.exists(destination)
        assert not mover.est_jonction(source)  # jonction pas encore créée

    mover.deplacer(str(src), str(dst), apres_copie=apres)
    assert appels == [(str(src), str(dst))]
    assert mover.est_jonction(str(src)) is True


def test_deplacer_apres_copie_appele_meme_si_jonction_echoue(tmp_path, monkeypatch):
    src = tmp_path / "app"; src.mkdir()
    (src / "bin.exe").write_bytes(b"x")
    dst = tmp_path / "cible" / "app"
    appels = []
    monkeypatch.setattr(mover, "creer_jonction",
                        lambda l, c: (_ for _ in ()).throw(RuntimeError("mklink KO")))
    with pytest.raises(RuntimeError):
        mover.deplacer(str(src), str(dst), apres_copie=lambda s, d: appels.append((s, d)))
    # apres_copie a bien été appelé avant l'échec de la jonction
    assert appels == [(str(src), str(dst))]


def test_valider_accepte_destination_existante_en_fusion(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    (src / "a.txt").write_bytes(b"x")
    dst = tmp_path / "dst"; dst.mkdir()
    # Sans fusion : refus (comportement historique)
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), str(dst))
    # Avec fusion : accepté
    mover.valider(str(src), str(dst), fusion=True)


def test_deplacer_fusion_reprend_une_copie_partielle(tmp_path):
    src = tmp_path / "app"; src.mkdir()
    (src / "a.txt").write_bytes(b"12345")
    (src / "b.txt").write_bytes(b"67")
    dst = tmp_path / "cible" / "app"
    os.makedirs(str(dst))
    (dst / "a.txt").write_bytes(b"12345")  # déjà copié

    mover.deplacer(str(src), str(dst), fusion=True)

    assert (dst / "a.txt").read_bytes() == b"12345"
    assert (dst / "b.txt").read_bytes() == b"67"
    assert mover.est_jonction(str(src)) is True
    assert (src / "b.txt").read_bytes() == b"67"


def test_deplacer_fusion_ne_supprime_pas_la_destination_si_copie_echoue(tmp_path, monkeypatch):
    src = tmp_path / "app"; src.mkdir()
    (src / "a.txt").write_bytes(b"programme")
    dst = tmp_path / "cible" / "app"
    os.makedirs(str(dst))
    (dst / "deja_la.txt").write_bytes(b"donnees precieuses")

    monkeypatch.setattr(
        mover, "copier",
        lambda source, destination: mover.ResultatCopie(
            succes=False, code=8, message="echec simule"),
    )

    with pytest.raises(mover.ErreurDeplacement):
        mover.deplacer(str(src), str(dst), fusion=True)

    # La destination préexistante est intacte, et l'original aussi
    assert (dst / "deja_la.txt").read_bytes() == b"donnees precieuses"
    assert (src / "a.txt").read_bytes() == b"programme"
    assert mover.est_jonction(str(src)) is False


def test_deplacer_sans_fusion_nettoie_toujours_la_destination(tmp_path, monkeypatch):
    src = tmp_path / "app"; src.mkdir()
    (src / "a.txt").write_bytes(b"programme")
    dst = tmp_path / "cible" / "app"

    def faux_copier(source, destination):
        os.makedirs(destination, exist_ok=True)
        with open(os.path.join(destination, "partiel.tmp"), "wb") as f:
            f.write(b"incomplet")
        return mover.ResultatCopie(succes=False, code=8, message="echec simule")

    monkeypatch.setattr(mover, "copier", faux_copier)

    with pytest.raises(mover.ErreurDeplacement):
        mover.deplacer(str(src), str(dst))

    assert not os.path.exists(str(dst))


def test_valider_refuse_destination_dans_la_source(tmp_path):
    src = tmp_path / "app"; src.mkdir()
    (src / "a.txt").write_bytes(b"x")
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), str(src / "sous"))
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), str(src / "sous"), fusion=True)
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), str(src))


def test_deplacer_refuse_destination_dans_la_source_sans_perte(tmp_path):
    src = tmp_path / "app"; src.mkdir()
    (src / "a.txt").write_bytes(b"precieux")
    with pytest.raises(mover.ErreurDeplacement):
        mover.deplacer(str(src), str(src / "sous"))
    assert (src / "a.txt").read_bytes() == b"precieux"
    assert mover.est_jonction(str(src)) is False


def test_copier_ne_purge_pas_la_destination(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    (src / "a.txt").write_bytes(b"AAAAA")
    dst = tmp_path / "dst"; dst.mkdir()
    (dst / "a.txt").write_bytes(b"PARTIEL")
    (dst / "fichier_utilisateur.txt").write_bytes(b"a moi")

    res = mover.copier(str(src), str(dst))

    assert res.succes is True
    assert (dst / "a.txt").read_bytes() == b"AAAAA"          # reparé
    assert (dst / "fichier_utilisateur.txt").read_bytes() == b"a moi"  # préservé


def test_valider_refuse_destination_dans_la_source_casse_differente(tmp_path):
    src = tmp_path / "App"; src.mkdir()
    (src / "a.txt").write_bytes(b"x")
    # Même emplacement physique, casse différente : doit être refusé aussi
    dst = os.path.join(str(src).upper(), "sous")
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), dst)
    with pytest.raises(mover.ErreurDeplacement):
        mover.valider(str(src), dst, fusion=True)


def test_valider_accepte_un_frere_au_prefixe_commun(tmp_path):
    src = tmp_path / "App"; src.mkdir()
    (src / "a.txt").write_bytes(b"x")
    frere = tmp_path / "App2" / "cible"
    # "App2" partage le préfixe "App" mais n'est pas dans la source : accepté
    mover.valider(str(src), str(frere))

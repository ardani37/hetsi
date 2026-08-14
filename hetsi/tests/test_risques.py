# hetsi/tests/test_risques.py
from hetsi.core import risques


def _codes(liste):
    return {r.code for r in liste}


def test_dossier_windows_est_bloquant(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    r = risques.analyser("C:\\Windows", str(tmp_path))
    assert "dossier_systeme" in _codes(r)
    assert any(x.niveau == "bloquant" for x in r if x.code == "dossier_systeme")


def test_sous_dossier_windows_est_bloquant(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    assert "dossier_systeme" in _codes(risques.analyser("C:\\Windows\\System32", str(tmp_path)))


def test_racine_program_files_bloquante_mais_pas_un_logiciel_dedans(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    assert "dossier_systeme" in _codes(risques.analyser("C:\\Program Files", str(tmp_path)))
    assert "dossier_systeme" not in _codes(
        risques.analyser("C:\\Program Files\\Adobe", str(tmp_path)))


def test_racine_de_lecteur_bloquante(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    assert "dossier_systeme" in _codes(risques.analyser("D:\\", str(tmp_path)))


def test_meme_disque_est_signale(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    src = tmp_path / "src"; src.mkdir()
    dst = tmp_path / "dst"; dst.mkdir()
    r = risques.analyser(str(src), str(dst))
    assert "meme_disque" in _codes(r)


def test_cible_amovible_est_signalee(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    monkeypatch.setattr(risques, "_type_lecteur", lambda racine: 2)  # DRIVE_REMOVABLE
    r = risques.analyser("C:\\Program Files\\Adobe", str(tmp_path))
    assert "cible_amovible" in _codes(r)


def test_service_windows_est_signale(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: ["MonAntivirus"])
    r = risques.analyser("C:\\Program Files\\Antivirus", str(tmp_path))
    assert "service_windows" in _codes(r)
    assert any("MonAntivirus" in x.message for x in r if x.code == "service_windows")


def test_deplacement_sain_sans_risque(tmp_path, monkeypatch):
    monkeypatch.setattr(risques, "_services_du_dossier", lambda d: [])
    monkeypatch.setattr(risques, "_type_lecteur", lambda racine: 3)  # DRIVE_FIXED
    monkeypatch.setattr(risques.diskinfo, "lettre_lecteur",
                        lambda chemin: "C:\\" if "Program" in chemin else "E:\\")
    assert risques.analyser("C:\\Program Files\\Adobe", "E:\\Logiciels\\Adobe") == []

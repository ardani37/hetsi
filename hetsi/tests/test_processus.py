import os
import shutil
import subprocess
import sys
import time

from hetsi.core import processus


def _lancer_python_depuis(dossier):
    """Copie un exécutable dans `dossier` et lance un processus qui dort.

    Note : on copie cmd.exe plutôt que sys.executable. Un python.exe copié
    seul ne trouve pas sa pythonXX.dll (STATUS_DLL_NOT_FOUND) ; cmd.exe,
    lui, a ses dépendances dans System32 et démarre sans souci depuis une
    copie isolée.
    """
    os.makedirs(dossier, exist_ok=True)
    exe = os.path.join(dossier, "faux_logiciel.exe")
    shutil.copy2(r"C:\Windows\System32\cmd.exe", exe)
    proc = subprocess.Popen(
        [exe, "/c", "ping", "-n", "60", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)  # laisser le processus démarrer
    return proc, exe


def test_dossier_sans_processus(tmp_path):
    vide = tmp_path / "vide"
    vide.mkdir()
    assert processus.processus_du_dossier(str(vide)) == []


def test_detecte_puis_ferme_un_processus(tmp_path):
    dossier = str(tmp_path / "appli")
    proc, exe = _lancer_python_depuis(dossier)
    try:
        trouves = processus.processus_du_dossier(dossier)
        assert any(p.pid == proc.pid for p in trouves)
        assert all(p.chemin.lower().startswith(dossier.lower()) for p in trouves)

        # Un processus console sans fenêtre ne répond pas à la fermeture propre :
        # on force, ce qui est le chemin de repli prévu.
        assert processus.fermer(proc.pid, force=True) is True
        assert processus.processus_du_dossier(dossier) == []
    finally:
        # cmd.exe lance ping.exe comme processus enfant. Le tuer (via
        # fermer(force=True) ou proc.kill()) ne tue pas cet enfant sous
        # Windows : on le retrouve par ParentProcessId (conservé sur
        # l'objet processus enfant même après la mort du parent) et on le
        # ferme explicitement pour ne laisser aucun processus orphelin.
        subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "Get-CimInstance Win32_Process -Filter "
                f"'ParentProcessId={proc.pid}' | ForEach-Object "
                "{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


def test_erreur_powershell_renvoie_liste_vide(tmp_path, monkeypatch):
    monkeypatch.setattr(processus, "_powershell", lambda script: "")
    assert processus.processus_du_dossier(str(tmp_path)) == []


def test_sortie_powershell_objet_unique(monkeypatch):
    # PowerShell renvoie un objet (pas une liste) quand il n'y a qu'un résultat.
    monkeypatch.setattr(
        processus, "_powershell",
        lambda script: '{"Id": 42, "ProcessName": "jeu", "Path": "C:\\\\Jeux\\\\jeu.exe"}',
    )
    trouves = processus.processus_du_dossier("C:\\Jeux")
    assert len(trouves) == 1
    assert trouves[0].pid == 42
    assert trouves[0].nom == "jeu"

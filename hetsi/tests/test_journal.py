import logging
from hetsi.core import journal


def test_configurer_ecrit_dans_le_fichier(tmp_path):
    chemin = str(tmp_path / "hetsi.log")
    log = journal.configurer(chemin)
    log.info("bonjour")
    for h in log.handlers:
        h.flush()
    with open(chemin, encoding="utf-8") as f:
        contenu = f.read()
    assert "bonjour" in contenu


def test_journal_renvoie_le_meme_logger():
    assert journal.journal() is logging.getLogger("hetsi")


def test_configurer_ne_stacke_pas_les_handlers(tmp_path):
    chemin = str(tmp_path / "hetsi.log")
    journal.configurer(chemin)
    journal.configurer(chemin)
    fichiers = [h for h in journal.journal().handlers if isinstance(h, logging.FileHandler)]
    assert len(fichiers) == 1

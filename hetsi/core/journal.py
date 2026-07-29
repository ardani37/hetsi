"""Journal fichier de hetsi (diagnostic)."""
import logging


def configurer(chemin_log):
    log = logging.getLogger("hetsi")
    log.setLevel(logging.INFO)
    # éviter d'empiler les handlers si rappelé
    log.handlers = [h for h in log.handlers if not isinstance(h, logging.FileHandler)]
    handler = logging.FileHandler(chemin_log, mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    return log


def journal():
    return logging.getLogger("hetsi")

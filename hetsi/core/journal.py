"""Journal fichier de hetsi (diagnostic)."""
import logging


def configurer(chemin_log):
    log = logging.getLogger("hetsi")
    log.setLevel(logging.INFO)
    # éviter d'empiler les handlers si rappelé (et fermer pour libérer le fd)
    for h in [h for h in log.handlers if isinstance(h, logging.FileHandler)]:
        h.close()
        log.removeHandler(h)
    handler = logging.FileHandler(chemin_log, mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    return log


def journal():
    return logging.getLogger("hetsi")

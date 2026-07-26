# hetsi/run.py
"""Point d'entrée hetsi : élève en admin puis lance la fenêtre."""
import sys

from hetsi.core import elevate
from hetsi.gui import app


def main():
    if elevate.relancer_en_admin():
        sys.exit(0)  # relancé en admin, on quitte l'instance non élevée
    app.lancer(elevate.chemin_donnees())


if __name__ == "__main__":
    main()

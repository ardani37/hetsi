# hetsi/core/history.py
"""Persistance JSON de l'historique des déplacements + annulation."""
import json
import os

from hetsi.core import mover


class Historique:
    def __init__(self, chemin_json):
        self.chemin = chemin_json

    def _lire(self):
        if not os.path.exists(self.chemin):
            return []
        with open(self.chemin, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ecrire(self, entrees):
        dossier = os.path.dirname(self.chemin)
        if dossier:
            os.makedirs(dossier, exist_ok=True)
        with open(self.chemin, "w", encoding="utf-8") as f:
            json.dump(entrees, f, ensure_ascii=False, indent=2)

    def entrees(self):
        return self._lire()

    def ajouter(self, source, destination, taille, date, fusion=False):
        entrees = self._lire()
        entrees.append({
            "source": source,
            "destination": destination,
            "taille": taille,
            "date": date,
            "fusion": bool(fusion),
        })
        self._ecrire(entrees)

    def annuler(self, index, progression=None):
        def _dire(msg):
            if progression:
                progression(msg)

        entrees = self._lire()
        e = entrees[index]
        source, destination = e["source"], e["destination"]

        _dire("Suppression de la jonction…")
        mover.supprimer_jonction(source)

        _dire("Recopie vers l'emplacement d'origine…")
        res = mover.copier(destination, source)
        if not res.succes:
            # robocopy a pu laisser un dossier partiel a `source` ; mklink /J
            # echoue si le chemin du lien existe deja, donc on nettoie d'abord.
            if os.path.exists(source):
                try:
                    mover._supprimer_arbre(source)
                except OSError:
                    pass
            # Recrée la jonction pour ne pas laisser un état cassé
            mover.creer_jonction(source, destination)
            raise mover.ErreurDeplacement(
                f"La recopie a échoué (code {res.code}). Jonction rétablie."
            )

        _dire("Suppression de la copie sur la cible…")
        if not e.get("fusion", False):
            try:
                mover._supprimer_arbre(destination)
            except OSError:
                pass  # ne pas masquer la réussite de la restauration

        entrees.pop(index)
        self._ecrire(entrees)
        _dire("Annulation terminée.")

# hetsi/gui/app.py
"""Fenêtre principale hetsi : ajouter, file d'attente, historique."""
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from hetsi.core import diskinfo, mover
from hetsi.core.history import Historique


class App(tk.Tk):
    def __init__(self, chemin_donnees):
        super().__init__()
        self.title("hetsi — déplacer des logiciels vers un autre lecteur")
        self.geometry("820x620")
        self.historique = Historique(chemin_donnees)
        self.file = []  # liste de (source, destination, taille)
        self._occupe = False
        self._construire()
        self._rafraichir_historique()

    # --- Construction de l'interface ---
    def _construire(self):
        # Zone Ajouter
        cadre_haut = ttk.LabelFrame(self, text="Ajouter un dossier")
        cadre_haut.pack(fill="x", padx=10, pady=8)

        self.var_source = tk.StringVar()
        ttk.Button(cadre_haut, text="Choisir un dossier…",
                   command=self._choisir).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(cadre_haut, textvariable=self.var_source, width=60,
                  anchor="w").grid(row=0, column=1, columnspan=3, sticky="w")

        ttk.Label(cadre_haut, text="Lecteur cible :").grid(row=1, column=0, padx=5)
        self.var_cible = tk.StringVar()
        self.combo_cible = ttk.Combobox(cadre_haut, textvariable=self.var_cible,
                                        values=diskinfo.lecteurs_disponibles(),
                                        state="readonly", width=8)
        self.combo_cible.grid(row=1, column=1, sticky="w")

        self.var_apercu = tk.StringVar(value="")
        ttk.Label(cadre_haut, textvariable=self.var_apercu,
                  foreground="#555").grid(row=2, column=0, columnspan=4,
                                          sticky="w", padx=5, pady=3)
        ttk.Button(cadre_haut, text="Ajouter à la file",
                   command=self._ajouter_file).grid(row=1, column=3, padx=5)

        # Zone File d'attente
        cadre_file = ttk.LabelFrame(self, text="File d'attente")
        cadre_file.pack(fill="both", expand=True, padx=10, pady=8)
        self.tab_file = ttk.Treeview(cadre_file, columns=("src", "dst", "taille"),
                                     show="headings", height=6)
        for c, t in (("src", "Source"), ("dst", "Cible"), ("taille", "Taille")):
            self.tab_file.heading(c, text=t)
        self.tab_file.pack(fill="both", expand=True, side="left")

        self.var_etat = tk.StringVar(value="Prêt.")
        barre = ttk.Frame(self)
        barre.pack(fill="x", padx=10)
        self.progress = ttk.Progressbar(barre, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.btn_deplacer = ttk.Button(barre, text="Tout déplacer",
                                       command=self._tout_deplacer)
        self.btn_deplacer.pack(side="right")
        ttk.Label(self, textvariable=self.var_etat).pack(anchor="w", padx=10)

        # Zone Historique
        cadre_hist = ttk.LabelFrame(self, text="Historique")
        cadre_hist.pack(fill="both", expand=True, padx=10, pady=8)
        self.tab_hist = ttk.Treeview(cadre_hist, columns=("src", "dst", "date"),
                                     show="headings", height=6)
        for c, t in (("src", "Dossier"), ("dst", "Cible"), ("date", "Date")):
            self.tab_hist.heading(c, text=t)
        self.tab_hist.pack(fill="both", expand=True, side="left")
        self.btn_annuler = ttk.Button(cadre_hist, text="Annuler la ligne sélectionnée",
                                      command=self._annuler)
        self.btn_annuler.pack(side="bottom", pady=4)

    # --- Actions ---
    def _choisir(self):
        dossier = filedialog.askdirectory(title="Choisir le dossier à déplacer")
        if not dossier:
            return
        dossier = os.path.normpath(dossier)
        self.var_source.set(dossier)
        taille = diskinfo.taille_dossier(dossier)
        cible = self.var_cible.get() or (diskinfo.lecteurs_disponibles() or [""])[0]
        self.var_cible.set(cible)
        libre = diskinfo.espace_libre(cible) if cible else 0
        self.var_apercu.set(
            f"Taille : {self._go(taille)} • Espace libre sur {cible} : {self._go(libre)}"
        )

    def _ajouter_file(self):
        source = self.var_source.get()
        cible = self.var_cible.get()
        if not source or not cible:
            messagebox.showwarning("hetsi", "Choisis un dossier et un lecteur cible.")
            return
        # Destination = <cible>\hetsi_apps\<nom du dossier>
        nom = os.path.basename(source.rstrip("\\"))
        if not nom:
            messagebox.showwarning("hetsi", "Choisis un dossier, pas la racine d'un lecteur.")
            return
        destination = os.path.join(cible, "hetsi_apps", nom)
        taille = diskinfo.taille_dossier(source)
        self.file.append((source, destination, taille))
        self.tab_file.insert("", "end", values=(source, destination, self._go(taille)))
        self.var_source.set("")
        self.var_apercu.set("")

    def _tout_deplacer(self):
        if self._occupe:
            return
        if not self.file:
            return
        recap = "\n".join(f"{s}  ->  {d}" for s, d, _ in self.file)
        if not messagebox.askyesno("Confirmer le déplacement",
                                    f"Déplacer ces dossiers ?\n\n{recap}"):
            return
        self._occupe = True
        self.btn_deplacer.config(state="disabled")
        self.btn_annuler.config(state="disabled")
        threading.Thread(target=self._worker_deplacer, daemon=True).start()

    def _worker_deplacer(self):
        self.after(0, self.progress.start)
        file = list(self.file)
        try:
            for i, (source, destination, taille) in enumerate(file, 1):
                try:
                    self._etat(f"Déplacement {i}/{len(file)} : {os.path.basename(source)}…")
                    mover.deplacer(source, destination,
                                   progression=lambda m: self._etat(f"{i}/{len(file)} : {m}"))
                    self.historique.ajouter(source, destination, taille,
                                            datetime.now().strftime("%Y-%m-%d %H:%M"))
                except Exception as e:
                    self._erreur(str(e))
            self.file.clear()
            self.after(0, lambda: self.tab_file.delete(*self.tab_file.get_children()))
            self._etat("Terminé.")
        finally:
            self.after(0, self.progress.stop)
            self.after(0, self._rafraichir_historique)
            self.after(0, self._fin_travail)

    def _annuler(self):
        if self._occupe:
            return
        sel = self.tab_hist.selection()
        if not sel:
            return
        index = self.tab_hist.index(sel[0])
        if not messagebox.askyesno("Confirmer l'annulation",
                                   "Ramener ce dossier à son emplacement d'origine ?"):
            return
        self._occupe = True
        self.btn_deplacer.config(state="disabled")
        self.btn_annuler.config(state="disabled")
        threading.Thread(target=self._worker_annuler, args=(index,), daemon=True).start()

    def _worker_annuler(self, index):
        self.after(0, self.progress.start)
        try:
            self.historique.annuler(index, progression=self._etat)
        except Exception as e:
            self._erreur(str(e))
        finally:
            self.after(0, self.progress.stop)
            self.after(0, self._rafraichir_historique)
            self.after(0, self._fin_travail)

    # --- Utilitaires UI ---
    def _rafraichir_historique(self):
        self.tab_hist.delete(*self.tab_hist.get_children())
        for e in self.historique.entrees():
            self.tab_hist.insert("", "end",
                                 values=(e["source"], e["destination"], e["date"]))

    def _etat(self, msg):
        self.after(0, lambda: self.var_etat.set(msg))

    def _erreur(self, msg):
        self.after(0, lambda: messagebox.showerror("hetsi", msg))

    def _fin_travail(self):
        self._occupe = False
        self.btn_deplacer.config(state="normal")
        self.btn_annuler.config(state="normal")

    @staticmethod
    def _go(octets):
        return f"{octets / (1024 ** 3):.2f} Go"


def lancer(chemin_donnees):
    App(chemin_donnees).mainloop()

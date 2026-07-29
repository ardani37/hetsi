# hetsi/gui/app.py
"""Fenêtre principale hetsi : ajouter, file d'attente, historique (CustomTkinter)."""
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

from hetsi.core import diskinfo, mover
from hetsi.core.history import Historique
from hetsi.core.journal import journal

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self, chemin_donnees):
        super().__init__()
        self.title("hetsi")
        self.geometry("900x760")
        self.minsize(760, 600)

        self.historique = Historique(chemin_donnees)
        self.file = []  # liste de (source, destination, taille)
        self._occupe = False
        self._taille_source_chemin = None
        self._taille_source_octets = 0

        self._definir_icone()
        self._construire()
        self._rafraichir_historique()
        self._maj_barre_espace()

    # --- Icône ---
    def _definir_icone(self):
        try:
            racine_paquet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            chemin_ico = os.path.join(racine_paquet, "assets", "hetsi.ico")
            if os.path.exists(chemin_ico):
                self.iconbitmap(chemin_ico)
        except Exception:
            pass

    # --- Construction de l'interface ---
    def _construire(self):
        conteneur = ctk.CTkFrame(self, fg_color="transparent")
        conteneur.pack(fill="both", expand=True, padx=16, pady=16)

        self._construire_entete(conteneur)
        self._construire_barre_espace(conteneur)
        self._construire_nouveau_deplacement(conteneur)
        self._construire_file_attente(conteneur)
        self._construire_historique(conteneur)

    def _construire_entete(self, parent):
        cadre = ctk.CTkFrame(parent, fg_color="transparent")
        cadre.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(cadre, text="🗂  hetsi",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        self.badge_admin = ctk.CTkLabel(
            cadre, text="admin", corner_radius=10,
            fg_color=("#dbeafe", "#1e3a5f"), text_color=("#1d4ed8", "#93c5fd"),
            font=ctk.CTkFont(size=12, weight="bold"), padx=10, pady=2,
        )
        self.badge_admin.pack(side="right")

        self.menu_apparence = ctk.CTkOptionMenu(
            cadre, values=["system", "dark", "light"], width=100,
            command=lambda v: ctk.set_appearance_mode(v),
        )
        self.menu_apparence.pack(side="right", padx=(0, 10))

    def _construire_barre_espace(self, parent):
        carte = ctk.CTkFrame(parent, corner_radius=10)
        carte.pack(fill="x", pady=(0, 12))
        interieur = ctk.CTkFrame(carte, fg_color="transparent")
        interieur.pack(fill="x", padx=16, pady=12)

        ligne = ctk.CTkFrame(interieur, fg_color="transparent")
        ligne.pack(fill="x")
        self.var_espace_titre = tk.StringVar(value="Disque C: — … / …")
        ctk.CTkLabel(ligne, textvariable=self.var_espace_titre,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.var_a_liberer = tk.StringVar(value="")
        ctk.CTkLabel(ligne, textvariable=self.var_a_liberer,
                     text_color=("#15803d", "#4ade80"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="right")

        self.barre_espace = ctk.CTkProgressBar(interieur, height=14)
        self.barre_espace.pack(fill="x", pady=(10, 4))
        self.barre_espace.set(0)

        self.var_espace_caption = tk.StringVar(value="")
        ctk.CTkLabel(interieur, textvariable=self.var_espace_caption,
                     text_color=("gray40", "gray60"),
                     font=ctk.CTkFont(size=11)).pack(anchor="w")

    def _construire_nouveau_deplacement(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(section, text="Nouveau déplacement",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 6))

        cadre = ctk.CTkFrame(section, fg_color="transparent")
        cadre.pack(fill="x")
        cadre.grid_columnconfigure(0, weight=1)
        cadre.grid_columnconfigure(1, weight=0)
        cadre.grid_columnconfigure(2, weight=1)

        # Carte Source
        carte_src = ctk.CTkFrame(cadre, corner_radius=10)
        carte_src.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(carte_src, text="Source", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=14, pady=(12, 4))
        ctk.CTkButton(carte_src, text="Choisir un dossier…",
                      command=self._choisir).pack(anchor="w", padx=14, pady=(0, 6))
        self.var_source = tk.StringVar(value="")
        ctk.CTkLabel(carte_src, textvariable=self.var_source, anchor="w",
                     wraplength=280, justify="left").pack(fill="x", padx=14)
        self.var_source_taille = tk.StringVar(value="")
        ctk.CTkLabel(carte_src, textvariable=self.var_source_taille, anchor="w",
                     text_color=("gray40", "gray60")).pack(fill="x", padx=14, pady=(2, 12))

        # Flèche
        ctk.CTkLabel(cadre, text="→", font=ctk.CTkFont(size=22)).grid(row=0, column=1, padx=6)

        # Carte Cible
        carte_dst = ctk.CTkFrame(cadre, corner_radius=10)
        carte_dst.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(carte_dst, text="Cible", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=14, pady=(12, 4))
        ctk.CTkButton(carte_dst, text="Choisir le dossier cible…",
                      command=self._choisir_cible).pack(anchor="w", padx=14, pady=(0, 6))
        self.var_cible = tk.StringVar(value="")
        ctk.CTkLabel(carte_dst, textvariable=self.var_cible, anchor="w",
                     wraplength=280, justify="left").pack(fill="x", padx=14)
        self.var_cible_libre = tk.StringVar(value="")
        ctk.CTkLabel(carte_dst, textvariable=self.var_cible_libre, anchor="w",
                     text_color=("gray40", "gray60")).pack(fill="x", padx=14, pady=(2, 12))

        pied = ctk.CTkFrame(section, fg_color="transparent")
        pied.pack(fill="x", pady=(8, 0))
        self.var_apercu = tk.StringVar(value="")
        ctk.CTkLabel(pied, textvariable=self.var_apercu,
                     text_color=("gray40", "gray60")).pack(side="left")
        self.btn_ajouter = ctk.CTkButton(pied, text="Ajouter", command=self._ajouter_file)
        self.btn_ajouter.pack(side="right")

    def _construire_file_attente(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="both", expand=True, pady=(0, 12))
        ctk.CTkLabel(section, text="File d'attente",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 6))

        self.liste_file = ctk.CTkScrollableFrame(section, height=160)
        self.liste_file.pack(fill="both", expand=True)
        self.var_file_vide = tk.StringVar(value="Aucun dossier en attente.")
        self.label_file_vide = ctk.CTkLabel(
            self.liste_file, textvariable=self.var_file_vide, text_color=("gray40", "gray60"))
        self.label_file_vide.pack(pady=10)

        pied = ctk.CTkFrame(section, fg_color="transparent")
        pied.pack(fill="x", pady=(8, 0))
        self.var_total_file = tk.StringVar(value="")
        ctk.CTkLabel(pied, textvariable=self.var_total_file).pack(side="left")
        self.btn_deplacer = ctk.CTkButton(pied, text="Tout déplacer",
                                          command=self._tout_deplacer)
        self.btn_deplacer.pack(side="right")

        self.progress = ctk.CTkProgressBar(section, mode="indeterminate")
        self.progress.pack(fill="x", pady=(8, 2))
        self.progress.set(0)

        self.var_etat = tk.StringVar(value="Prêt.")
        ctk.CTkLabel(section, textvariable=self.var_etat,
                     text_color=("gray40", "gray60")).pack(anchor="w")

    def _construire_historique(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="both", expand=True)
        ctk.CTkLabel(section, text="Historique",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 6))

        self.liste_hist = ctk.CTkScrollableFrame(section, height=160)
        self.liste_hist.pack(fill="both", expand=True)
        self.var_hist_vide = tk.StringVar(value="Aucun déplacement effectué.")
        self.label_hist_vide = ctk.CTkLabel(
            self.liste_hist, textvariable=self.var_hist_vide, text_color=("gray40", "gray60"))
        self.label_hist_vide.pack(pady=10)

    # --- Barre d'espace disque ---
    def _maj_barre_espace(self):
        if self.file:
            lecteur = diskinfo.lettre_lecteur(self.file[0][0])
        else:
            lecteur = "C:\\"
        try:
            total, utilise, libre = self._usage_lecteur(lecteur)
        except OSError:
            self.var_espace_titre.set(f"Disque {lecteur} — indisponible")
            self.var_espace_caption.set("")
            self.barre_espace.set(0)
            self.var_a_liberer.set("")
            return

        lettre = lecteur.rstrip("\\")
        self.var_espace_titre.set(
            f"Disque {lettre} — {self._go(utilise)} / {self._go(total)} utilisés")
        fraction = (utilise / total) if total else 0
        self.barre_espace.set(min(max(fraction, 0), 1))
        self.var_espace_caption.set(f"{self._go(libre)} libres sur {lettre}")

        total_a_liberer = sum(taille for _, _, taille in self.file)
        self.var_a_liberer.set(
            f"{self._go(total_a_liberer)} à libérer" if self.file else "")

    @staticmethod
    def _usage_lecteur(lecteur):
        import shutil
        u = shutil.disk_usage(lecteur)
        return u.total, u.used, u.free

    # --- Actions ---
    def _choisir(self):
        dossier = filedialog.askdirectory(title="Choisir le dossier à déplacer")
        if not dossier:
            return
        self.var_source.set(os.path.normpath(dossier))
        self._maj_apercu()

    def _choisir_cible(self):
        dossier = filedialog.askdirectory(title="Choisir le dossier cible")
        if not dossier:
            return
        self.var_cible.set(os.path.normpath(dossier))
        self._maj_apercu()

    def _taille_source_mise_en_cache(self, source):
        """Calcule la taille de `source` une seule fois par chemin, réutilise sinon."""
        if source != self._taille_source_chemin:
            self._taille_source_chemin = source
            self._taille_source_octets = diskinfo.taille_dossier(source) if source else 0
        return self._taille_source_octets

    def _maj_apercu(self):
        source = self.var_source.get()
        cible = self.var_cible.get()
        parts = []
        self.var_source_taille.set("")
        self.var_cible_libre.set("")
        if source:
            taille_txt = f"Taille : {self._go(self._taille_source_mise_en_cache(source))}"
            self.var_source_taille.set(taille_txt)
            parts.append(taille_txt)
        if cible:
            lecteur = diskinfo.lettre_lecteur(cible)
            libre_txt = f"Espace libre sur {lecteur} : {self._go(diskinfo.espace_libre(lecteur))}"
            self.var_cible_libre.set(libre_txt)
            parts.append(libre_txt)
        self.var_apercu.set("   •   ".join(parts))

    def _ajouter_file(self):
        source = self.var_source.get()
        cible = self.var_cible.get()
        if not source or not cible:
            messagebox.showwarning("hetsi", "Choisis un dossier à déplacer et un dossier cible.")
            return
        nom = os.path.basename(source.rstrip("\\"))
        if not nom:
            messagebox.showwarning("hetsi", "Choisis un dossier, pas la racine d'un lecteur.")
            return
        # Destination = <dossier cible>\<nom du logiciel>
        destination = os.path.join(cible, nom)
        src_abs = os.path.abspath(source)
        dst_abs = os.path.abspath(destination)
        if dst_abs == src_abs or dst_abs.startswith(src_abs + os.sep):
            messagebox.showwarning(
                "hetsi", "Le dossier cible ne peut pas être à l'intérieur du dossier à déplacer."
            )
            return
        try:
            mover.valider(source, destination)
        except mover.ErreurDeplacement as e:
            messagebox.showerror("hetsi", str(e))
            return

        taille = self._taille_source_mise_en_cache(source)
        self.file.append((source, destination, taille))
        self._ajouter_ligne_file(len(self.file) - 1, source, destination, taille)
        self.var_source.set("")
        self.var_cible.set("")
        self.var_source_taille.set("")
        self.var_cible_libre.set("")
        self.var_apercu.set("")
        self._maj_barre_espace()

    def _ajouter_ligne_file(self, index, source, destination, taille):
        vide = getattr(self, "label_file_vide", None)
        if vide is not None and vide.winfo_exists():
            vide.pack_forget()

        ligne = ctk.CTkFrame(self.liste_file, corner_radius=8)
        ligne.pack(fill="x", pady=3, padx=2)
        ligne._hetsi_index = index

        nom = os.path.basename(source.rstrip("\\"))
        texte_chemin = f"{self._tronquer(source)}  →  {self._tronquer(destination)}"

        cadre_txt = ctk.CTkFrame(ligne, fg_color="transparent")
        cadre_txt.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        ctk.CTkLabel(cadre_txt, text=nom, font=ctk.CTkFont(weight="bold"),
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(cadre_txt, text=texte_chemin, anchor="w",
                     text_color=("gray40", "gray60"), font=ctk.CTkFont(size=11)).pack(fill="x")

        ctk.CTkLabel(ligne, text=self._go(taille), width=90).pack(side="left", padx=6)

        btn_suppr = ctk.CTkButton(ligne, text="✕", width=28, height=28,
                                  fg_color="transparent", hover_color=("#fee2e2", "#450a0a"),
                                  text_color=("#dc2626", "#f87171"),
                                  command=lambda: self._retirer_file(ligne))
        btn_suppr.pack(side="right", padx=8)
        ligne._hetsi_btn_suppr = btn_suppr

        self._maj_total_file()

    def _retirer_file(self, ligne):
        if self._occupe:
            return
        index = ligne._hetsi_index
        if 0 <= index < len(self.file):
            del self.file[index]
        self._rafraichir_file_widgets()
        self._maj_barre_espace()

    def _rafraichir_file_widgets(self):
        for enfant in list(self.liste_file.winfo_children()):
            enfant.destroy()
        if not self.file:
            self.label_file_vide = ctk.CTkLabel(
                self.liste_file, textvariable=self.var_file_vide,
                text_color=("gray40", "gray60"))
            self.label_file_vide.pack(pady=10)
        else:
            for i, (source, destination, taille) in enumerate(self.file):
                self._ajouter_ligne_file(i, source, destination, taille)
        self._maj_total_file()

    def _maj_total_file(self):
        total = sum(taille for _, _, taille in self.file)
        self.var_total_file.set(
            f"{len(self.file)} dossier(s) — {self._go(total)}" if self.file else "")

    @staticmethod
    def _tronquer(chemin, longueur=36):
        if len(chemin) <= longueur:
            return chemin
        return "…" + chemin[-(longueur - 1):]

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
        self._definir_etat_boutons(disabled=True)
        threading.Thread(target=self._worker_deplacer, daemon=True).start()

    def _worker_deplacer(self):
        self.after(0, self.progress.start)
        file = list(self.file)
        reussis = []
        echoues = []
        try:
            for i, (source, destination, taille) in enumerate(file, 1):
                try:
                    self._etat(f"Déplacement {i}/{len(file)} : {os.path.basename(source)}…")
                    date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    mover.deplacer(
                        source, destination,
                        progression=lambda m, i=i: self._etat(f"{i}/{len(file)} : {m}"),
                        apres_copie=lambda s, d, taille=taille, date=date:
                            self.historique.ajouter(s, d, taille, date),
                    )
                    reussis.append((source, destination, taille))
                except Exception as e:
                    journal().exception("Échec du déplacement de %s vers %s", source, destination)
                    echoues.append((source, destination, taille))
                    self._erreur(f"{os.path.basename(source)} : {e}")

            def _appliquer_resultat():
                reussis_set = {(s, d) for s, d, _ in reussis}
                self.file = [(s, d, t) for s, d, t in self.file if (s, d) not in reussis_set]
                self._rafraichir_file_widgets()
                self._maj_barre_espace()

            self.after(0, _appliquer_resultat)
            self._etat(f"{len(reussis)} réussi(s), {len(echoues)} échoué(s).")
        except Exception:
            journal().exception("Erreur inattendue pendant le déplacement en lot")
            self._erreur("Une erreur inattendue est survenue pendant le déplacement.")
        finally:
            self.after(0, self.progress.stop)
            self.after(0, self._rafraichir_historique)
            self.after(0, self._fin_travail)

    def _annuler(self, index):
        if self._occupe:
            return
        if not messagebox.askyesno("Confirmer l'annulation",
                                   "Ramener ce dossier à son emplacement d'origine ?"):
            return
        self._occupe = True
        self._definir_etat_boutons(disabled=True)
        threading.Thread(target=self._worker_annuler, args=(index,), daemon=True).start()

    def _worker_annuler(self, index):
        self.after(0, self.progress.start)
        try:
            self.historique.annuler(index, progression=self._etat)
        except Exception as e:
            journal().exception("Échec de l'annulation de l'entrée %s", index)
            self._erreur(str(e))
        finally:
            self.after(0, self.progress.stop)
            self.after(0, self._rafraichir_historique)
            self.after(0, self._fin_travail)

    # --- Utilitaires UI ---
    def _rafraichir_historique(self):
        for enfant in list(self.liste_hist.winfo_children()):
            enfant.destroy()

        entrees = self.historique.entrees()
        if not entrees:
            self.label_hist_vide = ctk.CTkLabel(
                self.liste_hist, textvariable=self.var_hist_vide,
                text_color=("gray40", "gray60"))
            self.label_hist_vide.pack(pady=10)
            return

        for i, e in enumerate(entrees):
            ligne = ctk.CTkFrame(self.liste_hist, corner_radius=8)
            ligne.pack(fill="x", pady=3, padx=2)

            nom = os.path.basename(e["source"].rstrip("\\"))
            cadre_txt = ctk.CTkFrame(ligne, fg_color="transparent")
            cadre_txt.pack(side="left", fill="x", expand=True, padx=10, pady=6)
            ctk.CTkLabel(cadre_txt, text=f"{nom}  →  {self._tronquer(e['destination'])}",
                         font=ctk.CTkFont(weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(cadre_txt, text=e.get("date", ""), anchor="w",
                         text_color=("gray40", "gray60"), font=ctk.CTkFont(size=11)).pack(fill="x")

            btn_annuler = ctk.CTkButton(
                ligne, text="Annuler", width=80,
                command=lambda idx=i: self._annuler(idx))
            btn_annuler.pack(side="right", padx=8)
            ligne._hetsi_btn_annuler = btn_annuler

        if self._occupe:
            self._definir_etat_boutons(disabled=True)

    def _etat(self, msg):
        self.after(0, lambda: self.var_etat.set(msg))

    def _erreur(self, msg):
        self.after(0, lambda: messagebox.showerror("hetsi", msg))

    def _definir_etat_boutons(self, disabled):
        etat = "disabled" if disabled else "normal"
        self.btn_deplacer.configure(state=etat)
        self.btn_ajouter.configure(state=etat)
        for enfant in self.liste_file.winfo_children():
            btn = getattr(enfant, "_hetsi_btn_suppr", None)
            if btn is not None:
                btn.configure(state=etat)
        for enfant in self.liste_hist.winfo_children():
            btn = getattr(enfant, "_hetsi_btn_annuler", None)
            if btn is not None:
                btn.configure(state=etat)

    def _fin_travail(self):
        self._occupe = False
        self._definir_etat_boutons(disabled=False)

    @staticmethod
    def _go(octets):
        return f"{octets / (1024 ** 3):.2f} Go"


def lancer(chemin_donnees):
    App(chemin_donnees).mainloop()

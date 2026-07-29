# hetsi

Déplacez vos logiciels d'un lecteur à l'autre pour libérer de l'espace, sans
rien casser. hetsi copie le dossier vers le lecteur cible, vérifie la copie,
puis crée une jonction à l'emplacement d'origine — le logiciel continue de
fonctionner comme si de rien n'était.

## Fonctions

- Déplacement sécurisé (vérification de la copie avant suppression de l'original)
- File d'attente : plusieurs dossiers d'un coup
- Aperçu de la taille du dossier et de l'espace disque
- Historique avec annulation en un clic
- Interface CustomTkinter, mode sombre/clair automatique (suit Windows)

## Téléchargement

Rendez-vous dans les [Releases](https://github.com/ardani37/hetsi/releases) et
téléchargez `hetsi.exe`. Aucune installation requise.

> Au lancement, Windows demande les droits administrateur (nécessaires pour
> déplacer des dossiers de `Program Files` et copier les autorisations).
> Fermez le logiciel concerné avant de déplacer son dossier.

## Développement

```
py -m pip install -r hetsi/requirements.txt pytest pyinstaller
py -m pytest hetsi/
py -m hetsi.run
```

## Licence

MIT

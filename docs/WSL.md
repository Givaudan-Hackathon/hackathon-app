# Retrouver et comprendre le projet dans WSL

WSL permet de faire fonctionner Linux dans Windows. Ubuntu est la distribution
Linux déjà installée sur ce PC. Le projet est placé dans ses fichiers Linux ;
VS Code reste l'interface visible sous Windows et Docker fournit les conteneurs.

## Les chemins

| Vue                                                | Chemin                                                            |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| Copie Windows initiale                             | `C:\Users\Christopher\Desktop\hackathon-app`                      |
| Même copie Windows, vue depuis Ubuntu              | `/mnt/c/Users/Christopher/Desktop/hackathon-app`                  |
| Nouvelle copie Linux, depuis Ubuntu                | `/home/hristopherswl/projets/hackathon-app`                       |
| Nouvelle copie Linux, depuis l'Explorateur Windows | `\\wsl.localhost\Ubuntu\home\hristopherswl\projets\hackathon-app` |

`~` désigne ton répertoire personnel Linux, ici `/home/hristopherswl`.
`~/projets/hackathon-app` est donc un raccourci pour la nouvelle copie.
Un dossier sous `/mnt/c` reste sur le système de fichiers Windows : ouvrir
Ubuntu sans changer de dossier ne suffit pas à effectuer la bascule.

## Ouvrir le dossier

Dans l'Explorateur Windows, coller le chemin commençant par `\\wsl.localhost`
dans la barre d'adresse. Il n'est pas nécessaire de chercher dans les dossiers
internes du disque C où Windows stocke le disque virtuel d'Ubuntu.

Pour travailler, ouvrir Ubuntu depuis le menu Démarrer, puis taper :

```bash
cd ~/projets/hackathon-app
pwd
git status --short --branch
code .
```

VS Code doit indiquer `WSL: Ubuntu`. L'ouverture du dev container sera une étape
supplémentaire : `F1` puis `Dev Containers: Reopen in Container`, une fois sa
configuration disponible sur la branche utilisée.

## Préparation de la copie

Le script `scripts/preparer-wsl.sh` copie le dossier Windows, son historique Git
et ses changements locaux. Il refuse une cible existante et ne supprime rien.
La copie Windows reste disponible. Les deux copies sont ensuite indépendantes :
après la bascule, poursuivre le travail dans le dossier WSL.

La préparation de la copie ne signifie pas que la stack applicative est prête.
Consulter [le suivi](SUIVI-MATIN.md) pour les vérifications réellement effectuées.

Référence : [Microsoft — Stocker les fichiers dans WSL](https://learn.microsoft.com/windows/wsl/filesystems).

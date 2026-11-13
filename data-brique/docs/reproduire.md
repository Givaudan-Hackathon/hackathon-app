# Relancer l'API Data sur son poste (ticket #29)

Guide pour un membre de l'équipe Tech qui veut relancer seul l'API Data (port 8000) et les deux
applis Streamlit de démonstration (ports 8501 et 8502).

Toutes les commandes ci-dessous ont été exécutées le 2026-11-12 sur une **copie neuve** du dépôt
(`git clone`, branche `feature/data-affiner`, commit `569fc85`), sous Windows 11 avec Git Bash.
Les équivalents macOS / Linux sont indiqués, mais n'ont pas été testés.

## 1. Version évaluée et poste de référence

| Élément                 | Valeur                                                                                  |
| ----------------------- | --------------------------------------------------------------------------------------- |
| Branche, commit         | `feature/data-affiner`, `569fc85`                                                       |
| Version du moteur       | `v2.3.0-affiner` (champ `version_modele` de `POST /conversation`)                       |
| `/sante`                | renvoie toujours `baseline-v1` (contrat V1 inchangé)                                    |
| Poste                   | Intel Core i5-13420H (8 cœurs, 12 threads), 15,6 Go de RAM, Windows 11 Pro              |
| GPU                     | aucun utilisé (Intel UHD intégré ; Ollama tourne sur le CPU)                            |
| Python                  | 3.12.10                                                                                 |
| Ollama                  | 0.40.16                                                                                 |
| Modèles (`ollama list`) | `llama3.2:3b` (ID `a80c4f17acd5`, 2,0 Go) ; `bge-m3:latest` (ID `790764642607`, 1,2 Go) |

Temps mesurés sur ce poste (catalogue complet indexé, modèles préchargés) :

| Mesure                                                    | Temps                                       |
| --------------------------------------------------------- | ------------------------------------------- |
| Message entièrement reconnu par les règles                | 0,2 à 1,5 s (médiane 0,95 s sur les 30 cas) |
| Message qui appelle llama3.2:3b (mot inconnu, ex. durian) | 4 à 7 s                                     |
| Démarrage de l'API (modèles et vecteurs préchargés)       | environ 10 s                                |
| Installation des dépendances (`pip install`)              | 2 à 3 min                                   |
| Vecteurs du catalogue complet (8 943 produits)            | 54 min                                      |
| Vecteurs de l'échantillon (1 000 produits Flavors)        | 5,2 min (mesuré sur la copie neuve)         |
| `pytest` (89 tests)                                       | 1 à 1,5 min                                 |
| `benchmark/valider_30_cas.py`                             | environ 3 min                               |

## 2. Prérequis

- **Python 3.12** (testé : 3.12.10). Sous Windows, le lanceur `py -3.12` doit fonctionner.
- **Ollama** 0.40.x, lancé (`http://127.0.0.1:11434`), avec les deux modèles :

  ```bash
  ollama pull llama3.2:3b
  ollama pull bge-m3
  ollama list          # vérifier les ID : llama3.2:3b a80c4f17acd5, bge-m3 790764642607
  ```

  Si Ollama n'est pas lancé, l'API répond quand même, en mode dégradé : règles et TF-IDF, sans
  llama3.2:3b ni bge-m3.

- **RAM :** 8 Go au minimum ; 16 Go conseillés. Les deux modèles occupent environ 4 Go en
  mémoire. Fermer les applications lourdes : des instances d'Orange Data Mining ouvertes ont
  déjà fait échouer bge-m3 (« unable to allocate CPU buffer »).
- **Disque :** environ 5 Go en tout :
  - modèles Ollama : 3,2 Go ;
  - environnement Python : 840 Mo ;
  - données et cache : environ 200 Mo, dont 37 Mo pour les vecteurs du catalogue complet.
- **Windows :** cloner dans un chemin **court** (ex. `C:\Users\<vous>\hackathon-app`). Dans un
  dossier trop profond, `pip install` échoue sur un fichier de `jupyter` (limite de 260
  caractères des chemins Windows). Solution de rechange : activer les chemins longs de Windows.
- **Optionnel :** ngrok, pour exposer l'API au front.

## 3. Installation

```bash
git clone --branch feature/data-affiner https://github.com/Givaudan-Hackathon/hackathon-app.git
cd hackathon-app/data-brique

# Windows (Git Bash ou PowerShell)
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt

# macOS / Linux (non testé)
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Aucun token n'est nécessaire. Ne pas créer de `.env` avec un token ngrok dans le dépôt.

## 4. Données et vecteurs

Les données sont **dans le dépôt** : l'échantillon `data/processed/sample_v1.csv`, le catalogue
Flavors complet `data/processed/catalogue_complet/flavors_catalogue_complet.csv` (8 943
produits) et la banque de références fictives `data/processed/banque_references_demo.csv`.
Aucun téléchargement n'est nécessaire.

Les **vecteurs bge-m3** ne sont pas versionnés (`benchmark/cache/` est ignoré par git). Trois
options :

1. **Catalogue complet (recommandé, c'est la version évaluée) :** environ 1 h, avec reprise si
   le script est interrompu.

   ```bash
   .venv/Scripts/python scripts/indexer_catalogue_complet.py
   ```

   Résultat : `benchmark/cache/bge-m3_complet.npz` (37 Mo). L'API l'utilise automatiquement
   au démarrage suivant.

2. **Repli : échantillon** (1 000 produits Flavors) :

   ```bash
   .venv/Scripts/python -c "from src.moteur_v2 import MoteurV2; MoteurV2().indexer()"
   ```

   Durée : 5,2 min. Résultat : `benchmark/cache/bge-m3.npz` (4 Mo). L'API l'utilise quand les
   vecteurs complets sont absents (testé : `MoteurV22()` choisit alors l'échantillon).

3. **Sans vecteurs :** l'API fonctionne quand même. La recherche passe par le TF-IDF de
   l'échantillon (testé sur la copie neuve : Affiner, pistes, choix et échantillons répondent).
   Les études de marché portent alors sur moins de produits, et les choix proposés par Affiner
   sont moins riches.

Les autres fichiers de `benchmark/cache/` (vecteurs de la banque DEMO, vocabulaire d'arômes) se
créent tout seuls au premier démarrage.

## 5. Lancement

Depuis `data-brique/`, une commande par terminal :

```bash
# API Data (port 8000)
.venv/Scripts/uvicorn api.main:app --host 127.0.0.1 --port 8000

# Appli de test du contrat V2 (port 8501)
.venv/Scripts/streamlit run demo_streamlit.py --server.port 8501 --server.headless true

# Appli « parcours » Givaudan AI Challenge (port 8502)
.venv/Scripts/streamlit run demo_parcours.py --server.port 8502 --server.headless true

# Optionnel : exposer l'API au front (le token ngrok reste sur votre poste)
ngrok http 8000
```

`--server.headless true` évite que Streamlit demande une adresse e-mail dans le terminal au
premier lancement ; ouvrir ensuite http://127.0.0.1:8501 et http://127.0.0.1:8502 dans le
navigateur.

Swagger : http://127.0.0.1:8000/docs. Les deux applis Streamlit appellent l'API sur
`http://127.0.0.1:8000`, ou sur l'adresse donnée dans la variable `API_DATA_URL`.

## 6. Vérifications

```bash
# 1. l'API répond
curl -s http://127.0.0.1:8000/sante
# -> {"statut":"ok","version_modele":"baseline-v1"}

# 2. une conversation : « un yaourt à la fraise » -> etape "affiner" avec des questions
curl -s -X POST http://127.0.0.1:8000/conversation \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @- <<'EOF'
{"session_id": null, "message": "un yaourt à la fraise"}
EOF
# -> "etape":"affiner", "questions":[{"id":"gout", ... "choix":[..., "Je ne sais pas, proposez-moi"]}, ...],
#    "version_modele":"v2.3.0-affiner"

# 3. les tests (89, Ollama conseillé)
.venv/Scripts/python -m pytest -q

# 4. la validation sur les 30 cas de référence (catalogue complet indexé requis pour retrouver 26/30)
.venv/Scripts/python benchmark/valider_30_cas.py
```

**Windows :** un corps JSON avec des accents passé directement en argument de `curl` (`-d
'{"message": "un yaourt à la fraise"}'`) peut être réencodé par Git Bash ou PowerShell, et
l'API répond alors 400. Envoyer le corps depuis un fichier UTF-8 (`--data-binary @corps.json`)
ou depuis l'entrée standard comme ci-dessus. Un front qui utilise `fetch` n'est pas concerné.

## 7. Problèmes connus

| Symptôme                                                     | Cause et solution                                                                                                        |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `pip install` : « No such file or directory … django-stubs » | Chemin trop long sous Windows : cloner plus près de la racine (`C:\Users\<vous>\…`).                                     |
| Réponses lentes (5 s et plus) sur chaque message             | Modèles non préchargés, ou autre programme gourmand en mémoire : attendre le premier message, fermer les applis lourdes. |
| `"version_modele"` correct mais pistes pauvres               | Vecteurs absents : lancer l'indexation (section 4).                                                                      |
| bge-m3 : erreur 500 « unable to allocate CPU buffer »        | Mémoire insuffisante : fermer des applications (ex. Orange Data Mining), relancer Ollama.                                |
| `/sante` répond `baseline-v1`                                | Normal : c'est le contrat V1. La version du moteur V2 est dans `version_modele` de `/conversation`.                      |

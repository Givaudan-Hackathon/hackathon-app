"""Temps par message de la V2.2 sur le parcours boisson + citron vert, avant/apres.

Usage (depuis data-brique/, Ollama lance, rien d'autre ne tournant sur le CPU) :
  .venv/Scripts/python benchmark/mesure_temps_v22.py [chemin_moteur_avant.py]
Le module « avant » (src/moteur_v22.py du commit fea195c, optionnel) est charge depuis un
fichier. Sortie : benchmark/sorties/temps_v22.csv et des tableaux Markdown.
"""
import importlib.util
import sys
import time

import pandas as pd

sys.path.insert(0, ".")
from src.moteur_v22 import AssistantV22, MoteurV22  # noqa: E402

MESSAGES = ["Bonjour", "je voudrais créer une boisson",
            "pétillante, goût citron vert, pas trop sucrée", "elle doit être bio",
            "pourquoi vous proposez cette association ?", "je prends la piste 1",
            "comment je reçois des échantillons ?"]


def chronometrer(nom: str, assistant, **options) -> list[dict]:
    lignes = []
    for message in MESSAGES:
        debut = time.perf_counter()
        assistant.repondre(message, **options)
        lignes.append({"configuration": nom, "message": message,
                       "secondes": round(time.perf_counter() - debut, 3)})
    print(f"{nom} : {sum(l['secondes'] for l in lignes) / len(lignes):.2f} s/message", flush=True)
    return lignes


def markdown(table: pd.DataFrame) -> str:
    entete = [table.index.name or ""] + [str(c) for c in table.columns]
    lignes_md = ["| " + " | ".join(entete) + " |", "|" + "---|" * len(entete)]
    lignes_md += ["| " + " | ".join([str(i)] + [f"{v:.2f}" for v in ligne]) + " |"
                  for i, ligne in zip(table.index, table.to_numpy())]
    return "\n".join(lignes_md)


lignes = []
if len(sys.argv) > 1:
    spec = importlib.util.spec_from_file_location("moteur_v22_avant", sys.argv[1])
    avant = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(avant)
    a = avant.AssistantV22(avant.MoteurV22())
    a.repondre("Bonjour")  # chargement des modeles, hors mesure
    lignes += chronometrer("avant, reformulation (ancien défaut), échantillon",
                           avant.AssistantV22(avant.MoteurV22(), a.noms))
    lignes += chronometrer("avant, rapide, échantillon",
                           avant.AssistantV22(avant.MoteurV22(), a.noms), reformuler=False)
for catalogue in ("echantillon", "complet"):
    debut = time.perf_counter()
    a = AssistantV22(MoteurV22(catalogue=catalogue), prechauffer=True)
    print(f"démarrage après ({catalogue}) : {time.perf_counter() - debut:.1f} s", flush=True)
    lignes += chronometrer(f"après, rapide (défaut), {catalogue}", a)
    if catalogue == "complet":
        a.reinitialiser()
        lignes += chronometrer("après, reformulation, complet", a, reformuler=True)
df = pd.DataFrame(lignes)
df.to_csv("benchmark/sorties/temps_v22.csv", index=False)
resume = df.groupby("configuration", sort=False)["secondes"].agg(["mean", "min", "max", "sum"]).round(2)
resume.columns = ["moyenne (s)", "min (s)", "max (s)", "total (s)"]
print(markdown(resume))
print()
print(markdown(df.pivot(index="message", columns="configuration", values="secondes").reindex(MESSAGES)))

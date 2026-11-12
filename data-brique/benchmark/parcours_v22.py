"""Parcours de reference de la V2.2 : 7 messages, du bonjour a la demande d'echantillons.

Usage (depuis data-brique/, Ollama lance) : .venv/Scripts/python benchmark/parcours_v22.py [-v]
[--rapide] (--rapide : sans reformulation, sortie parcours_v22_rapide.json)
Affiche la conversation (-v : projet et brouillon de chaque tour) et enregistre les reponses dans
benchmark/sorties/parcours_v22.json, verifiees ensuite par tests/test_moteur_v22.py.
"""
import json
import sys
import time

sys.path.insert(0, ".")
from src.moteur_v22 import AssistantV22

PARCOURS = ["Bonjour", "je voudrais créer un dessert",
            "un goût pistache gourmand, pas trop sucré, pour des desserts végétaux",
            "plutôt une crème dessert", "pourquoi la vanille ?", "je prends la piste 2",
            "comment je reçois des échantillons ?"]
verbeux = "-v" in sys.argv
rapide = "--rapide" in sys.argv
a = AssistantV22(reformuler=not rapide)
journal = []
for m in PARCOURS:
    t = time.perf_counter()
    r = a.repondre(m)
    dt = time.perf_counter() - t
    v = r["verification"]
    print(f"\nVous > {m}\n  [intention {r['intention']} (modèle : {r['etapes'].get('intention_llm')}) · "
          f"{dt:.1f} s · texte : {v['source']} · tentatives {v['tentatives']}]")
    for rej in v["rejets"]:
        print("  [REJET]", {k: x for k, x in rej.items() if k != "texte" and x}, "|",
              rej["texte"][:200].replace("\n", " "))
    if verbeux:
        print("  projet:", r["projet"], "| filtres:", r["etapes"].get("filtre_contraintes"))
        print("  BROUILLON:", r["contexte"]["brouillon"].replace("\n", "\n             "))
    print("Bot >", r["texte"].replace("\n", "\n      "))
    if r["demande_echantillons"]:
        print("  RÉCAPITULATIF :", json.dumps(r["demande_echantillons"], ensure_ascii=False))
    journal.append({"message": m, "secondes": round(dt, 1), **{k: r[k] for k in (
        "intention", "texte", "projet", "verification", "etapes", "demande_echantillons")},
        "brouillon": r["contexte"]["brouillon"]})
sortie = f"benchmark/sorties/parcours_v22{'_rapide' if rapide else ''}.json"
json.dump(journal, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
temps = [t["secondes"] for t in journal]
print(f"\nTemps par message : moyenne {sum(temps) / len(temps):.1f} s, min {min(temps)} s, "
      f"max {max(temps)} s, total {sum(temps):.1f} s")

"""Parcours de reference de la V2.2 : boisson + citron vert, et un cas sans reference (durian).

Usage (depuis data-brique/, Ollama lance) :
  .venv/Scripts/python benchmark/parcours_v22.py [-v] [--reformuler] [--echantillon]
Par defaut : mode rapide (sans reformulation), catalogue complet s'il est indexe.
Affiche les conversations (-v : projet et trace de chaque tour) et enregistre les reponses dans
benchmark/sorties/parcours_v22[_reformule].json, verifiees ensuite par tests/test_moteur_v22.py.
"""
import json
import sys
import time

sys.path.insert(0, ".")
from src.moteur_v22 import AssistantV22, MoteurV22  # noqa: E402

PARCOURS = {
    "boisson_citron_vert": ["Bonjour", "je voudrais créer une boisson",
                            "pétillante, goût citron vert, pas trop sucrée", "elle doit être bio",
                            "pourquoi vous proposez cette association ?", "je prends la piste 1",
                            "comment je reçois des échantillons ?"],
    "glace_durian": ["un arôme durian pour une glace"],
}
verbeux = "-v" in sys.argv
reformuler = "--reformuler" in sys.argv
debut = time.perf_counter()
moteur = MoteurV22(catalogue="echantillon" if "--echantillon" in sys.argv else "auto")
assistant = AssistantV22(moteur, reformuler=reformuler)
prechauffage = assistant.prechauffer()
print(f"Démarrage : {time.perf_counter() - debut:.1f} s (catalogue {moteur.catalogue}, "
      f"reformulation {'oui' if reformuler else 'non'}) · {prechauffage}")
journal = []
for nom, messages in PARCOURS.items():
    print(f"\n===== {nom} =====")
    assistant.reinitialiser()
    for m in messages:
        t = time.perf_counter()
        r = assistant.repondre(m)
        dt = time.perf_counter() - t
        v = r["verification"]
        print(f"\nVous > {m}\n  [intention {r['intention']} · modèle appelé : "
              f"{'oui' if r['etapes'].get('modele_appele') else 'non'} · {dt:.2f} s · texte : {v['source']}]")
        for rej in v["rejets"]:
            print("  [REJET]", {k: x for k, x in rej.items() if k != "texte" and x}, "|",
                  rej["texte"][:160].replace("\n", " "))
        if verbeux:
            print("  projet:", r["projet"], "| étapes:", {k: x for k, x in r["etapes"].items()
                                                          if k not in ("intention",)})
        print("Bot >", r["texte"].replace("\n", "\n      "))
        if r["demande_echantillons"]:
            print("  RÉCAPITULATIF :", json.dumps(r["demande_echantillons"], ensure_ascii=False))
        journal.append({"parcours": nom, "message": m, "secondes": round(dt, 2),
                        **{k: r[k] for k in ("intention", "texte", "projet", "pistes", "solutions",
                                              "brief_final", "verification", "etapes",
                                              "demande_echantillons")},
                        "brouillon": r["contexte"]["brouillon"]})
sortie = f"benchmark/sorties/parcours_v22{'_reformule' if reformuler else ''}.json"
json.dump(journal, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
temps = [t["secondes"] for t in journal]
print(f"\nTemps par message ({len(temps)} messages) : moyenne {sum(temps) / len(temps):.2f} s, "
      f"min {min(temps):.2f} s, max {max(temps):.2f} s, total {sum(temps):.1f} s")

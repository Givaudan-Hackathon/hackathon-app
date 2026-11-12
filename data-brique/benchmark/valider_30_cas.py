"""Validation sur les 30 cas de reference (benchmark/cas_reference_30.csv), ecrits avant le test.

Usage (depuis data-brique/, Ollama lance, catalogue complet indexe) :
  .venv/Scripts/python benchmark/valider_30_cas.py
Sorties : benchmark/sorties/validation_30_cas.csv (une ligne par cas) et docs/validation_30_cas.md.
Autre jeu de cas (meme format), sans toucher au rapport des 30 cas :
  .venv/Scripts/python benchmark/valider_30_cas.py --cas benchmark/cas_finaux_10.csv       --sortie benchmark/sorties/validation_cas_finaux.csv
  (rapport ecrit a cote du CSV, meme nom en .md)

Chaque cas est le 1er message d'une nouvelle session :
- V2.2 : AssistantV22, mode rapide (defaut), catalogue complet ;
- V1   : MoteurV1.recommander (division ; arome juge sur les 5 produits recommandes) ;
- V2.1 : MoteurV21.pistes, catalogue complet (division, arome principal, pistes ou relance).
Les criteres sont stricts et fixes avant la mesure (voir docs/validation_30_cas.md).
"""
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from src.moteur_v1 import CATALOGUE_DEFAUT, MoteurV1, normaliser  # noqa: E402
from src.moteur_v2 import (AROMES_FLAVORS, AROMES_FRAGRANCE, CATALOGUE_COMPLET,  # noqa: E402
                           MoteurV21, extraire_aromes)
from src.moteur_v22 import (ADJECTIFS, CONTRAINTES, FEMININ_SINGULIER, MOTS_COURANTS,  # noqa: E402
                            PLURIELS, PROFILS, TYPES, VERSION_V22, AssistantV22, MoteurV22, nombres)

CAS = RACINE / "benchmark" / "cas_reference_30.csv"
SORTIE_CSV = RACINE / "benchmark" / "sorties" / "validation_30_cas.csv"
SORTIE_MD = RACINE / "docs" / "validation_30_cas.md"
# seule equivalence de vocabulaire : les cas ecrivent « vegan », le moteur nomme la contrainte
# « végétal » (elle couvre vegan, vegetal, sans lait)
SYNONYMES = {"vegan": "végétal"}
CATEGORIES = ["boisson_agrumes", "autre_produit", "flou_hors_sujet"]
MARQUEUR = "<!-- analyse manuelle : conservee quand le script regenere ce fichier -->"
PRIX = re.compile(r"\d\s*(?:€|euros?)|\bprix de\b|\bcoute\b", re.I)


def liste(valeur) -> list[str]:
    return [v.strip() for v in str(valeur).split("|") if v.strip()] if isinstance(valeur, str) else []


def comportement_attendu(valeur: str) -> str:
    return valeur.split("(")[0].strip()


def _forme(texte: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", normaliser(texte)))


# vocabulaire du moteur (aromes, types, contraintes, profils, mots des modeles de phrase) : le
# champ « brands » d'Open Food Facts contient aussi ces mots generiques (« Fruité », « Vanille »,
# « Cola », « Aucun »...), qui ne sont pas des marques dans une reponse du bot
VOCABULAIRE = {_forme(m) for m in [*AROMES_FLAVORS, *AROMES_FRAGRANCE, *TYPES, *PLURIELS.values(),
                                   *CONTRAINTES, *ADJECTIFS.values(), *PROFILS,
                                   *FEMININ_SINGULIER.values(), "vegan", "aucun", "aucune"]}


class Marques:
    """Marques du catalogue (mot a mot), pour verifier qu'aucune n'apparait dans une reponse.
    Une « marque » identique a un mot du vocabulaire du moteur est ignoree (liste : ignorees)."""

    def __init__(self):
        brands = pd.concat([pd.read_csv(c, dtype=str, usecols=["brands"])["brands"]
                            for c in (CATALOGUE_DEFAUT, CATALOGUE_COMPLET)]).dropna()
        formes = {_forme(m) for b in brands for m in b.split(",") if len(m.strip()) > 3}
        self.ignorees = sorted(f for f in formes if f in VOCABULAIRE or f in MOTS_COURANTS)
        self.formes = {f for f in formes if f and f not in VOCABULAIRE and f not in MOTS_COURANTS}

    def trouvees(self, texte: str) -> list[str]:
        texte = f" {' '.join(re.findall(r'[a-z0-9]+', normaliser(texte)))} "
        return sorted(f for f in self.formes if f" {f} " in texte)


def entiers(objet) -> set[str]:
    """Tous les entiers d'une structure (donnees de l'etude de marche)."""
    if isinstance(objet, bool):
        return set()
    if isinstance(objet, (int, float)):
        return {str(int(objet))} if float(objet).is_integer() else set()
    if isinstance(objet, dict):
        return set().union(*(entiers(v) for v in objet.values())) if objet else set()
    if isinstance(objet, (list, tuple)):
        return set().union(*(entiers(v) for v in objet)) if objet else set()
    return set()


def comportement_v22(r: dict) -> set[str]:
    if r["etape"] == "pistes":
        obtenus = {"pistes"}
        if r["pistes"] and r["compris"]["arome"] in r["pistes"][0]["sans_reference"]:
            obtenus.add("creation_sur_mesure")
        return obtenus
    if r["intention"] in ("hors_sujet", "question"):
        return {r["intention"]}
    return {"relance"}


def valider(chemin: Path = CAS) -> pd.DataFrame:
    cas = pd.read_csv(chemin, dtype=str)
    marques = Marques()
    moteur = MoteurV22(catalogue="complet")
    assistant = AssistantV22(moteur, prechauffer=True)
    v1 = MoteurV1()
    v21 = MoteurV21(catalogue="complet")
    v21.pistes("échauffement : boisson au citron")  # chargement des modeles, hors mesure
    lignes = []
    for c in cas.itertuples():
        type_att, aromes_att = c.type_produit_attendu, liste(c.arome_attendu)
        contraintes_att = {SYNONYMES.get(x, x) for x in liste(c.contraintes_attendues)}
        comp_att = comportement_attendu(c.comportement_attendu)
        division_att = None if c.categorie == "flou_hors_sujet" else "flavors"

        # --- V2.2 ---
        assistant.reinitialiser()
        assistant.historique = []
        debut = time.perf_counter()
        r = assistant.repondre(c.phrase_client)
        secondes = time.perf_counter() - debut
        compris, texte = r["compris"], r["texte"]
        # etape Affiner (V2.3) : le front affiche une question ; la mesure clique « Je ne sais pas,
        # proposez-moi » et juge le comportement sur la reponse suivante (pistes)
        affiner = r["etape"] == "affiner"
        r_comportement = assistant.repondre("Je ne sais pas, proposez-moi") if affiner else r
        texte_suite = r_comportement["texte"] if affiner else ""
        obtenus = comportement_v22(r_comportement)
        aromes_obt = compris["aromes"]
        # chiffres : chaque nombre de la reponse vient des donnees de l'etude de marche, des
        # numeros de piste ou du message du client
        marche = (assistant.etude or {}).get("marche") or {}
        source = (entiers(marche) | nombres(json.dumps(marche, ensure_ascii=False))
                  | {"1", "2", "3"} | nombres(c.phrase_client))
        chiffres_inventes = sorted(nombres(f"{texte} {texte_suite}") - source)
        marques_citees = marques.trouvees(f"{texte} {texte_suite}")
        ligne = {
            "id": c.id, "categorie": c.categorie, "phrase_client": c.phrase_client,
            "type_attendu": type_att if isinstance(type_att, str) else "",
            "type_obtenu": compris["type_produit"] or "",
            "aromes_attendus": "|".join(aromes_att), "aromes_obtenus": "|".join(aromes_obt),
            "contraintes_attendues": "|".join(sorted(contraintes_att)),
            "contraintes_obtenues": "|".join(sorted(compris["contraintes"])),
            "comportement_attendu": c.comportement_attendu,
            "comportement_obtenu": "|".join(sorted(obtenus)),
            "etape": r["etape"], "intention": r["intention"], "passe_par_affiner": affiner,
            "type_ok": (compris["type_produit"] or "") == (type_att if isinstance(type_att, str) else ""),
            "arome_principal_ok": (compris["arome"] in aromes_att) if aromes_att else compris["arome"] is None,
            "aromes_ok": set(aromes_att) <= set(aromes_obt) and (bool(aromes_att) or not aromes_obt),
            "contraintes_ok": set(compris["contraintes"]) == contraintes_att,
            "comportement_ok": comp_att in obtenus,
            "division_ok": compris["division"] == division_att,
            "sans_marque": not marques_citees, "marques_citees": "|".join(marques_citees),
            "sans_chiffre_invente": not chiffres_inventes,
            "chiffres_inventes": "|".join(chiffres_inventes),
            "sans_prix": not PRIX.search(f"{texte} {texte_suite}"),
            "modele_appele": r["etapes"].get("modele_appele", False),
            "secondes": round(secondes, 3),
            "reponse": texte + (f"\n[après « Je ne sais pas, proposez-moi »] {texte_suite}" if affiner else ""),
        }
        ligne["cas_reussi"] = all(ligne[k] for k in ("type_ok", "aromes_ok", "contraintes_ok",
                                                     "comportement_ok", "sans_marque",
                                                     "sans_chiffre_invente", "sans_prix"))

        # --- V1 : division ; arome juge sur les 5 produits recommandes ---
        resultat_v1 = v1.recommander(c.phrase_client)
        aromes_top = set()
        for _, produit in resultat_v1["top"].iterrows():
            aromes_top |= set(extraire_aromes(str(produit["product_name"])))
        ligne["v1_division"] = resultat_v1["division"]
        ligne["v1_division_ok"] = (resultat_v1["division"] == division_att) if division_att else \
            resultat_v1["division"] == "indeterminee"
        ligne["v1_arome_top5_ok"] = (set(aromes_att) <= aromes_top) if aromes_att else None

        # --- V2.1 : division, arome principal, pistes ou relance ---
        debut = time.perf_counter()
        resultat_v21 = v21.pistes(c.phrase_client)
        ligne["v21_secondes"] = round(time.perf_counter() - debut, 3)
        division_v21 = None if resultat_v21["division"] == "indeterminee" else resultat_v21["division"]
        ligne["v21_division_ok"] = division_v21 == division_att
        ligne["v21_arome"] = resultat_v21["arome"] or ""
        ligne["v21_arome_principal_ok"] = (resultat_v21["arome"] in aromes_att) if aromes_att else \
            resultat_v21["arome"] is None
        mode_v21 = "relance" if resultat_v21["mode"] == "relance" else "pistes"
        ligne["v21_comportement"] = mode_v21
        ligne["v21_comportement_ok"] = (mode_v21 == comp_att) if comp_att in ("pistes", "relance") else None
        ligne["v22_comparable_ok"] = (comp_att in obtenus) if comp_att in ("pistes", "relance") else None
        ligne["v21_sans_marque"] = not marques.trouvees(" ".join(p["explication"] for p in resultat_v21["pistes"]))
        lignes.append(ligne)
        print(f"{c.id} {'OK ' if ligne['cas_reussi'] else 'ECHEC'} {secondes:5.2f} s · "
              f"type {ligne['type_obtenu'] or '—'} · aromes {ligne['aromes_obtenus'] or '—'} · "
              f"contraintes {ligne['contraintes_obtenues'] or '—'} · {ligne['comportement_obtenu']}",
              flush=True)
    return pd.DataFrame(lignes)


def taux(serie: pd.Series) -> str:
    serie = serie.dropna().astype(bool)
    return f"{serie.sum()}/{len(serie)} ({serie.mean():.0%})" if len(serie) else "—"


AVANT = RACINE / "benchmark" / "sorties" / "validation_30_cas_avant.csv"


def avant_apres(df: pd.DataFrame) -> list[str]:
    """Tableau AVANT (V2.2.2, mesure du 2026-11-12 avant correction) / APRES (cette mesure)."""
    if not AVANT.exists() or set(df.id) != set(pd.read_csv(AVANT).id):
        return []
    avant = pd.read_csv(AVANT)
    lignes = ["", "## Avant / après les corrections par mécanismes", "",
              "| Critère | Avant (V2.2.2) | Après (" + VERSION_V22 + ") |", "|---|---|---|"]
    for cle, nom in [("type_ok", "Type de produit"), ("aromes_ok", "Arôme(s), tous trouvés"),
                     ("arome_principal_ok", "Arôme principal"), ("contraintes_ok", "Contraintes"),
                     ("comportement_ok", "Comportement"), ("sans_marque", "Aucune marque"),
                     ("sans_chiffre_invente", "Aucun chiffre inventé"), ("sans_prix", "Aucun prix inventé"),
                     ("cas_reussi", "**Cas entièrement réussi**")]:
        lignes.append(f"| {nom} | {taux(avant[cle])} | {taux(df[cle])} |")
    for cat in CATEGORIES:
        lignes.append(f"| Cas réussis — {cat} | {taux(avant[avant.categorie == cat].cas_reussi)} | "
                      f"{taux(df[df.categorie == cat].cas_reussi)} |")
    lignes.append(f"| Temps moyen par cas | {avant.secondes.mean():.2f} s | {df.secondes.mean():.2f} s |")
    lignes.append(f"| Temps médian par cas | {avant.secondes.median():.2f} s | {df.secondes.median():.2f} s |")
    gagnes = sorted(set(df[df.cas_reussi].id) - set(avant[avant.cas_reussi].id))
    perdus = sorted(set(avant[avant.cas_reussi].id) - set(df[df.cas_reussi].id))
    lignes += ["", f"Cas gagnés : {', '.join(gagnes) or 'aucun'}. Cas perdus : {', '.join(perdus) or 'aucun'}."]
    return lignes


def rapport(df: pd.DataFrame, ignorees: list[str], titre: str = "les 30 cas de référence") -> str:
    CATEGORIES = list(dict.fromkeys(df.categorie))  # noqa: N806 (categories du jeu de cas)
    criteres = [("type_ok", "Type de produit"), ("aromes_ok", "Arôme(s), tous trouvés"),
                ("arome_principal_ok", "Arôme principal"), ("contraintes_ok", "Contraintes (égalité stricte)"),
                ("comportement_ok", "Comportement"), ("sans_marque", "Aucune marque citée"),
                ("sans_chiffre_invente", "Aucun chiffre inventé"), ("sans_prix", "Aucun prix inventé"),
                ("cas_reussi", "**Cas entièrement réussi**")]
    l = [f"# Validation sur {titre} (V2.2, `{VERSION_V22}`)", "",
         f"Mesure du {date.today().isoformat()}. Les cas (`benchmark/cas_reference_30.csv`) ont été "
         "écrits avant le test et n'ont pas été modifiés. Le résultat **avant correction** (V2.2.2, "
         "18/30) est conservé dans `benchmark/sorties/validation_30_cas_avant.csv`.",
         *avant_apres(df),
         "", "## Méthode", "",
         "- Chaque cas est le **premier message d'une nouvelle session**.",
         "- V2.2 : `AssistantV22` en mode rapide (défaut), catalogue Flavors complet (8 943 "
         "produits), modèles préchargés. Script : `benchmark/valider_30_cas.py`.",
         "- **Type** : `compris.type_produit` égal au type attendu (vide attendu → aucun type).",
         "- **Arôme(s)** : tous les arômes attendus figurent dans `compris.aromes` ; aucun attendu "
         "→ aucun arôme. L'arôme principal (`compris.arome`) est aussi mesuré à part.",
         "- **Contraintes** : égalité stricte des ensembles. Seule équivalence : « vegan » des cas = "
         "contrainte « végétal » du moteur. Une contrainte en trop (ex. « pour enfants ») est un échec.",
         "- **Comportement** : `pistes` si `etape = pistes` ; `creation_sur_mesure` si, en plus, "
         "l'arôme principal n'a aucune référence DEMO ; `hors_sujet` ou `question` selon "
         "`intention` ; sinon `relance`.",
         "- **Aucune marque** : aucune marque du catalogue (mot à mot) dans la réponse, y compris "
         "une marque citée par le client (ex. « Coca-Cola », 153 produits au catalogue). Le champ "
         "`brands` d'Open Food Facts contient aussi des mots génériques : une « marque » identique "
         "au vocabulaire du moteur (arôme, type, contrainte, profil) est ignorée. Formes ignorées "
         f"présentes au catalogue : {', '.join(f'« {f} »' for f in ignorees)}.",
         "- **Aucun chiffre inventé** : chaque nombre de la réponse vient des données de l'étude de "
         "marché (comptages), d'un numéro de piste ou du message du client. **Aucun prix** : ni "
         "« € », ni « euros », ni « prix de ».",
         "- **Cas réussi** : tous les critères ci-dessus à la fois.",
         "- **Étape Affiner (V2.3)** : quand le 1er message donne `etape = affiner` (type et arôme "
         "connus, aucun profil), la mesure répond « Je ne sais pas, proposez-moi », comme le bouton "
         "du front. Le comportement est jugé sur cette 2e réponse. Type, arômes et contraintes "
         "sont jugés sur la 1re. Marques, chiffres et prix sont contrôlés dans les deux textes. "
         "Les cas n'ont pas été modifiés.",
         "- **V1** (`MoteurV1`) : division ; l'arôme est jugé sur les 5 produits recommandés (tous "
         "les arômes attendus présents dans leurs noms), car V1 n'extrait pas d'arôme.",
         "- **V2.1** (`MoteurV21.pistes`, catalogue complet) : division, arôme principal, pistes ou "
         "relance. V2.1 n'a ni type de produit, ni contraintes, ni intention `hors_sujet` / "
         "`question`, ni références : ces critères ne sont pas comparables.",
         "", "## Résultats V2.2", "",
         "| Critère | Global | " + " | ".join(CATEGORIES) + " |",
         "|---|---|" + "---|" * len(CATEGORIES)]
    for cle, nom in criteres:
        l.append(f"| {nom} | {taux(df[cle])} | "
                 + " | ".join(taux(df[df.categorie == cat][cle]) for cat in CATEGORIES) + " |")
    t = df["secondes"]
    l += ["", f"Temps de réponse V2.2 : moyenne {t.mean():.2f} s, médiane {t.median():.2f} s, "
          f"max {t.max():.2f} s ; modèle appelé pour {int(df.modele_appele.sum())} cas sur {len(df)} "
          f"(moyenne {df[df.modele_appele].secondes.mean():.2f} s ces fois-là, "
          f"{df[~df.modele_appele].secondes.mean():.2f} s sinon).", "",
          "## Comparaison V1 / V2.1 / V2.2", "",
          "| Critère comparable | V1 | V2.1 | V2.2 |", "|---|---|---|---|",
          f"| Division (flavors, ou aucune pour les cas flous) | {taux(df.v1_division_ok)} | "
          f"{taux(df.v21_division_ok)} | {taux(df.division_ok)} |",
          f"| Arôme principal | — | {taux(df.v21_arome_principal_ok)} | {taux(df.arome_principal_ok)} |",
          f"| Arôme(s) attendus dans les 5 produits recommandés (V1) | {taux(df.v1_arome_top5_ok)} | — | — |",
          f"| Pistes ou relance, cas qui l'attendent | — | {taux(df.v21_comportement_ok)} | "
          f"{taux(df.v22_comparable_ok)} |",
          f"| Aucune marque citée | (produits du commerce : non) | {taux(df.v21_sans_marque)} | "
          f"{taux(df.sans_marque)} |",
          f"| Temps moyen par cas | < 0,1 s | {df.v21_secondes.mean():.2f} s | {t.mean():.2f} s |",
          "", "## Échecs (réponse obtenue)", ""]
    for _, e in df[~df.cas_reussi].iterrows():
        raisons = [nom for cle, nom in criteres[:-1] if cle != "arome_principal_ok" and not e[cle]]
        l += [f"### {e['id']} — « {e['phrase_client']} »", "",
              f"- Échec : {', '.join(raisons)}",
              f"- Attendu : type `{e['type_attendu'] or '—'}`, arômes `{e['aromes_attendus'] or '—'}`, "
              f"contraintes `{e['contraintes_attendues'] or '—'}`, comportement `{e['comportement_attendu']}`",
              f"- Obtenu : type `{e['type_obtenu'] or '—'}`, arômes `{e['aromes_obtenus'] or '—'}`, "
              f"contraintes `{e['contraintes_obtenues'] or '—'}`, comportement `{e['comportement_obtenu']}` "
              f"(etape `{e['etape']}`, intention `{e['intention']}`)"
              + (f", marques citées : {e['marques_citees']}" if e["marques_citees"] else "")
              + (f", chiffres non sourcés : {e['chiffres_inventes']}" if e["chiffres_inventes"] else ""),
              "- Réponse :", "", "> " + e["reponse"].replace("\n", "\n> "), ""]
    l += ["## Limites de la mesure", "",
          "- 30 cas courts, un seul message chacun : la conversation (précisions, retraits, choix) "
          "est couverte par les tests pytest, pas par cette validation.",
          "- Critères stricts écrits avant la mesure : un type absent de la liste du moteur "
          "(« snack salé », « biscuit ») ou une contrainte en trop compte comme un échec, même si "
          "la réponse reste utile.",
          "- Le contrôle « aucun chiffre inventé » vérifie la provenance des nombres, pas leur "
          "interprétation dans la phrase.",
          "- Le contrôle des marques porte sur les marques du catalogue Open Food Facts : une marque "
          "absente du catalogue ne serait pas détectée.",
          "- V2.1 et V2.2 dépendent d'Ollama (llama3.2:3b, bge-m3) ; résultats obtenus à "
          "température 0, sur le CPU de l'équipe.", ""]
    return "\n".join(l)


if __name__ == "__main__":
    for flux in (sys.stdout,):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")
    import argparse
    options = argparse.ArgumentParser()
    options.add_argument("--cas", type=Path, help="autre fichier de cas (meme format)")
    options.add_argument("--sortie", type=Path, help="CSV de sortie pour --cas")
    arguments = options.parse_args()
    if arguments.cas:
        resultats = valider(arguments.cas)
        sortie = arguments.sortie or SORTIE_CSV.with_name(f"validation_{arguments.cas.stem}.csv")
        resultats.to_csv(sortie, index=False)
        sortie.with_suffix(".md").write_text(
            rapport(resultats, Marques().ignorees, f"{len(resultats)} cas jamais vus ({arguments.cas.name})"),
            encoding="utf-8")
        print(f"\nCas réussis : {resultats.cas_reussi.sum()}/{len(resultats)} -> {sortie.name}")
        sys.exit(0)
    resultats = valider()
    SORTIE_CSV.parent.mkdir(parents=True, exist_ok=True)
    resultats.to_csv(SORTIE_CSV, index=False)
    # l'analyse ecrite a la main apres le marqueur est conservee d'une execution a l'autre
    manuel = ""
    if SORTIE_MD.exists() and MARQUEUR in SORTIE_MD.read_text(encoding="utf-8"):
        manuel = SORTIE_MD.read_text(encoding="utf-8").split(MARQUEUR, 1)[1]
    SORTIE_MD.write_text(rapport(resultats, Marques().ignorees) + "\n" + MARQUEUR + manuel,
                         encoding="utf-8")
    print(f"\nCas réussis : {resultats.cas_reussi.sum()}/30 -> {SORTIE_CSV.name}, {SORTIE_MD.name}")

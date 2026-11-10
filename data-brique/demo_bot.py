"""Bot de demo du moteur V2 dans le terminal.

Usage (depuis data-brique/, venv active, Ollama lance) : python demo_bot.py
Ecrire une demande comme une cliente ; ligne vide, « quitter » ou Ctrl+C pour sortir.
Option : python demo_bot.py --complet (catalogue Flavors complet, vecteurs a calculer avant).
"""
import sys
import textwrap
import time

from src.moteur_v2 import MODELE_EMBEDDING, MODELE_LLM, MoteurV2

ATTRIBUTION = "Contient des données d'Open Food Facts / Open Beauty Facts, licence ODbL"
DIVISIONS = {"flavors": "Flavors (arômes alimentaires)", "fragrance": "Fragrance (parfums)",
             "indeterminee": "indéterminée"}
MODES = {"v2": "", "v2_partiel": "  [bge-m3 indisponible : recherche TF-IDF V1]",
         "repli_v1": "  [Ollama indisponible : mode secours V1, mots-clés + TF-IDF]"}
SORTIES = {"", "q", "quit", "quitter", "exit", "au revoir"}


def _couper(texte, largeur: int) -> str:
    texte = "" if texte is None or texte != texte else str(texte)  # NaN -> ""
    return texte if len(texte) <= largeur else texte[:largeur - 1] + "…"


def afficher(resultat: dict, secondes: float) -> None:
    arome = resultat["arome"] or "non identifié"
    print(f"\n  J'ai compris : division {DIVISIONS[resultat['division']]}, arôme principal : {arome}"
          f"{MODES[resultat['mode']]}")
    print(f"  Voici {len(resultat['top'])} produits proches de votre demande ({secondes:.1f} s) :\n")
    print(f"  {'#':>2}  {'Produit':<44} {'Marque':<20} {'Catégorie':<22} {'Score':>5}")
    for rang, p in enumerate(resultat["top"].itertuples(), 1):
        print(f"  {rang:>2}  {_couper(p.product_name, 44):<44} {_couper(p.brands, 20):<20} "
              f"{_couper(p.query_category, 22):<22} {p.score:>5.2f}")
    print()


def main() -> None:
    for flux in (sys.stdin, sys.stdout):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")
    catalogue = "complet" if "--complet" in sys.argv else "echantillon"
    print("Chargement du moteur V2…")
    moteur = MoteurV2(catalogue=catalogue)
    print(textwrap.dedent(f"""
        Bonjour ! Décrivez votre projet avec vos mots, par exemple :
          « un goût pistache gourmand, pas trop sucré, pour des desserts végétaux »
        Je vous propose 5 produits du marché proches de votre idée.
        (compréhension : {MODELE_LLM}, recherche : {MODELE_EMBEDDING} sur le catalogue {catalogue})
        Ligne vide ou « quitter » pour sortir.
        {ATTRIBUTION}"""))
    while True:
        try:
            brief = input("Vous > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if brief.lower() in SORTIES:
            break
        if len(brief) < 3:
            print("  Pouvez-vous en dire un peu plus ?\n")
            continue
        debut = time.perf_counter()
        resultat = moteur.recommander(brief, k=5)
        afficher(resultat, time.perf_counter() - debut)
    print("À bientôt !")


if __name__ == "__main__":
    main()

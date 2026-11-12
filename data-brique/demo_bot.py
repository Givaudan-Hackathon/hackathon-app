"""Bot de demo du moteur V2.1 dans le terminal : pistes d'aromes, sans produit ni marque.

Usage (depuis data-brique/, venv active, Ollama lance) : python demo_bot.py
Ecrire une demande comme une cliente ; une reponse courte (« plutot fruite ») complete la
demande precedente ; « nouvelle demande » repart de zero ; ligne vide, « quitter » ou Ctrl+C
pour sortir.
Option : python demo_bot.py --complet (catalogue Flavors complet, vecteurs a calculer avant).

Les produits du marche proches de la demande servent d'etude de marche interne : le bot n'en
affiche ni le nom ni la marque, seulement les aromes et le nombre de produits qui les utilisent.
"""
import sys
import textwrap
import time

from src.moteur_v2 import MODELE_EMBEDDING, MODELE_LLM, N_MARCHE, Conversation, MoteurV21

ATTRIBUTION = "Étude de marché réalisée sur des données d'Open Food Facts / Open Beauty Facts (ODbL)"
DIVISIONS = {"flavors": "un arôme alimentaire", "fragrance": "un parfum"}
MODES = {"v2.1": "", "repli_v1": "  [Ollama indisponible : mode secours, mots-clés]"}
TITRES = {"principal": "Piste 1 · L'arôme seul",
          "association_frequente": "Piste 2 · L'association la plus courante",
          "association_originale": "Piste 3 · L'association originale"}
SORTIES = {"", "q", "quit", "quitter", "exit", "au revoir"}
NOUVELLE = {"nouvelle demande", "nouvelle", "recommencer"}


def afficher(resultat: dict, secondes: float) -> None:
    if resultat["complement"]:
        print(f"\n  (je complète votre demande : « {resultat['brief']} »)")
    if resultat["mode"] == "relance":
        print("\n  Je n'ai pas encore assez d'éléments pour vous proposer des arômes.\n"
              f"  {resultat['question']}\n")
        return
    produit = f" (produit : {resultat['application']})" if resultat["application"] else ""
    print(f"\n  J'ai compris : vous cherchez {DIVISIONS[resultat['division']]} autour de "
          f"« {resultat['arome']} »{produit}.{MODES[resultat['mode']]}")
    print(f"  J'ai étudié les {resultat['marche']['nb_produits_analyses']} produits du marché les "
          f"plus proches de votre projet ({secondes:.1f} s). Voici mes pistes :\n")
    for piste in resultat["pistes"]:
        print(f"  {TITRES[piste['type']]} : {' + '.join(piste['aromes'])}")
        for ligne in textwrap.wrap(piste["explication"], 86):
            print(f"      {ligne}")
        print()
    if len(resultat["pistes"]) < 3:
        print("  (pas assez de produits proches pour proposer d'autres associations)\n")
    if resultat["question"]:
        print(f"  Pour affiner : {resultat['question']}\n")


def main() -> None:
    for flux in (sys.stdin, sys.stdout):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")
    catalogue = "complet" if "--complet" in sys.argv else "echantillon"
    print("Chargement du moteur V2.1…")
    moteur = MoteurV21(catalogue=catalogue)
    conversation = Conversation(moteur, moteur.pistes)
    print(textwrap.dedent(f"""
        Bonjour ! Décrivez le produit que vous voulez créer, avec vos mots, par exemple :
          « un goût pistache gourmand, pas trop sucré, pour des desserts végétaux »
        Je vous propose 3 pistes d'arômes, à partir d'une étude des {N_MARCHE} produits du marché
        les plus proches de votre idée. Vous pouvez ensuite préciser (« plutôt fruité »).
        (compréhension : {MODELE_LLM}, étude de marché : {MODELE_EMBEDDING}, catalogue {catalogue})
        « nouvelle demande » pour repartir de zéro, ligne vide ou « quitter » pour sortir.
        {ATTRIBUTION}"""))
    while True:
        try:
            message = input("Vous > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in SORTIES:
            break
        if message.lower() in NOUVELLE:
            conversation.reinitialiser()
            print("  D'accord, je vous écoute : quel est votre nouveau projet ?\n")
            continue
        if len(message) < 3:
            print("  Pouvez-vous en dire un peu plus ?\n")
            continue
        debut = time.perf_counter()
        resultat = conversation.repondre(message)
        afficher(resultat, time.perf_counter() - debut)
    print("À bientôt !")


if __name__ == "__main__":
    main()

"""Bot de demo du moteur V2.2 dans le terminal : assistant conversationnel (RAG), sans produit
ni marque.

Usage (depuis data-brique/, venv active, Ollama lance) : python demo_bot_v22.py
Le bot comprend les precisions (« plutot une creme dessert »), repond aux questions sur les
pistes (« pourquoi la vanille ? »), enregistre le choix d'une piste (« je prends la piste 2 ») et
prepare un recapitulatif de demande d'echantillons (rien n'est envoye).
« nouvelle demande » repart de zero ; ligne vide, « quitter » ou Ctrl+C pour sortir.
Options : --complet (catalogue Flavors complet, vecteurs a calculer avant) ; --trace (intention,
source du texte et rejets des garde-fous) ; --rapide (pas de reformulation : le bot affiche le
brouillon factuel, environ deux fois plus vite).
Le bot V2.1 (pistes affichees telles quelles) reste disponible : python demo_bot.py
"""
import sys
import textwrap
import time

from src.moteur_v2 import MODELE_EMBEDDING, MODELE_LLM
from src.moteur_v22 import AssistantV22, MoteurV22

ATTRIBUTION = "Étude de marché réalisée sur des données d'Open Food Facts / Open Beauty Facts (ODbL)"
SORTIES = {"", "q", "quit", "quitter", "exit", "au revoir"}
NOUVELLE = {"nouvelle demande", "nouvelle", "recommencer"}
CHAMPS = [("type_de_produit", "Type de produit"), ("division", "Division"), ("piste", "Piste"),
          ("aromes", "Arômes"), ("profil", "Profil"), ("contraintes", "Contraintes"),
          ("brief_du_client", "Brief du client"), ("date", "Date"), ("statut", "Statut")]


def afficher(resultat: dict, secondes: float, trace: bool) -> None:
    print()
    for paragraphe in resultat["texte"].split("\n"):
        for ligne in textwrap.wrap(paragraphe, 90) or [""]:
            print(f"  {ligne}")
    demande = resultat["demande_echantillons"]
    if demande:
        print("\n  ┌─ Demande d'échantillons (récapitulatif) " + "─" * 30)
        for cle, libelle in CHAMPS:
            valeur = demande.get(cle)
            if isinstance(valeur, list):
                valeur = ", ".join(valeur) or "—"
            for i, ligne in enumerate(textwrap.wrap(f"{libelle} : {valeur}", 80)):
                print(f"  │ {'' if i == 0 else '  '}{ligne}")
        print("  └" + "─" * 71)
    if trace:
        v = resultat["verification"]
        print(f"\n  [intention {resultat['intention']} (modèle : {resultat['etapes'].get('intention_llm')})"
              f" · texte : {v['source']} · {secondes:.1f} s]")
        for rejet in v["rejets"]:
            print("  [rejeté]", {k: x for k, x in rejet.items() if k != "texte" and x})
    print()


def main() -> None:
    for flux in (sys.stdin, sys.stdout):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")
    catalogue = "complet" if "--complet" in sys.argv else "echantillon"
    trace = "--trace" in sys.argv
    rapide = "--rapide" in sys.argv
    print("Chargement de l'assistant V2.2…")
    assistant = AssistantV22(MoteurV22(catalogue=catalogue), reformuler=not rapide)
    print(textwrap.dedent(f"""
        Bonjour ! Je suis l'assistant arômes. Parlez-moi de votre projet avec vos mots, par exemple :
          « un goût pistache gourmand, pas trop sucré, pour des desserts végétaux »
        Je vous propose des pistes d'arômes à partir d'une étude des produits du marché les plus
        proches de votre idée. Vous pouvez préciser, me poser des questions, choisir une piste et
        préparer une demande d'échantillons.
        (modèle : {MODELE_LLM}, étude de marché : {MODELE_EMBEDDING}, catalogue {catalogue}{", mode rapide" if rapide else ""})
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
            assistant.reinitialiser()
            print("  D'accord, je vous écoute : quel est votre nouveau projet ?\n")
            continue
        debut = time.perf_counter()
        resultat = assistant.repondre(message)
        afficher(resultat, time.perf_counter() - debut, trace)
    print("À bientôt !")


if __name__ == "__main__":
    main()

"""Bot de demo du moteur V2.2 dans le terminal : assistant conversationnel (RAG), sans produit
ni marque, avec les references de la banque de demo (codes DEMO fictifs).

Usage (depuis data-brique/, venv active, Ollama lance) : python demo_bot_v22.py
Le bot comprend les precisions (« petillante, gout citron vert », « elle doit etre bio »),
repond aux questions sur les pistes (« pourquoi cette association ? »), enregistre le choix
d'une piste (« je prends la piste 1 ») et prepare un recapitulatif de demande d'echantillons avec
les codes DEMO (rien n'est envoye).
« nouvelle demande » repart de zero ; ligne vide, « quitter » ou Ctrl+C pour sortir.
Options :
  --reformuler   llama3.2:3b reformule chaque reponse (verifiee) ; environ 5 fois plus lent.
                 Par defaut, mode rapide : le bot affiche le brouillon factuel.
  --echantillon  catalogue sample_v1 (par defaut : catalogue complet s'il est indexe, cf.
                 scripts/indexer_catalogue_complet.py)
  --trace        intention, appel du modele, source du texte, rejets des garde-fous et temps
Le bot V2.1 (pistes affichees telles quelles) reste disponible : python demo_bot.py
"""
import sys
import textwrap
import time

from src.moteur_v2 import MODELE_EMBEDDING, MODELE_LLM
from src.moteur_v22 import ATTRIBUTION, AssistantV22, MoteurV22

SORTIES = {"", "q", "quit", "quitter", "exit", "au revoir"}
NOUVELLE = {"nouvelle demande", "nouvelle", "recommencer"}
CHAMPS = [("type_de_produit", "Type de produit"), ("division", "Division"), ("piste", "Piste"),
          ("aromes", "Arômes"), ("codes_references", "Références"),
          ("codes_solutions", "Solutions"), ("creation_sur_mesure", "Création sur mesure"),
          ("profil", "Profil"), ("contraintes", "Contraintes"),
          ("brief_du_client", "Brief du client"), ("date", "Date"), ("statut", "Statut")]


def afficher(resultat: dict, secondes: float, trace: bool) -> None:
    print()
    for paragraphe in resultat["texte"].split("\n"):
        retrait = "  " + " " * (len(paragraphe) - len(paragraphe.lstrip()))
        for ligne in textwrap.wrap(paragraphe.strip(), 92, subsequent_indent="   "
                                   if paragraphe[:2].strip(". ").isdigit() else "") or [""]:
            print(f"{retrait}{ligne}")
    demande = resultat["demande_echantillons"]
    if demande:
        print("\n  ┌─ Demande d'échantillons (récapitulatif) " + "─" * 30)
        for cle, libelle in CHAMPS:
            valeur = demande.get(cle)
            if isinstance(valeur, list):
                if not valeur and cle in ("codes_solutions", "creation_sur_mesure"):
                    continue
                valeur = ", ".join(valeur) or "—"
            for i, ligne in enumerate(textwrap.wrap(f"{libelle} : {valeur}", 80)):
                print(f"  │ {'' if i == 0 else '  '}{ligne}")
        print("  └" + "─" * 71)
    if trace:
        v = resultat["verification"]
        print(f"\n  [intention {resultat['intention']} · modèle appelé : "
              f"{'oui' if resultat['etapes'].get('modele_appele') else 'non'} · texte : {v['source']}"
              f" · {secondes:.2f} s]")
        for rejet in v["rejets"]:
            print("  [rejeté]", {k: x for k, x in rejet.items() if k != "texte" and x})
    print()


def main() -> None:
    for flux in (sys.stdin, sys.stdout):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")
    trace = "--trace" in sys.argv
    reformuler = "--reformuler" in sys.argv
    print("Chargement de l'assistant V2.2 (modèles et vecteurs)…")
    debut = time.perf_counter()
    moteur = MoteurV22(catalogue="echantillon" if "--echantillon" in sys.argv else "auto")
    assistant = AssistantV22(moteur, reformuler=reformuler, prechauffer=True)
    print(f"Prêt en {time.perf_counter() - debut:.0f} s.")
    print(textwrap.dedent(f"""
        Bonjour ! Je suis l'assistant arômes. Parlez-moi de votre projet avec vos mots, par exemple :
          « une boisson pétillante, goût citron vert, pas trop sucrée »
        Je vous propose des pistes d'arômes à partir d'une étude des produits du marché les plus
        proches de votre idée, avec les références de notre banque de démonstration. Vous pouvez
        préciser, me poser des questions, choisir une piste et préparer une demande d'échantillons.
        (étude de marché : {MODELE_EMBEDDING}, catalogue {moteur.catalogue} ; {MODELE_LLM} si
        nécessaire ; {'reformulation activée' if reformuler else 'mode rapide'})
        Références DEMO fictives, pour la démonstration.
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

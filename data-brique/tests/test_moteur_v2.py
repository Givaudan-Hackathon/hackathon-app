"""Tests du moteur V2 qui ne dependent pas d'Ollama : repli sur la V1.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import re

from src.moteur_v1 import MoteurV1, normaliser
from src.moteur_v2 import MoteurV2


def test_repli_v1_si_ollama_injoignable():
    # port 9 (discard) : connexion refusee immediatement, comme un Ollama arrete
    v2 = MoteurV2(ollama_url="http://127.0.0.1:9")
    brief = "arôme fraise pour yaourt à boire"
    resultat = v2.recommander(brief)
    attendu = MoteurV1().recommander(brief)
    assert resultat["mode"] == "repli_v1"
    assert resultat["arome"] is None
    assert resultat["division"] == attendu["division"] == "flavors"
    assert resultat["top"]["code"].tolist() == attendu["top"]["code"].tolist()


def test_relance_sans_ollama_si_aucun_mot_cle():
    resultat = MoteurV2(ollama_url="http://127.0.0.1:9").recommander("Bonjour")
    assert resultat["mode"] == "relance"
    assert resultat["arome"] is None and resultat["top"].empty
    assert resultat["question"] == "Quel goût recherchez-vous ? Pour quel type de produit ?"


def test_ancrage_du_garde_fou():
    from src.moteur_v2 import ancre
    assert ancre("desserts végétaux", "une marque de desserts")
    assert not ancre("citron", "Bonjour")


class _MoteurFactice:
    """Remplace MoteurV2 : relance tant qu'aucun arome n'est cite, sans appel a Ollama."""

    def comprendre(self, message):
        return None, None, ("dessert" if "dessert" in message else None)

    def recommander(self, brief, k=5):
        return {"mode": "v2" if "pistache" in brief else "relance"}


def test_conversation_complete_la_demande():
    from src.moteur_v2 import Conversation
    conv = Conversation(_MoteurFactice())
    assert conv.repondre("Bonjour")["mode"] == "relance"
    resultat = conv.repondre("un dessert goût pistache")  # reponse a la relance : complement
    assert resultat["complement"] and resultat["brief"] == "Bonjour, un dessert goût pistache"
    assert conv.repondre("plutôt fruité")["brief"].endswith("pistache, plutôt fruité")
    nouvelle = conv.repondre("je cherche un nouveau dessert pour une autre gamme de produits")
    assert not nouvelle["complement"]


def test_extraction_des_aromes():
    from src.moteur_v2 import extraire_aromes
    texte = "Coco mangue-passion | lait de coco, jus de citron concentré, arôme naturel de vanille"
    assert extraire_aromes(texte) == ["fruit de la passion", "vanille", "coco", "mangue"]
    assert extraire_aromes("Cola | eau, colorant : caramel E150d") == ["cola"]
    assert extraire_aromes("Citron vert menthe") == ["citron vert", "menthe"]


def test_pistes_v21_sans_produit_ni_marque():
    import pandas as pd
    from src.moteur_v1 import CATALOGUE_DEFAUT
    from src.moteur_v2 import MoteurV21
    # repli sans Ollama : division par mots-cles, arome par la liste de reference, TF-IDF
    resultat = MoteurV21(ollama_url="http://127.0.0.1:9").pistes("arôme fraise pour yaourt à boire")
    assert resultat["mode"] == "repli_v1" and resultat["arome"] == "fraise"
    assert [p["type"] for p in resultat["pistes"]] == [
        "principal", "association_frequente", "association_originale"]
    assert "top" not in resultat
    # texte montre au client : aromes et explications, compare mot a mot aux noms et marques
    affiche = " ".join(" ".join(p["aromes"]) + " " + p["explication"] for p in resultat["pistes"])
    affiche = f" {' '.join(re.findall(r'[a-z0-9]+', normaliser(affiche)))} "
    catalogue = pd.read_csv(CATALOGUE_DEFAUT, dtype=str)
    candidats = {n for n in catalogue["product_name"].dropna() if len(n) > 6}
    candidats |= {m.strip() for b in catalogue["brands"].dropna() for m in b.split(",")
                  if len(m.strip()) > 3}
    fuites = [c for c in candidats
              if f" {' '.join(re.findall(r'[a-z0-9]+', normaliser(c)))} " in affiche]
    assert not fuites, fuites

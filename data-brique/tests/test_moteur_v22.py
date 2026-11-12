"""Tests de la V2.2 (assistant RAG) qui ne dependent pas d'Ollama, plus la verification des
reponses reelles de llama3.2:3b enregistrees par benchmark/parcours_v22.py.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.moteur_v1 import CATALOGUE_DEFAUT
from src.moteur_v2 import OllamaIndisponible
from src.moteur_v22 import (MOTS_COURANTS, AssistantV22, MoteurV22, NomsDuCommerce,
                            couples_inventes, extraire_contraintes, extraire_profil, nombres)

PARCOURS = Path(__file__).resolve().parents[1] / "benchmark" / "sorties" / "parcours_v22.json"


def _indisponible(*args, **kwargs):
    raise OllamaIndisponible("test hors ligne")


def _sans_vecteurs():
    raise FileNotFoundError("test hors ligne")


@pytest.fixture(scope="module")
def noms():
    return NomsDuCommerce([CATALOGUE_DEFAUT])


@pytest.fixture
def assistant_hors_ligne(noms):
    """Assistant sans Ollama : intention par les garde-fous, recherche TF-IDF, texte = brouillon."""
    moteur = MoteurV22()
    moteur._post = _indisponible
    moteur._vecteurs = _sans_vecteurs
    return AssistantV22(moteur, noms)


def test_extraction_des_contraintes_et_du_profil():
    message = "un goût pistache gourmand, pas trop sucré, bio, pour des desserts végétaux pour enfants"
    assert extraire_contraintes(message) == ["peu sucré", "végétal", "bio", "pour enfants"]
    assert extraire_contraintes("zéro sucre et sans gluten") == ["sans sucre", "sans gluten"]
    assert extraire_contraintes("sans sucres ajoutés") == ["peu sucré"]
    assert extraire_profil(message) == ["gourmand"]


def test_verification_des_chiffres_et_des_marques(noms, assistant_hors_ligne):
    source = "Parmi les 19 produits proches, il n'apparaît que dans 2 produits ; amande : 13 produits."
    assert nombres("19 produits, 2,5 g") == {"19", "2.5"}
    assert couples_inventes("dans 13 des 19 produits", source) == ["13 des 19"]
    assert couples_inventes("dans 2 des 19 produits", "présent dans 2 des 19 produits") == []
    marque = next(m.strip() for b in pd.read_csv(CATALOGUE_DEFAUT, dtype=str)["brands"].dropna()
                  for m in b.split(",") if len(m.strip()) > 5 and m.strip().lower() not in MOTS_COURANTS)
    erreurs = assistant_hors_ligne.verifier(f"Comme {marque}, dans 7 produits.", source)
    assert erreurs["chiffres_inventes"] == ["7"]
    assert erreurs["noms_du_commerce"]
    assert not any(assistant_hors_ligne.verifier(source, source).values())


def test_reformulation_refusee_si_marque_ou_chiffre_invente(noms):
    moteur = MoteurV22()
    assistant = AssistantV22(moteur, noms)
    marque = next(f.strip() for f in sorted(noms.formes) if f.strip().isalpha() and len(f) > 8)
    reponses = iter([f"Je vous conseille {marque}, comme 40 produits.",
                     "Monsieur, 19 produits : je vais vous transmettre la demande au conseiller."])
    assistant._chat = lambda *args, **kwargs: next(reponses)
    brouillon = "J'ai étudié 19 produits. Dans ce prototype, rien n'est envoyé : voyez un conseiller."
    texte, verification = assistant.rediger("et alors ?", brouillon, ["prototype"])
    assert texte == brouillon and verification["source"] == "brouillon (vérification échouée)"
    premier, second = verification["rejets"]
    assert premier["chiffres_inventes"] == ["40"] and premier["noms_du_commerce"]
    assert second["genre_suppose"] and second["envoi_annonce"] and second["mots_oublies"] == ["prototype"]


def test_parcours_complet_hors_ligne(assistant_hors_ligne):
    messages = ["Bonjour", "je voudrais créer un dessert",
                "un goût pistache gourmand, pas trop sucré, pour des desserts végétaux",
                "plutôt une crème dessert", "pourquoi la vanille ?", "je prends la piste 2",
                "comment je reçois des échantillons ?"]
    resultats = [assistant_hors_ligne.repondre(m) for m in messages]
    assert [r["intention"] for r in resultats] == [
        "hors_sujet", "nouvelle_demande", "precision", "precision", "question_piste",
        "choix_piste", "demande_echantillons"]
    projet = resultats[3]["projet"]
    assert projet["type_de_produit"] == "crème dessert" and projet["arome_principal"] == "pistache"
    assert projet["contraintes"] == ["peu sucré", "végétal"]
    assert "vanille" in resultats[4]["texte"]
    demande = resultats[-1]["demande_echantillons"]
    assert demande["piste"] == 2 and demande["aromes"][0] == "pistache"
    assert "non envoyé" in demande["statut"]
    for r in resultats:  # hors ligne, le texte est le brouillon : il passe ses propres controles
        assert not any(assistant_hors_ligne.verifier(r["texte"], r["contexte"]["brouillon"],
                                                     r["contexte"].get("mots_obligatoires") or []).values())


def test_reponses_enregistrees_sans_marque_ni_chiffre_invente(noms, assistant_hors_ligne):
    """Reponses reelles de llama3.2:3b (benchmark/parcours_v22.py) : aucune marque, aucun nom de
    produit, et chaque chiffre cite existe dans le contexte (brouillon) du tour."""
    if not PARCOURS.exists():
        pytest.skip("lancer d'abord benchmark/parcours_v22.py (Ollama requis)")
    tours = json.loads(PARCOURS.read_text(encoding="utf-8"))
    assert tours
    for tour in tours:
        erreurs = assistant_hors_ligne.verifier(tour["texte"], tour["brouillon"])
        assert not erreurs["noms_du_commerce"], (tour["message"], erreurs)
        assert not erreurs["chiffres_inventes"], (tour["message"], erreurs)
        assert not erreurs["couples_inventes"], (tour["message"], erreurs)


def test_mode_rapide_sans_reformulation(noms):
    assistant = AssistantV22(MoteurV22(), noms, reformuler=False)
    assistant.moteur._post = _indisponible
    assistant.rediger = lambda *args, **kwargs: pytest.fail("reformulation appelee en mode rapide")
    resultat = assistant.repondre("Bonjour")
    assert resultat["texte"] == resultat["contexte"]["brouillon"]
    assert resultat["verification"]["source"] == "brouillon (mode rapide)"


def test_correction_des_fautes_du_modele():
    from src.moteur_v22 import corriger
    assert corriger("La piste 2, c'est une excellente choix !") == "La piste 2, c'est un excellent choix !"
    assert corriger("Un excellente idée.") == "Une excellente idée."

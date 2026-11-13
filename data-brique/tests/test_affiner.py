"""Tests de l'etape Affiner (V2.3) et des synonymes du vocabulaire, sans Ollama.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import pytest

from src.mecanismes_v22 import synonyme_par_forme
from src.moteur_v1 import CATALOGUE_DEFAUT
from src.moteur_v2 import OllamaIndisponible
from src.moteur_v22 import JE_NE_SAIS_PAS, AssistantV22, MoteurV22, NomsDuCommerce


def _indisponible(*args, **kwargs):
    raise OllamaIndisponible("test hors ligne")


def _sans_vecteurs():
    raise FileNotFoundError("test hors ligne")


@pytest.fixture(scope="module")
def moteur():
    """Catalogue complet (variantes tirees des noms de produits), sans Ollama."""
    m = MoteurV22(catalogue="complet")
    m._post = _indisponible
    m._vecteurs = _sans_vecteurs
    return m


@pytest.fixture
def assistant(moteur):
    return AssistantV22(moteur, NomsDuCommerce([CATALOGUE_DEFAUT]))


def test_affiner_avant_les_pistes(assistant):
    resultat = assistant.repondre("un yaourt à la fraise")
    assert resultat["etape"] == "affiner" and resultat["pistes"] == []
    gout, intensite = resultat["questions"]
    assert gout["id"] == "gout" and intensite["id"] == "intensite"
    assert "fraise des bois" in gout["choix"]  # variante tiree des noms de produits du catalogue
    assert all(q["choix"][-1] == JE_NE_SAIS_PAS for q in resultat["questions"])
    assert 2 <= len(gout["choix"]) <= 7


def test_choix_puis_pistes(assistant):
    assistant.repondre("un yaourt à la fraise")
    resultat = assistant.repondre("fraise des bois")
    assert resultat["etape"] == "pistes" and resultat["questions"] == []
    assert resultat["compris"]["profil"] == ["fraise des bois"] and resultat["pistes"]


def test_je_ne_sais_pas_passe_aux_pistes(assistant):
    assistant.repondre("un yaourt à la fraise")
    resultat = assistant.repondre(JE_NE_SAIS_PAS)
    assert resultat["etape"] == "pistes" and resultat["compris"]["profil"] == []


@pytest.mark.parametrize("message", ["un yaourt à la fraise des bois", "un yaourt gourmand à la fraise",
                                     "un yaourt à la fraise pas trop sucré"])
def test_gout_deja_precise_saute_affiner(assistant, message):
    resultat = assistant.repondre(message)
    assert resultat["etape"] == "pistes" and resultat["questions"] == []


def test_une_seule_serie_de_questions(assistant):
    assistant.repondre("un yaourt à la fraise")
    resultat = assistant.repondre("il doit être bio")  # pas un choix : on n'interroge pas a nouveau
    assert resultat["etape"] == "pistes" and resultat["compris"]["contraintes"] == ["bio"]
    assert assistant.repondre("plutôt une crème dessert")["etape"] == "pistes"


def test_pas_de_choix_de_piste_pendant_affiner(assistant):
    assistant.repondre("un yaourt à la fraise")
    resultat = assistant.repondre("je prends la piste 1")
    assert resultat["intention"] != "choix_piste" and resultat["brief_final"] is None
    assert resultat["etape"] == "pistes" and resultat["pistes"]  # la question est passee
    assert not resultat["etapes"].get("modele_appele")


def test_choix_generes_pour_un_arome_sans_variante(assistant):
    resultat = assistant.repondre("un arôme durian pour une glace")
    gout = resultat["questions"][0]
    assert {"fruité", "gourmand", "acidulé", "frais"} & set(gout["choix"])  # choix generiques


def test_synonymes_par_la_forme():
    assert synonyme_par_forme("limette") == "citron vert"
    assert synonyme_par_forme("limettes") == "citron vert"
    assert synonyme_par_forme("citronnelle") is None  # n'est pas du citron
    assert synonyme_par_forme("frais") is None  # pas « fraise »


def test_un_arome_ne_s_associe_pas_avec_lui_meme(assistant, moteur):
    assert moteur.vocabulaire.extraire("un soda citron vert et limette") == ["citron vert"]
    assistant.repondre("un soda citron vert et limette")
    resultat = assistant.repondre(JE_NE_SAIS_PAS)
    for piste in resultat["pistes"]:
        assert len(set(piste["liste_aromes"])) == len(piste["liste_aromes"])
        assert "limette" not in piste["id"]

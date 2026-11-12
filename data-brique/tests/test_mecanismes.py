"""Tests des mecanismes generaux de la V2.2.3 (src/mecanismes_v22.py), sans Ollama, et non-regression
des phrases de la 2e revue Codex.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import numpy as np
import pytest

from src.mecanismes_v22 import groupe_produit, rattacher_type
from src.moteur_v1 import CATALOGUE_DEFAUT
from src.moteur_v2 import OllamaIndisponible
from src.moteur_v22 import TYPES, AssistantV22, MoteurV22, NomsDuCommerce


def _indisponible(*args, **kwargs):
    raise OllamaIndisponible("test hors ligne")


def _sans_vecteurs():
    raise FileNotFoundError("test hors ligne")


@pytest.fixture(scope="module")
def moteur():
    """Catalogue complet (vocabulaire), sans Ollama : recherche TF-IDF, pas d'alias bge-m3."""
    m = MoteurV22(catalogue="complet")
    m._post = _indisponible
    m._vecteurs = _sans_vecteurs
    return m


@pytest.fixture
def assistant(moteur):
    a = AssistantV22(moteur, NomsDuCommerce([CATALOGUE_DEFAUT]))
    return a


# 1. aromes : liste Fragrance acceptee en Flavors si les produits alimentaires la citent, et
#    vocabulaire tire du catalogue (sans liste ecrite a la main)
def test_vocabulaire_fragrance_et_catalogue(moteur):
    vocabulaire = moteur.vocabulaire
    assert {"mandarine", "bergamote", "agrumes"} <= set(vocabulaire.depuis_fragrance)
    assert "musc" not in vocabulaire.depuis_fragrance  # « muscat » ne compte pas
    assert vocabulaire.depuis_catalogue  # termes tires des noms et ingredients
    assert vocabulaire.extraire("sirop de mandarine") == ["mandarine"]
    assert vocabulaire.extraire("une limonade au sureau") == ["fleur de sureau"]


def test_arome_inconnu_extrait_quand_le_type_est_reconnu(assistant):
    assistant._analyse_llm = lambda message: {"intention": "nouvelle_demande", "numero": None,
                                              "division": "flavors", "arome": "durian", "application": None}
    analyse = assistant.analyser("une glace au durian")
    assert analyse["type"] == "glace" and analyse["arome"] == "durian"
    assert analyse["trace"]["modele_appele"]


def test_message_entierement_reconnu_sans_modele(assistant):
    assistant._analyse_llm = lambda message: pytest.fail("modele appele alors que tout est reconnu")
    analyse = assistant.analyser("une boisson pétillante au citron vert, pas trop sucrée")
    assert analyse["type"] == "boisson pétillante" and analyse["arome"] == "citron vert"


# 2. un mot qui fait partie du type n'est jamais l'arome
def test_mot_du_type_pas_arome(assistant):
    analyse = assistant.analyser("un thé glacé à la pêche et au citron")
    assert analyse["type"] == "thé glacé" and analyse["aromes"] == ["pêche", "citron"]
    assistant._analyse_llm = lambda message: {"intention": "nouvelle_demande", "numero": None,
                                              "division": "flavors", "arome": "noisette",
                                              "application": "biscuits"}
    analyse = assistant.analyser("je fais des biscuits, je veux un goût noisette")
    assert analyse["application"] == "biscuits" and "biscuit" not in analyse["aromes"]
    assert analyse["arome"] == "noisette"


# 3. type inconnu : groupe du produit, rattachement par vote, sinon le type tel que dit
def test_groupe_produit():
    assert groupe_produit("eau", "une eau aromatisée à l'orange") == "eau aromatisée"
    assert groupe_produit("pizza à la truffe", "pizza à la truffe") == "pizza"
    assert groupe_produit("smoothie mangue", "un smoothie mangue", arrets={"mangue"}) == "smoothie"


def test_rattacher_type_par_vote(moteur):
    class Factice:
        flavors = moteur.flavors
        masque_type = moteur.masque_type

        def __init__(self, score):
            self.score = score

        def _vecteurs(self):
            vecteurs = np.zeros((len(self.flavors), 1), dtype=np.float32)
            vecteurs[moteur.masque_type(self.flavors, "boisson pétillante")] = self.score
            return vecteurs

        def _embed(self, textes):
            return np.ones((1, 1), dtype=np.float32)

    assert rattacher_type(Factice(0.7), "eau gazeuse", list(TYPES))[0] == "boisson pétillante"
    assert rattacher_type(Factice(0.5), "pizza", list(TYPES))[0] is None  # rien d'assez proche


def test_type_hors_catalogue_garde_tel_quel(assistant):
    assistant._analyse_llm = lambda message: {"intention": "nouvelle_demande", "numero": None,
                                              "division": "flavors", "arome": None,
                                              "application": "pizza à la truffe"}
    resultat = assistant.repondre("pizza à la truffe")
    assert resultat["compris"]["type_produit"] == "pizza" and resultat["compris"]["arome"] == "truffe"
    assert "marché étudié est donc limité" in resultat["texte"]


# 4. intentions des messages flous
@pytest.mark.parametrize("message, intention, etape", [
    ("je veux un truc bon", "nouvelle_demande", "relance"),
    ("quel est le meilleur arôme ?", "nouvelle_demande", "relance"),
    ("j'ai besoin d'aide pour mon produit", "nouvelle_demande", "relance"),
    ("c'est combien un échantillon ?", "question", "relance"),
    ("vous livrez sous combien de temps ?", "question", "relance"),
    ("quelle heure est-il ?", "hors_sujet", "relance"),
])
def test_intentions_des_messages_flous(assistant, message, intention, etape):
    resultat = assistant.repondre(message)
    assert (resultat["intention"], resultat["etape"]) == (intention, etape)
    assert "€" not in resultat["texte"]


# 5. jamais d'arome tire d'une marque ; reponse polie
def test_marque(assistant):
    resultat = assistant.repondre("donne-moi la recette de Coca-Cola")
    assert resultat["intention"] == "hors_sujet" and resultat["compris"]["aromes"] == []
    assert "marque" in resultat["texte"] and "coca" not in resultat["texte"].lower()
    assistant.reinitialiser()
    resultat = assistant.repondre("un soda comme Coca-Cola mais au gingembre")
    assert resultat["compris"]["aromes"] == ["gingembre"]
    # « Crème dessert » figure dans le champ brands d'Open Food Facts : ce n'est pas une marque
    assistant.reinitialiser()
    resultat = assistant.repondre("une crème dessert végétale à la vanille")
    assert resultat["compris"]["type_produit"] == "crème dessert"


# non-regression : phrases de la 2e revue Codex (le gout ne doit pas etre perdu)
@pytest.mark.parametrize("message, type_produit, aromes", [
    ("une glace au durian", "glace", ["durian"]),
    ("une boisson à la bergamote", "boisson", ["bergamote"]),
    ("un thé glacé à la pêche et au citron", "thé glacé", ["pêche", "citron"]),
])
def test_revue_codex_2(assistant, message, type_produit, aromes):
    resultat = assistant.repondre(message)  # sans Ollama : repli par regles
    assert resultat["compris"]["type_produit"] == type_produit
    assert resultat["compris"]["aromes"] == aromes
    assert resultat["etape"] == "pistes"

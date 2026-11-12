"""Non-regression de la 3e revue Codex (commit 75d259d), sans Ollama.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import pytest

from src.moteur_v1 import CATALOGUE_DEFAUT
from src.moteur_v2 import OllamaIndisponible
from src.moteur_v22 import AssistantV22, MoteurV22, NomsDuCommerce, extraire_contraintes, extraire_retraits


def _indisponible(*args, **kwargs):
    raise OllamaIndisponible("test hors ligne")


def _sans_vecteurs():
    raise FileNotFoundError("test hors ligne")


@pytest.fixture(scope="module")
def noms():
    return NomsDuCommerce([CATALOGUE_DEFAUT])


@pytest.fixture
def assistant(noms):
    moteur = MoteurV22(catalogue="echantillon")
    moteur._post = _indisponible
    moteur._vecteurs = _sans_vecteurs
    return AssistantV22(moteur, noms)


# 1. « maintenant je voudrais… » : nouveau projet seulement si un autre type ou produit est cite
def test_maintenant_sans_autre_produit_est_une_precision(assistant):
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("elle doit être bio")
    resultat = assistant.repondre("maintenant je voudrais moins de sucre")
    assert resultat["intention"] == "precision" and resultat["etape"] == "pistes"
    compris = resultat["compris"]
    assert compris["type_produit"] == "boisson pétillante" and compris["arome"] == "citron vert"
    assert compris["contraintes"] == ["bio", "peu sucré"]
    assert any(s["nom"] == "Sweetness" for s in resultat["solutions"])  # etude relancee


def test_maintenant_avec_autre_produit_est_un_nouveau_projet(assistant):
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("elle doit être bio")
    resultat = assistant.repondre("maintenant je voudrais un yaourt à la fraise")
    assert resultat["intention"] == "nouvelle_demande"
    assert resultat["compris"]["type_produit"] == "yaourt" and resultat["compris"]["contraintes"] == []


# 2. exclusion != retrait : « pas de gluten » confirme la contrainte
@pytest.mark.parametrize("contrainte, mot", [("sans gluten", "gluten"), ("sans lactose", "lactose")])
def test_pas_de_x_garde_la_contrainte(assistant, contrainte, mot):
    assert extraire_contraintes(f"pas de {mot}") == [contrainte]
    assert extraire_retraits(f"pas de {mot}")[0] == []
    assistant.repondre(f"une crème dessert à la vanille {contrainte}")
    resultat = assistant.repondre(f"pas de {mot}")
    assert contrainte in resultat["compris"]["contraintes"]


@pytest.mark.parametrize("contrainte, phrase", [
    ("sans gluten", "finalement avec du gluten"),
    ("sans gluten", "on peut mettre du gluten"),
    ("sans gluten", "le gluten n'est plus un problème"),
    ("sans lactose", "finalement avec du lactose"),
    ("sans lactose", "on peut mettre du lactose"),
    ("sans lactose", "le lactose n'est plus un problème"),
])
def test_acceptation_retire_la_contrainte(assistant, contrainte, phrase):
    assert extraire_retraits(phrase)[0] == [contrainte]
    assistant.repondre(f"une crème dessert à la vanille {contrainte}")
    resultat = assistant.repondre(phrase)
    assert resultat["intention"] == "precision" and contrainte not in resultat["compris"]["contraintes"]


# 3. refus d'echantillons : pas de brouillon, etape recapitulatif, brief conserve
@pytest.mark.parametrize("refus", ["non merci, je ne veux pas d'échantillons",
                                   "pas d'échantillon pour l'instant"])
def test_refus_d_echantillons(assistant, refus):
    assistant.repondre("une boisson pétillante goût citron vert")
    brief = assistant.repondre("je prends la piste 1")["brief_final"]
    resultat = assistant.repondre(refus)
    assert resultat["etape"] == "recapitulatif" and resultat["demande_echantillons"] is None
    assert resultat["brief_final"] == brief and resultat["intention"] != "demande_echantillons"
    assert resultat["texte"].startswith("Entendu, je ne prépare pas de demande d'échantillons")


def test_refus_annule_un_brouillon_existant(assistant):
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("je prends la piste 1")
    assert assistant.repondre("je veux des échantillons")["demande_echantillons"] is not None
    resultat = assistant.repondre("finalement pas d'échantillon pour l'instant")
    assert resultat["etape"] == "recapitulatif" and resultat["demande_echantillons"] is None


def test_demande_d_echantillons_toujours_reconnue(assistant):
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("je prends la piste 1")
    resultat = assistant.repondre("comment je reçois des échantillons ?")
    assert resultat["intention"] == "demande_echantillons" and resultat["etape"] == "echantillons"


# « au bord de l'eau » : un mot de lieu ou suivi de « de » n'est jamais un arome
KOMBUCHA_1 = ("J'ai une marque de kombucha et je veux sortir une édition d'été. Un truc frais, un peu "
              "exotique, qui donne l'impression d'être en vacances au bord de l'eau.")


def test_kombucha_premier_message_sans_arome(assistant):
    resultat = assistant.repondre(KOMBUCHA_1)  # sans Ollama : repli par regles
    assert resultat["compris"]["type_produit"] == "kombucha"
    assert resultat["compris"]["arome"] is None and resultat["compris"]["aromes"] == []
    assert resultat["etape"] == "relance" and "Quel goût recherchez-vous ?" in resultat["texte"]


def test_mot_de_contexte_refuse_meme_venant_du_modele(assistant):
    assistant._analyse_llm = lambda message: {"intention": "nouvelle_demande", "numero": None,
                                              "division": "flavors", "arome": "bord", "application": None}
    resultat = assistant.repondre(KOMBUCHA_1)
    assert resultat["compris"]["arome"] is None and resultat["etape"] == "relance"


@pytest.mark.parametrize("message", ["une glace au cœur de l'été", "un sirop à la place de la grenadine du coin",
                                     "une boisson pour la plage"])
def test_mot_suivi_de_de_ou_de_lieu(message):
    from src.mecanismes_v22 import mot_de_contexte
    from src.moteur_v1 import normaliser
    texte = " ".join(__import__("re").findall(r"[a-z]+", normaliser(message)))
    mot = {"une glace au cœur de l'été": "coeur", "un sirop à la place de la grenadine du coin": "place",
           "une boisson pour la plage": "plage"}[message]
    assert mot_de_contexte(mot, texte)
    assert not mot_de_contexte("truffe", "pizza a la truffe")


def test_repli_apres_au_garde_un_vrai_gout(assistant):
    resultat = assistant.repondre("une glace au durian")  # sans Ollama : repli « au durian »
    assert resultat["compris"]["aromes"] == ["durian"]

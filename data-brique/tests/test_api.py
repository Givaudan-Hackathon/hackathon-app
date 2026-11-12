"""Tests des endpoints de l'API : V1 (/sante, /recommander) et contrat V2 (/conversation).

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client():
    # le bloc with declenche le lifespan, donc la construction de l'index TF-IDF
    with TestClient(app) as c:
        yield c


def test_sante(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok", "version_modele": "baseline-v1"}


@pytest.mark.parametrize("brief, division", [
    ("arôme fraise pour yaourt à boire", "flavors"),
    ("déodorant parfum boisé pour homme", "fragrance"),
])
def test_recommander(client, brief, division):
    reponse = client.post("/recommander", json={"brief": brief})
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["division"] == division
    assert len(corps["recommandations"]) == 5


CLES_REPONSE = {"session_id", "etape", "intention", "reponse", "compris", "pistes", "solutions",
                "brief", "echantillons", "version_modele", "attribution"}
CLES_PISTE = {"id", "rang", "nom", "description", "explication", "aromes", "nb_produits_marche",
              "references", "sans_reference", "image"}
CLES_REFERENCE = {"code", "nom", "profil_sensoriel", "forme", "labels"}
CLES_BRIEF = {"type_produit", "piste_id", "aromes", "contraintes", "codes_references",
              "codes_solutions", "creation_sur_mesure"}


def _envoyer(client, session_id, message="", **champs):
    reponse = client.post("/conversation", json={"session_id": session_id, "message": message, **champs})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert set(corps) == CLES_REPONSE  # toujours l'objet complet
    for piste in corps["pistes"]:
        assert set(piste) == CLES_PISTE and piste["image"] is None
        assert all(set(r) == CLES_REFERENCE for r in piste["references"])
    assert all(set(s) == CLES_REFERENCE for s in corps["solutions"])
    return corps


def test_conversation_parcours_citron_vert(client):
    corps = _envoyer(client, None, "Bonjour")
    session_id = corps["session_id"]
    assert (corps["etape"], corps["intention"]) == ("relance", "hors_sujet")
    assert corps["brief"] is None and corps["echantillons"] is None and corps["pistes"] == []

    corps = _envoyer(client, session_id, "je voudrais créer une boisson")
    assert (corps["etape"], corps["intention"]) == ("relance", "nouvelle_demande")
    assert corps["compris"]["type_produit"] == "boisson" and corps["compris"]["division"] == "flavors"

    corps = _envoyer(client, session_id, "pétillante, goût citron vert, pas trop sucrée")
    assert (corps["etape"], corps["intention"]) == ("pistes", "precision")
    assert corps["compris"] == {"division": "flavors", "type_produit": "boisson pétillante",
                                "arome": "citron vert", "aromes": ["citron vert"],
                                "contraintes": ["peu sucré"]}
    assert corps["pistes"][0]["id"] == "citron-vert" and corps["pistes"][0]["rang"] == 1
    assert [s["code"] for s in corps["solutions"]] == ["DEMO-028"]

    corps = _envoyer(client, session_id, "elle doit être bio")
    assert corps["compris"]["contraintes"] == ["peu sucré", "bio"]
    corps = _envoyer(client, session_id, "pourquoi vous proposez cette association ?")
    assert (corps["etape"], corps["intention"]) == ("pistes", "question_piste")

    corps = _envoyer(client, session_id, "je prends la piste 1")
    assert (corps["etape"], corps["intention"]) == ("recapitulatif", "choix_piste")
    assert set(corps["brief"]) == CLES_BRIEF and corps["brief"]["piste_id"] == "citron-vert"
    assert corps["brief"]["codes_references"] == ["DEMO-004"] and corps["brief"]["codes_solutions"] == ["DEMO-028"]

    corps = _envoyer(client, session_id, "comment je reçois des échantillons ?")
    assert (corps["etape"], corps["intention"]) == ("echantillons", "demande_echantillons")
    assert corps["echantillons"]["statut"] == "brouillon_non_envoye"
    assert set(corps["echantillons"]) == CLES_BRIEF | {"statut", "date", "brief_client"}
    assert corps["brief"] is not None and corps["pistes"]  # objet complet, pas un delta


def test_id_de_piste_stable(client):
    session_id = _envoyer(client, None, "une boisson pétillante goût citron vert")["session_id"]
    avant = _envoyer(client, session_id, "c'est quoi la piste 2 ?")
    apres = _envoyer(client, session_id, "et la piste 3, pourquoi ?")
    assert [p["id"] for p in avant["pistes"]] == [p["id"] for p in apres["pistes"]]
    assert all("+" in p["id"] for p in avant["pistes"][1:])
    # une contrainte relance l'etude : la piste « citron vert seul » garde son identifiant
    bio = _envoyer(client, session_id, "elle doit être bio")
    assert bio["pistes"][0]["id"] == avant["pistes"][0]["id"] == "citron-vert"


def test_choix_par_piste_id(client):
    corps = _envoyer(client, None, "une boisson pétillante goût citron vert")
    session_id, piste = corps["session_id"], corps["pistes"][1]
    corps = _envoyer(client, session_id, "", piste_id=piste["id"])
    assert (corps["etape"], corps["intention"]) == ("recapitulatif", "choix_piste")
    assert corps["brief"]["piste_id"] == piste["id"] and corps["brief"]["aromes"] == piste["aromes"]
    inconnu = client.post("/conversation", json={"session_id": session_id, "message": "",
                                                 "piste_id": "durian+fraise"})
    assert inconnu.status_code == 422 and "piste_id inconnu" in inconnu.json()["detail"]


def test_question_generale(client):
    session_id = _envoyer(client, None, "une boisson pétillante goût citron vert")["session_id"]
    corps = _envoyer(client, session_id, "c'est combien la livraison ?")
    assert (corps["etape"], corps["intention"]) == ("pistes", "question")
    assert "conseiller Givaudan" in corps["reponse"]


def test_conversation_message_vide(client):
    assert client.post("/conversation", json={"session_id": None, "message": ""}).status_code == 422

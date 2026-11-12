"""Tests des endpoints de l'API baseline V1.

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


def test_conversation_parcours_citron_vert(client):
    reponse = client.post("/conversation", json={"message": "je voudrais créer une boisson"})
    assert reponse.status_code == 200
    corps = reponse.json()
    conversation_id = corps["conversation_id"]
    assert corps["intention"] == "nouvelle_demande" and corps["projet"]["type_de_produit"] == "boisson"
    for message in ["pétillante, goût citron vert, pas trop sucrée", "je prends la piste 1",
                    "comment je reçois des échantillons ?"]:
        corps = client.post("/conversation", json={"conversation_id": conversation_id,
                                                   "message": message}).json()
        assert corps["conversation_id"] == conversation_id
    assert corps["intention"] == "demande_echantillons"
    demande = corps["demande_echantillons"]
    assert demande["codes_references"][0].startswith("DEMO-") and "DEMO-028" in demande["codes_solutions"]
    assert all("references" in piste for piste in corps["pistes"])


def test_conversation_message_vide(client):
    assert client.post("/conversation", json={"message": ""}).status_code == 422

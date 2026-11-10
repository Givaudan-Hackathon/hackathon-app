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

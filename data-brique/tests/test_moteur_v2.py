"""Tests du moteur V2 qui ne dependent pas d'Ollama : repli sur la V1.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
from src.moteur_v1 import MoteurV1
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

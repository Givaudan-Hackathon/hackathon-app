"""Tests des 7 anomalies de la revue Codex de la PR #18 et du scenario Product « kombucha ».

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
Les tests du moteur tournent sans Ollama ; ceux de l'API utilisent le TestClient (Ollama
optionnel : sans lui, l'API passe en repli).
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.moteur_v2 import OllamaIndisponible
from src.moteur_v22 import (AssistantV22, BanqueReferences, MoteurV22, NomsDuCommerce,
                            extraire_retraits, extraire_volume, type_cite)
from src.moteur_v1 import CATALOGUE_DEFAUT

RACINE = Path(__file__).resolve().parents[1]
KOMBUCHA = [
    "J'ai une marque de kombucha et je veux sortir une édition d'été. Un truc frais, un peu "
    "exotique, qui donne l'impression d'être en vacances au bord de l'eau.",
    "Plutôt un fruit, mais pas trop sucré. Peut-être fruit de la passion, avec un côté frais derrière.",
    "Assez acidulé, c'est notre signature.",
    "Oui, naturel, c'est important pour nos clients. Peut-être 5 000 bouteilles pour tester ?",
]


def _indisponible(*args, **kwargs):
    raise OllamaIndisponible("test hors ligne")


def _sans_vecteurs():
    raise FileNotFoundError("test hors ligne")


@pytest.fixture(scope="module")
def noms():
    return NomsDuCommerce([CATALOGUE_DEFAUT])


@pytest.fixture
def assistant(noms):
    """Assistant sans Ollama (regles, TF-IDF, references par nom d'arome)."""
    moteur = MoteurV22(catalogue="echantillon")
    moteur._post = _indisponible
    moteur._vecteurs = _sans_vecteurs
    return AssistantV22(moteur, noms)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _envoyer(client, session_id, message="", **champs):
    reponse = client.post("/conversation", json={"session_id": session_id, "message": message, **champs})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


# 1. une contrainte ne change jamais le type de produit
def test_1_contrainte_ne_change_pas_le_type(assistant):
    assert type_cite("riche en protéines") is None
    assert type_cite("un yaourt riche en protéines") == "yaourt"
    assert type_cite("une boisson protéinée à la vanille") == "boisson protéinée"
    assistant.repondre("un yaourt à la fraise")
    resultat = assistant.repondre("riche en protéines")
    assert resultat["intention"] == "precision"
    assert resultat["compris"]["type_produit"] == "yaourt"
    assert "protéiné" in resultat["compris"]["contraintes"]


# 2. le brouillon d'echantillons reste renvoye tant qu'il est valide
def test_2_echantillons_conserves_apres_merci(client):
    sid = _envoyer(client, None, "une boisson pétillante goût citron vert")["session_id"]
    _envoyer(client, sid, "Je ne sais pas, proposez-moi")  # etape Affiner
    _envoyer(client, sid, "je prends la piste 1")
    assert _envoyer(client, sid, "je veux des échantillons")["echantillons"] is not None
    corps = _envoyer(client, sid, "merci")
    assert corps["etape"] == "echantillons" and corps["echantillons"] is not None
    assert corps["echantillons"]["statut"] == "brouillon_non_envoye" and corps["brief"] is not None
    # une precision qui relance l'etude invalide le brouillon
    corps = _envoyer(client, sid, "elle doit être bio")
    assert corps["etape"] == "pistes" and corps["echantillons"] is None and corps["brief"] is None


# 3. references sans le label demande, dans la piste, le brief et les echantillons
def test_3_references_sans_label(client):
    banque = BanqueReferences(MoteurV22(catalogue="echantillon"))
    trouve = banque.chercher(["chocolat"], "laitier", ["bio"])
    assert trouve["references"] == []
    assert [(s["arome"], s["code"], s["labels_manquants"]) for s in trouve["sans_label"]] == [
        ("chocolat", "DEMO-020", ["bio"])]
    corps = _envoyer(client, None, "une crème dessert au chocolat bio")
    corps = _envoyer(client, corps["session_id"], "Je ne sais pas, proposez-moi")  # etape Affiner
    piste = corps["pistes"][0]
    attendu = {"arome": "chocolat", "code": "DEMO-020", "label_manquant": "bio"}
    assert attendu in piste["references_sans_label"]
    corps = _envoyer(client, corps["session_id"], "", piste_id=piste["id"])
    assert attendu in corps["brief"]["references_sans_label"]
    corps = _envoyer(client, corps["session_id"], "des échantillons s'il vous plaît")
    assert attendu in corps["echantillons"]["references_sans_label"]


# 4. une contrainte peut etre retiree, et les references sont recalculees
@pytest.mark.parametrize("retrait", ["finalement pas bio", "sans le bio", "pas besoin de bio"])
def test_4_retrait_de_contrainte(assistant, retrait):
    assert extraire_retraits(retrait)[0] == ["bio"]
    assert extraire_retraits("pas trop sucré")[0] == []  # « pas trop sucre » est une contrainte
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("Je ne sais pas, proposez-moi")  # etape Affiner
    bio = assistant.repondre("elle doit être bio")
    assert "bio" in bio["compris"]["contraintes"]
    assert "bio" in bio["pistes"][0]["references"][0]["labels"]
    resultat = assistant.repondre(retrait)
    assert resultat["intention"] == "precision" and "bio" not in resultat["compris"]["contraintes"]
    assert "bio" not in resultat["pistes"][0]["references"][0]["labels"]  # references recalculees


# 5. un changement explicite de projet repart d'un projet vide
@pytest.mark.parametrize("message, type_produit", [
    ("maintenant je voudrais un yaourt à la fraise", "yaourt"),
    ("une autre boisson", "boisson"),
    ("nouveau projet", None),
    ("un autre produit", None),
])
def test_5_changement_de_projet(assistant, message, type_produit):
    assistant.repondre("une boisson pétillante goût citron vert, pas trop sucrée")
    assistant.repondre("elle doit être bio")
    resultat = assistant.repondre(message)
    assert resultat["intention"] == "nouvelle_demande"
    assert resultat["compris"]["contraintes"] == []
    assert resultat["compris"]["type_produit"] == type_produit
    assert resultat["compris"]["arome"] == ("fraise" if type_produit == "yaourt" else None)
    assert resultat["brief_final"] is None


def test_5_une_autre_piste_n_est_pas_un_nouveau_projet(assistant):
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("Je ne sais pas, proposez-moi")  # etape Affiner
    assert assistant.repondre("tu as une autre piste ?")["intention"] != "nouvelle_demande"


# 6. numero de piste hors bornes : pas d'erreur, reponse polie
def test_6_piste_hors_bornes(client):
    sid = _envoyer(client, None, "une boisson pétillante goût citron vert")["session_id"]
    _envoyer(client, sid, "Je ne sais pas, proposez-moi")  # etape Affiner
    corps = _envoyer(client, sid, "je prends la piste 9")
    assert corps["intention"] == "choix_piste" and corps["etape"] == "pistes"
    assert corps["reponse"].startswith(f"Je n'ai que {len(corps['pistes'])} pistes : 1. ")
    assert corps["brief"] is None


# 7. le script d'indexation cree benchmark/cache avant la boucle
def test_7_indexation_cree_le_dossier_cache(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "indexer_catalogue_complet", RACINE / "scripts" / "indexer_catalogue_complet.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class MoteurFactice:
        dossier_cache = tmp_path / "benchmark" / "cache"  # absent, comme sur un clone neuf
        fichier_vecteurs = dossier_cache / "bge-m3_complet.npz"
        textes = ["a", "b", "c"]

        def _cle_cache(self):
            return "cle"

        def _embed(self, textes):
            return np.ones((len(textes), 2), dtype=np.float32)

    fichier = module.indexer(MoteurFactice(), taille_lot=1, point_reprise=1)
    assert fichier.exists() and np.load(fichier)["vecteurs"].shape == (3, 2)


# scenario Product : kombucha d'ete
def test_scenario_kombucha(assistant):
    resultats = [assistant.repondre(m) for m in KOMBUCHA]
    premier = resultats[0]["compris"]
    assert premier["division"] == "flavors" and premier["type_produit"] == "kombucha"
    compris = resultats[-1]["compris"]
    assert compris["type_produit"] == "kombucha" and compris["arome"] == "fruit de la passion"
    assert compris["profil"] == ["frais", "exotique", "acidulé"]
    assert compris["contraintes"] == ["peu sucré", "naturel"]
    assert extraire_volume(KOMBUCHA[-1]) == "5 000 bouteilles"
    # le volume est note dans le brief, sans aucun commentaire dans les reponses
    assert not any("5 000" in r["texte"] or "bouteille" in r["texte"] for r in resultats)
    brief = assistant.repondre("je prends la piste 1")["brief_final"]
    assert brief["volume"] == "5 000 bouteilles" and brief["type_de_produit"] == "kombucha"


def test_volume_seul_ne_relance_pas_le_choix(assistant):
    assistant.repondre("une boisson pétillante goût citron vert")
    assistant.repondre("Je ne sais pas, proposez-moi")  # etape Affiner
    assistant.repondre("je prends la piste 1")
    resultat = assistant.repondre("environ 2000 litres")
    assert resultat["intention"] == "precision" and resultat["etape"] == "recapitulatif"
    assert resultat["brief_final"]["volume"] == "2000 litres"
    assert "2000" not in resultat["texte"]

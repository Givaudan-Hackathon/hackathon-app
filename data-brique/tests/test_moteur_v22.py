"""Tests de la V2.2 (assistant RAG) qui ne dependent pas d'Ollama, plus la verification des
reponses enregistrees par benchmark/parcours_v22.py.

Usage (depuis data-brique/) : .venv/Scripts/python -m pytest
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.moteur_v1 import CATALOGUE_DEFAUT
from src.moteur_v2 import OllamaIndisponible
from src.moteur_v22 import (MOTS_COURANTS, AssistantV22, BanqueReferences, MoteurV22,
                            NomsDuCommerce, aromes_inventes, corriger, couples_inventes,
                            extraire_contraintes, extraire_profil, nombres, type_cite,
                            types_inventes)

SORTIES = Path(__file__).resolve().parents[1] / "benchmark" / "sorties"
PARCOURS_CITRON_VERT = ["Bonjour", "je voudrais créer une boisson",
                        "pétillante, goût citron vert, pas trop sucrée", "elle doit être bio",
                        "pourquoi vous proposez cette association ?", "je prends la piste 1",
                        "comment je reçois des échantillons ?"]


def _indisponible(*args, **kwargs):
    raise OllamaIndisponible("test hors ligne")


def _sans_vecteurs():
    raise FileNotFoundError("test hors ligne")


@pytest.fixture(scope="module")
def noms():
    return NomsDuCommerce([CATALOGUE_DEFAUT])


def _moteur_hors_ligne() -> MoteurV22:
    moteur = MoteurV22(catalogue="echantillon")
    moteur._post = _indisponible
    moteur._vecteurs = _sans_vecteurs
    return moteur


@pytest.fixture
def assistant_hors_ligne(noms):
    """Assistant sans Ollama : analyse par regles, recherche TF-IDF, references par nom d'arome."""
    return AssistantV22(_moteur_hors_ligne(), noms)


def test_extraction_des_contraintes_du_profil_et_du_type():
    message = "un goût pistache gourmand, pas trop sucré, bio, pour des desserts végétaux pour enfants"
    assert extraire_contraintes(message) == ["peu sucré", "végétal", "bio", "pour enfants"]
    assert extraire_contraintes("zéro sucre et sans gluten") == ["sans sucre", "sans gluten"]
    assert extraire_contraintes("sans sucres ajoutés") == ["peu sucré"]
    assert extraire_profil(message) == ["gourmand"]
    assert type_cite("pétillante, goût citron vert") == "boisson pétillante"
    assert type_cite("un thé glacé à la pêche") == "thé glacé"
    assert type_cite("un arôme durian pour une glace") == "glace"
    assert type_cite("plutôt une crème dessert") == "crème dessert"
    assert type_cite(message) == "dessert"
    assert type_cite("elle doit être bio") is None


def test_verification_des_chiffres_aromes_et_marques(noms, assistant_hors_ligne):
    source = "Parmi les 19 produits proches, il n'apparaît que dans 2 produits ; amande : 13 produits."
    assert nombres("19 produits, 2,5 g, DEMO-004") == {"19", "2.5"}
    assert couples_inventes("dans 13 des 19 produits", source) == ["13 des 19"]
    assert couples_inventes("dans 2 des 19 produits", "présent dans 2 des 19 produits") == []
    assert types_inventes("Parmi les 50 sirops", "50 boissons pétillantes") == ["sirop"]
    from src.moteur_v22 import codes_deplaces
    brouillon = "1. Durian seul.\n   Aucune référence.\n2. Durian + coco.\n   Référence : DEMO-026."
    assert codes_deplaces("1. Durian seul. DEMO-026\n2. Durian + coco. DEMO-026", brouillon) == ["piste 1"]
    assert codes_deplaces(brouillon, brouillon) == []
    assert aromes_inventes("Pistes : fraise + vanille, fraise + rhubarbe", "citron vert + citron") == [
        "fraise", "vanille"]
    marque = next(m.strip() for b in pd.read_csv(CATALOGUE_DEFAUT, dtype=str)["brands"].dropna()
                  for m in b.split(",") if len(m.strip()) > 5 and m.strip().lower() not in MOTS_COURANTS)
    erreurs = assistant_hors_ligne.verifier(f"Comme {marque}, dans 7 produits.", source)
    assert erreurs["chiffres_inventes"] == ["7"]
    assert erreurs["noms_du_commerce"]
    assert not any(assistant_hors_ligne.verifier(source, source).values())


def test_reformulation_refusee_si_invention(noms):
    assistant = AssistantV22(MoteurV22(catalogue="echantillon"), noms, reformuler=True)
    marque = next(f.strip() for f in sorted(noms.formes) if f.strip().isalpha() and len(f) > 8)
    reponses = iter([f"Je vous conseille {marque}, avec fraise + rhubarbe, comme 40 produits (DEMO-099).",
                     "Monsieur, 19 produits : je vais vous transmettre la demande au conseiller."])
    assistant._chat = lambda *args, **kwargs: next(reponses)
    brouillon = ("J'ai étudié 19 produits au citron vert (DEMO-004). Dans ce prototype, rien n'est "
                 "envoyé : voyez un conseiller.")
    texte, verification = assistant.rediger("et alors ?", brouillon, ["prototype", "DEMO-004"])
    assert texte == brouillon and verification["source"] == "brouillon (vérification échouée)"
    premier, second = verification["rejets"]
    assert premier["chiffres_inventes"] == ["40"] and premier["noms_du_commerce"]
    assert premier["aromes_inventes"] == ["fraise"] and premier["codes_inventes"] == ["DEMO-099"]
    assert second["genre_suppose"] and second["envoi_annonce"]
    assert second["mots_oublies"] == ["prototype", "DEMO-004"]


def test_banque_de_references():
    banque = BanqueReferences(_moteur_hors_ligne())
    assert len(banque.df) == 30 and banque.df["code"].str.match(r"DEMO-\d{3}$").all()
    assert (banque.df["famille"] == "agrumes").sum() >= 8
    bio = banque.chercher(["citron vert"], "boissons", ["bio"])
    assert [r["code"] for r in bio["references"]] == ["DEMO-004"]
    standard = banque.chercher(["citron vert"], "boissons", [])
    assert "bio" not in standard["references"][0]["labels"]
    assert banque.chercher(["citron vert", "menthe"], "boissons", [])["references"][0]["nom"] == \
        "Citron vert et menthe"
    assert banque.chercher(["durian"], "sucré", [])["manquants"] == ["durian"]
    assert [s["nom"] for s in banque.solutions(["peu sucré"], "boissons")] == ["Sweetness"]


def test_parcours_citron_vert_hors_ligne_sans_derive(assistant_hors_ligne):
    assistant_hors_ligne._chat = lambda *a, **k: pytest.fail("modele appele alors qu'une regle suffit")
    resultats = [assistant_hors_ligne.repondre(m) for m in PARCOURS_CITRON_VERT]
    assert [r["intention"] for r in resultats] == [
        "hors_sujet", "nouvelle_demande", "precision", "precision", "question_piste",
        "choix_piste", "demande_echantillons"]
    assert not any(r["etapes"]["modele_appele"] for r in resultats)
    assert resultats[1]["texte"].count("?") <= 2  # au plus 2 questions
    for r in resultats[2:4]:  # le type ne change pas avec les contraintes
        assert r["etapes"]["filtre_type"] == "boisson pétillante"
        assert r["projet"]["type_de_produit"] == "boisson pétillante"
        assert all(p["aromes"].startswith("citron vert") for p in r["pistes"])
        assert not {"amande", "banane", "vanille"} & {a for p in r["pistes"] for a in p["aromes"].split(" + ")}
        assert "DEMO-028" in r["texte"]  # peu sucré -> Sweetness
    assert resultats[3]["projet"]["contraintes"] == ["peu sucré", "bio"]
    assert "boisson pétillante au citron vert, peu sucrée et bio" in resultats[3]["texte"]
    assert "observée" in resultats[4]["texte"]  # origine de l'association
    brief = resultats[5]["brief_final"]
    assert brief["piste"] == 1 and brief["codes_references"] == ["DEMO-004"]  # citron vert bio
    assert brief["codes_solutions"] == ["DEMO-028"]
    demande = resultats[-1]["demande_echantillons"]
    assert demande["codes_references"] == ["DEMO-004"] and "non envoyé" in demande["statut"]


def test_sans_reference_creation_sur_mesure(assistant_hors_ligne):
    resultat = assistant_hors_ligne.repondre("un arôme durian pour une glace")
    assert resultat["etape"] == "affiner"
    resultat = assistant_hors_ligne.repondre("Je ne sais pas, proposez-moi")
    assert resultat["projet"]["type_de_produit"] == "glace"
    assert resultat["projet"]["arome_principal"] == "durian"
    assert resultat["pistes"][0]["references"] == [] and resultat["pistes"][0]["sans_reference"] == ["durian"]
    assert "création sur mesure" in resultat["texte"]


def test_mode_rapide_par_defaut(noms):
    assistant = AssistantV22(_moteur_hors_ligne(), noms)
    assistant.rediger = lambda *args, **kwargs: pytest.fail("reformulation appelee en mode rapide")
    resultat = assistant.repondre("Bonjour")
    assert resultat["texte"] == resultat["contexte"]["brouillon"]
    assert resultat["verification"]["source"] == "brouillon (mode rapide)"


def test_correction_des_fautes_du_modele():
    assert corriger("La piste 2, c'est une excellente choix !") == "La piste 2, c'est un excellent choix !"
    assert corriger("Un excellente idée.") == "Une excellente idée."


@pytest.mark.parametrize("fichier", ["parcours_v22.json", "parcours_v22_reformule.json"])
def test_reponses_enregistrees_sans_invention(assistant_hors_ligne, fichier):
    """Reponses enregistrees par benchmark/parcours_v22.py (reformulees par llama3.2:3b pour le
    second fichier) : aucune marque, aucun nom de produit, aucun arome ni chiffre absent du
    brouillon du tour, et chaque piste porte un champ references."""
    chemin = SORTIES / fichier
    if not chemin.exists():
        pytest.skip(f"lancer d'abord benchmark/parcours_v22.py ({fichier})")
    tours = json.loads(chemin.read_text(encoding="utf-8"))
    assert tours
    for tour in tours:
        erreurs = assistant_hors_ligne.verifier(tour["texte"], tour["brouillon"])
        for cle in ("noms_du_commerce", "chiffres_inventes", "couples_inventes", "aromes_inventes",
                    "codes_inventes", "types_inventes", "codes_deplaces"):
            assert not erreurs[cle], (tour["message"], cle, erreurs[cle])
        assert all("references" in piste for piste in tour["pistes"])


def test_accord_masculin_pour_yaourt(assistant_hors_ligne):
    resultat = assistant_hors_ligne.repondre("un yaourt à la fraise, gourmand et pas trop sucré")
    assert "yaourt à la fraise, gourmand, peu sucré" in resultat["texte"]

"""Cree la banque de references de demo (30 references fictives) et sa fiche .meta.json.

Usage (depuis data-brique/) : .venv/Scripts/python scripts/creer_banque_references.py
Sorties : data/processed/banque_references_demo.csv et banque_references_demo.meta.json.

Les references sont FICTIVES (codes DEMO-xxx) : elles imitent la structure d'un catalogue
d'aromes (gammes, familles, formes, labels, applications) decrite publiquement, sans reprendre
de vraies references Givaudan.
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "processed" / "banque_references_demo.csv"
COLONNES = ["code", "nom", "gamme", "famille", "profil_sensoriel", "forme", "labels",
            "applications", "inspire_de"]
ESSENTIALS = "Givaudan, présentation publique de la gamme TasteEssentials® (famille {})"
COLLECTIONS = "Givaudan, présentation publique de la gamme TasteCollections (fruits et épices)"
SOLUTIONS = "Givaudan, présentation publique de la gamme TasteSolutions® ({})"

# nom, gamme, famille, profil sensoriel, forme, labels, applications
REFERENCES = [
    ("Citron jaune zesté", "TasteEssentials", "agrumes",
     "citron frais, zeste, légèrement acidulé", "soluble eau", "naturel|vegan|halal|casher",
     "boissons|sucré|laitier"),
    ("Citron jaune bio", "TasteEssentials", "agrumes",
     "citron jaune juteux, notes de zeste, acidulé", "soluble eau", "naturel|bio|vegan",
     "boissons|sucré"),
    ("Citron vert frais", "TasteEssentials", "agrumes",
     "citron vert vif, zeste, acidulé, notes vertes", "soluble eau",
     "naturel|vegan|halal|casher|sans allergène", "boissons|sucré"),
    ("Citron vert bio", "TasteEssentials", "agrumes",
     "citron vert juteux, frais, légèrement amer", "soluble eau", "naturel|bio|vegan",
     "boissons|sucré"),
    ("Citron vert et menthe", "TasteEssentials", "agrumes",
     "citron vert acidulé, menthe fraîche, effet rafraîchissant", "soluble eau",
     "naturel|vegan|halal", "boissons"),
    ("Orange douce", "TasteEssentials", "agrumes",
     "orange mûre, juteuse, sucrée", "soluble eau", "naturel|vegan|halal|casher",
     "boissons|sucré|laitier"),
    ("Orange bio", "TasteEssentials", "agrumes",
     "orange pressée, zeste, douce", "soluble eau", "naturel|bio|vegan", "boissons|sucré"),
    ("Pamplemousse", "TasteEssentials", "agrumes",
     "pamplemousse frais, amertume légère, zeste", "soluble eau", "naturel|vegan|halal",
     "boissons"),
    ("Pamplemousse rose", "TasteEssentials", "agrumes",
     "pamplemousse rose, fruité, peu amer", "soluble eau", "naturel|vegan|sans allergène",
     "boissons|sucré"),
    ("Yuzu", "TasteEssentials", "agrumes",
     "yuzu floral, acidulé, notes de mandarine", "soluble eau", "naturel|vegan",
     "boissons|sucré"),
    ("Bergamote", "TasteEssentials", "agrumes",
     "bergamote fleurie, zeste, légèrement poivrée", "huile", "naturel|vegan",
     "boissons|sucré"),
    ("Agrumes mélangés", "TasteEssentials", "agrumes",
     "citron, orange et pamplemousse, frais et équilibré", "soluble eau",
     "naturel|vegan|halal|casher", "boissons|sucré|laitier"),
    ("Agrumes mélangés bio", "TasteEssentials", "agrumes",
     "citron et orange, frais, zesté", "soluble eau", "naturel|bio|vegan", "boissons"),
    ("Vanille bourbon", "TasteEssentials", "vanille",
     "vanille ronde, crémeuse, notes boisées", "soluble eau", "naturel|halal|casher",
     "sucré|laitier|boissons"),
    ("Vanille bio", "TasteEssentials", "vanille",
     "vanille douce, gourmande", "poudre", "naturel|bio|vegan", "sucré|laitier"),
    ("Café torréfié", "TasteEssentials", "café",
     "café torréfié, notes grillées, légère amertume", "soluble eau", "naturel|vegan|halal",
     "boissons|laitier|sucré"),
    ("Thé vert", "TasteEssentials", "thé",
     "thé vert frais, herbacé, légèrement astringent", "soluble eau", "naturel|vegan",
     "boissons"),
    ("Thé noir pêche", "TasteEssentials", "thé",
     "thé noir infusé, pêche juteuse", "soluble eau", "naturel|vegan|halal", "boissons"),
    ("Crème fraîche", "TasteEssentials", "laitier",
     "crème lactée, ronde, onctueuse", "poudre", "naturel|halal|casher", "laitier|sucré|salé"),
    ("Chocolat noir", "TasteEssentials", "chocolat",
     "cacao intense, notes torréfiées", "poudre", "naturel|vegan|halal",
     "sucré|laitier|boissons"),
    ("Menthe poivrée", "TasteEssentials", "menthe",
     "menthe poivrée, fraîche, puissante", "huile", "naturel|vegan|halal|casher",
     "boissons|sucré"),
    ("Menthe verte", "TasteEssentials", "menthe",
     "menthe douce, verte, rafraîchissante", "soluble eau", "naturel|vegan|bio",
     "boissons|sucré"),
    ("Fruits rouges", "TasteCollections", "fruits rouges",
     "fraise, framboise et cassis, fruité, légèrement acidulé", "soluble eau",
     "naturel|vegan|halal", "boissons|sucré|laitier"),
    ("Fraise mûre", "TasteCollections", "fruits rouges",
     "fraise mûre, sucrée, juteuse", "soluble eau", "naturel|vegan|sans allergène",
     "laitier|sucré|boissons"),
    ("Mangue Alphonso", "TasteCollections", "mangue",
     "mangue mûre, exotique, juteuse", "soluble eau", "naturel|vegan|halal",
     "boissons|laitier|sucré"),
    ("Noix de coco", "TasteCollections", "coco",
     "coco lactée, douce, exotique", "soluble eau", "naturel|vegan|sans allergène",
     "boissons|laitier|sucré"),
    ("Gingembre", "TasteCollections", "gingembre",
     "gingembre piquant, frais, épicé", "huile", "naturel|vegan|halal|casher",
     "boissons|sucré|salé"),
    ("Sweetness", "TasteSolutions", "solution",
     "renforce la perception sucrée pour réduire le sucre ajouté", "soluble eau",
     "naturel|vegan|halal|casher", "boissons|sucré|laitier"),
    ("Mouthfeel", "TasteSolutions", "solution",
     "apporte de l'onctuosité et du corps avec moins de matières grasses", "poudre",
     "naturel|vegan|halal", "laitier|sucré|boissons"),
    ("Saltiness", "TasteSolutions", "solution",
     "renforce la perception salée pour réduire le sel", "poudre", "naturel|vegan|halal|casher",
     "salé"),
]


def inspiration(gamme: str, famille: str, nom: str) -> str:
    if gamme == "TasteEssentials":
        return ESSENTIALS.format(famille)
    if gamme == "TasteSolutions":
        return SOLUTIONS.format(nom)
    return COLLECTIONS


def main() -> None:
    lignes = [dict(zip(COLONNES, (f"DEMO-{i:03d}", nom, gamme, famille, profil, forme, labels,
                                  applications, inspiration(gamme, famille, nom))))
              for i, (nom, gamme, famille, profil, forme, labels, applications)
              in enumerate(REFERENCES, 1)]
    with open(SORTIE, "w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, COLONNES)
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    familles = sorted({ligne["famille"] for ligne in lignes})
    meta = {
        "fichier": SORTIE.name,
        "nature": "EXEMPLE FICTIF pour la démo : codes DEMO-xxx inventés, ce ne sont pas de vraies "
                  "références Givaudan. Noms, profils, formes, labels et applications sont "
                  "illustratifs.",
        "inspiration": "Structure inspirée de sources publiques : présentations publiques des gammes "
                       "Givaudan TasteEssentials®, TasteCollections et TasteSolutions®. Aucune "
                       "donnée propriétaire.",
        "a_valider": "La répartition des familles entre TasteEssentials et TasteCollections est "
                     "une hypothèse : le document de Product « Défi 02 : les arômes du catalogue "
                     "Givaudan » n'a pas été transmis avec la demande.",
        "date_creation": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "scripts/creer_banque_references.py",
        "licence": "Données fictives créées par l'équipe G15, libres de réutilisation pour le "
                   "hackathon.",
        "n_references": len(lignes),
        "colonnes": {
            "code": "identifiant fictif DEMO-001 à DEMO-030",
            "gamme": "TasteEssentials, TasteCollections ou TasteSolutions",
            "famille": "famille d'arôme ; « solution » pour les TasteSolutions",
            "profil_sensoriel": "description courte du goût",
            "forme": "soluble eau, huile ou poudre",
            "labels": "séparés par | : naturel, vegan, bio, halal, casher, sans allergène",
            "applications": "séparées par | : boissons, sucré, laitier, salé",
            "inspire_de": "référence publique d'origine (gamme et famille)",
        },
        "familles": familles,
        "n_agrumes": sum(ligne["famille"] == "agrumes" for ligne in lignes),
    }
    SORTIE.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
    print(f"{len(lignes)} références -> {SORTIE}")


if __name__ == "__main__":
    main()

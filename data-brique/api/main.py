"""API de la brique Data : brief client -> recommandation (baseline V1).

Lancement (depuis data-brique/) : .venv/Scripts/uvicorn api.main:app --port 8000
Swagger : http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager
from typing import Literal

import pandas as pd
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.moteur_v1 import VERSION_MODELE, MoteurV1

ATTRIBUTION = "Contient des données d'Open Food Facts / Open Beauty Facts, licence ODbL"

EXEMPLE_REPONSE = {
    "brief": "sirop goût menthe pour cafés",
    "division": "flavors",
    "scores_division": {"flavors": 4, "fragrance": 0},
    "recommandations": [
        {
            "code": "3660668209510",
            "nom": "Sirop de Menthe",
            "marque": "Frigolet",
            "categorie": "boissons_aromatisees",
            "format": None,
            "score": 0.42,
            "url_produit": "https://world.openfoodfacts.org/product/3660668209510",
        },
        {
            "code": "3092712200226",
            "nom": "Sirop de Menthe Verte",
            "marque": "Teisseire",
            "categorie": "boissons_aromatisees",
            "format": None,
            "score": 0.399,
            "url_produit": "https://world.openfoodfacts.org/product/3092712200226",
        },
    ],
    "version_modele": VERSION_MODELE,
    "attribution": ATTRIBUTION,
}

moteur: MoteurV1 | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    # index TF-IDF construit une fois au demarrage (~1 s)
    global moteur
    moteur = MoteurV1()
    yield


app = FastAPI(
    title="Givaudan G15 — Brique Data",
    description=(
        "Moteur **brief client → recommandation** (baseline V1 : mots-clés + TF-IDF).\n\n"
        "Données : Open Food Facts / Open Beauty Facts (ODbL), produits vendus en France. "
        "L'attribution renvoyée dans chaque réponse doit être affichée par le front."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS ouvert pour le front de l'equipe Tech (pas de cookies ni d'authentification)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Sante(BaseModel):
    statut: Literal["ok"] = "ok"
    version_modele: str = Field(examples=[VERSION_MODELE])


class Demande(BaseModel):
    brief: str = Field(min_length=3, max_length=500,
                       description="Demande client en texte libre, en français.")
    k: int = Field(default=5, ge=1, le=20, description="Nombre de produits recommandés.")


class Recommandation(BaseModel):
    code: str = Field(description="Code-barres du produit (EAN).")
    nom: str | None
    marque: str | None
    categorie: str = Field(description="query_category du produit, ex. boissons_proteinees.")
    format: Literal["poudre", "pret_a_boire"] | None = Field(
        description="Renseigné uniquement pour les boissons protéinées.")
    score: float = Field(description="Similarité cosinus TF-IDF, entre 0 et 1.")
    url_produit: str


class Reponse(BaseModel):
    model_config = {"json_schema_extra": {"examples": [EXEMPLE_REPONSE]}}

    brief: str
    division: Literal["flavors", "fragrance", "indeterminee"]
    scores_division: dict[str, int] = Field(
        description="Nombre de mots-clés de chaque division trouvés dans le brief.")
    recommandations: list[Recommandation]
    version_modele: str
    attribution: str


EXEMPLES_DEMANDE = {
    "proteinee": {"summary": "Boisson protéinée (Flavors)",
                  "value": {"brief": "boisson protéinée vanille pour sportifs, base pois", "k": 5}},
    "yaourt": {"summary": "Yaourt à boire (Flavors)",
               "value": {"brief": "arôme fraise pour yaourt à boire", "k": 5}},
    "sirop": {"summary": "Sirop (Flavors)",
              "value": {"brief": "sirop goût menthe pour cafés", "k": 3}},
    "savon": {"summary": "Savons (Fragrance)",
              "value": {"brief": "senteur premium fraîche pour une gamme de savons", "k": 5}},
    "deodorant": {"summary": "Déodorant (Fragrance)",
                  "value": {"brief": "déodorant parfum boisé pour homme", "k": 5}},
}


def _valeur(v):
    return None if pd.isna(v) else v


@app.get("/sante", response_model=Sante, tags=["supervision"],
         summary="Vérifier que l'API répond")
def sante() -> Sante:
    return Sante(version_modele=VERSION_MODELE)


@app.post("/recommander", response_model=Reponse, tags=["recommandation"],
          summary="Recommander des produits à partir d'un brief client")
def recommander(demande: Demande = Body(openapi_examples=EXEMPLES_DEMANDE)) -> Reponse:
    resultat = moteur.recommander(demande.brief, demande.k)
    recommandations = [
        Recommandation(
            code=ligne.code, nom=_valeur(ligne.product_name), marque=_valeur(ligne.brands),
            categorie=ligne.query_category, format=_valeur(ligne.format),
            score=float(ligne.score), url_produit=ligne.url_produit,
        )
        for ligne in resultat["top"].itertuples()
    ]
    return Reponse(
        brief=demande.brief, division=resultat["division"],
        scores_division=resultat["scores_division"], recommandations=recommandations,
        version_modele=VERSION_MODELE, attribution=ATTRIBUTION,
    )

"""API de la brique Data.

- POST /recommander : brief client -> top k produits (baseline V1, inchange).
- POST /conversation : assistant conversationnel V2.2 (pistes d'aromes, references DEMO,
  demande d'echantillons), un message par appel, etat garde par conversation_id.

Lancement (depuis data-brique/) : .venv/Scripts/uvicorn api.main:app --port 8000
Swagger : http://127.0.0.1:8000/docs
"""
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

import pandas as pd
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.moteur_v1 import CATALOGUE_DEFAUT, VERSION_MODELE, MoteurV1
from src.moteur_v2 import CATALOGUE_COMPLET
from src.moteur_v22 import ATTRIBUTION as ATTRIBUTION_V22
from src.moteur_v22 import VERSION_V22, AssistantV22, MoteurV22, NomsDuCommerce

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
moteur_v22: MoteurV22 | None = None
noms_du_commerce: NomsDuCommerce | None = None

# conversations en memoire (prototype) : au plus MAX_CONVERSATIONS, oubliees apres DUREE_CONVERSATION
MAX_CONVERSATIONS = 500
DUREE_CONVERSATION = 2 * 3600  # secondes d'inactivite
conversations: dict[str, dict] = {}  # id -> {"assistant", "verrou", "vu"}
verrou_conversations = threading.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # index TF-IDF construit une fois au demarrage (~1 s) ; moteur V2.2 partage entre les
    # conversations, modeles et vecteurs precharges (sans Ollama, l'assistant passe en repli)
    global moteur, moteur_v22, noms_du_commerce
    moteur = MoteurV1()
    moteur_v22 = MoteurV22()
    chemins = [CATALOGUE_DEFAUT] + ([CATALOGUE_COMPLET] if moteur_v22.catalogue == "complet" else [])
    noms_du_commerce = NomsDuCommerce(chemins)
    AssistantV22(moteur_v22, noms_du_commerce).prechauffer()
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


class MessageConversation(BaseModel):
    conversation_id: str | None = Field(
        default=None, max_length=64,
        description="Absent ou inconnu : nouvelle conversation (l'identifiant est renvoyé).")
    message: str = Field(min_length=1, max_length=500, description="Message du client, en français.")
    reformuler: bool = Field(
        default=False, description="Expérimental : réponse reformulée par llama3.2:3b (~33 s).")


class Reference(BaseModel):
    code: str = Field(description="Code fictif DEMO-001 à DEMO-030 (banque de démo).")
    nom: str
    profil_sensoriel: str
    forme: Literal["soluble eau", "huile", "poudre"]
    labels: list[str]


class Piste(BaseModel):
    numero: int
    aromes: str = Field(examples=["citron vert + citron"])
    explication: str
    origine: str = Field(description="Nombre de produits, association observée ou à valider.")
    references: list[Reference]
    sans_reference: list[str] = Field(description="Arômes sans référence : création sur mesure.")


class Projet(BaseModel):
    division: str | None
    type_de_produit: str | None
    arome_principal: str | None
    profil_recherche: list[str]
    contraintes: list[str]


class BriefFinal(BaseModel):
    division: str | None
    type_de_produit: str | None
    piste: int
    aromes: list[str]
    profil: list[str]
    contraintes: list[str]
    codes_references: list[str]
    codes_solutions: list[str]
    creation_sur_mesure: list[str]
    brief_du_client: str


class DemandeEchantillons(BriefFinal):
    statut: str = Field(examples=["brouillon, non envoyé (prototype)"])
    date: str


class PisteChoisie(BaseModel):
    numero: int
    aromes: str


class ReponseConversation(BaseModel):
    conversation_id: str
    intention: Literal["nouvelle_demande", "precision", "question_piste", "choix_piste",
                       "demande_echantillons", "hors_sujet"]
    texte: str = Field(description="Réponse à afficher (paragraphes séparés par \n).")
    projet: Projet
    pistes: list[Piste]
    solutions: list[Reference]
    piste_choisie: PisteChoisie | None
    brief_final: BriefFinal | None
    demande_echantillons: DemandeEchantillons | None = Field(
        description="Récapitulatif à afficher ; rien n'est envoyé.")
    version_modele: str
    attribution: str


EXEMPLES_CONVERSATION = {
    "debut": {"summary": "Nouvelle conversation",
              "value": {"message": "je voudrais créer une boisson"}},
    "suite": {"summary": "Suite d'une conversation",
              "value": {"conversation_id": "remplacer-par-l-id-recu",
                        "message": "pétillante, goût citron vert, pas trop sucrée"}},
}


def _conversation(conversation_id: str | None) -> tuple[str, dict]:
    """Conversation existante, ou nouvelle si l'identifiant est absent, inconnu ou expire."""
    maintenant = time.time()
    with verrou_conversations:
        for cle in [c for c, v in conversations.items() if maintenant - v["vu"] > DUREE_CONVERSATION]:
            del conversations[cle]
        if conversation_id not in conversations:
            if len(conversations) >= MAX_CONVERSATIONS:
                del conversations[min(conversations, key=lambda c: conversations[c]["vu"])]
            conversation_id = conversation_id or uuid.uuid4().hex[:12]
            conversations[conversation_id] = {"assistant": AssistantV22(moteur_v22, noms_du_commerce),
                                              "verrou": threading.Lock()}
        conversations[conversation_id]["vu"] = maintenant
        return conversation_id, conversations[conversation_id]


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


@app.post("/conversation", response_model=ReponseConversation, tags=["conversation"],
          summary="Assistant V2.2 : un message du client, la réponse et l'état du brief")
def conversation(demande: MessageConversation = Body(openapi_examples=EXEMPLES_CONVERSATION)
                 ) -> ReponseConversation:
    conversation_id, session = _conversation(demande.conversation_id)
    with session["verrou"]:  # messages d'une meme conversation traites dans l'ordre
        r = session["assistant"].repondre(demande.message, reformuler=demande.reformuler)
    return ReponseConversation(
        conversation_id=conversation_id, intention=r["intention"], texte=r["texte"],
        projet=r["projet"], pistes=r["pistes"], solutions=r["solutions"],
        piste_choisie=r["piste_choisie"], brief_final=r["brief_final"],
        demande_echantillons=r["demande_echantillons"], version_modele=VERSION_V22,
        attribution=ATTRIBUTION_V22,
    )

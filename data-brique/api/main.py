"""API de la brique Data.

- POST /recommander : brief client -> top k produits (baseline V1, inchange).
- POST /conversation : assistant conversationnel V2.2 (pistes d'aromes, references DEMO,
  demande d'echantillons), un message par appel, etat garde par session_id.

Lancement (depuis data-brique/) : .venv/Scripts/uvicorn api.main:app --port 8000
Swagger : http://127.0.0.1:8000/docs
"""
import threading
import time
import uuid
import re
import unicodedata
from functools import lru_cache
from contextlib import asynccontextmanager
from typing import Literal

import pandas as pd
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from src.moteur_v1 import CATALOGUE_DEFAUT, VERSION_MODELE, MoteurV1
from src.moteur_v2 import CATALOGUE_COMPLET
from src.moteur_v22 import ATTRIBUTION as ATTRIBUTION_V22
from src.moteur_v22 import VERSION_V22, AssistantV22, MoteurV22, NomsDuCommerce
from src.moteur_v22 import BANQUE_DEFAUT, TYPES, SOUS_TYPES, PROFILS

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

# sessions en memoire (prototype) : au plus MAX_SESSIONS, oubliees apres DUREE_SESSION
MAX_SESSIONS = 500
DUREE_SESSION = 2 * 3600  # secondes d'inactivite
sessions: dict[str, dict] = {}  # session_id -> {"assistant", "verrou", "vu"}
verrou_sessions = threading.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # index TF-IDF construit une fois au demarrage (~1 s) ; moteur V2.2 partage entre les
    # sessions, modeles et vecteurs precharges (sans Ollama, l'assistant passe en repli)
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
    guidage: bool = Field(default=False, description="Active les questions à choix issues du catalogue avant les pistes.")
    session_id: str | None = Field(
        default=None, max_length=64,
        description="null, absent ou inconnu : nouvelle session (l'identifiant est renvoyé).")
    message: str = Field(default="", max_length=500,
                         description="Message du client, en français. Peut être vide si piste_id est fourni.")
    piste_id: str | None = Field(
        default=None, max_length=200,
        description="Optionnel : choix de cette piste (id d'une piste de la dernière réponse), "
                    "quel que soit le message.")

    @model_validator(mode="after")
    def _message_ou_piste(self):
        if not self.message.strip() and not self.piste_id:
            raise ValueError("message vide : fournir un message ou un piste_id")
        return self


Etape = Literal["relance", "affiner", "pistes", "recapitulatif", "echantillons"]
Intention = Literal["nouvelle_demande", "precision", "question", "question_piste", "choix_piste",
                    "demande_echantillons", "hors_sujet"]


class Reference(BaseModel):
    code: str = Field(description="Code fictif DEMO-001 à DEMO-030 (banque de démo).")
    nom: str
    profil_sensoriel: str
    forme: Literal["soluble eau", "huile", "poudre"]
    labels: list[str]


class ReferenceSansLabel(BaseModel):
    arome: str = Field(examples=["chocolat"])
    code: str = Field(description="Référence qui existe, mais sans le label demandé.",
                      examples=["DEMO-020"])
    label_manquant: str = Field(examples=["bio"])


class Compris(BaseModel):
    division: Literal["flavors", "fragrance"] | None
    type_produit: str | None = Field(examples=["boisson pétillante"])
    arome: str | None = Field(description="Arôme principal.", examples=["citron vert"])
    aromes: list[str] = Field(description="Arômes cités par le client, le principal en premier.")
    contraintes: list[str] = Field(examples=[["peu sucré", "bio"]])
    profil: list[str] = Field(default=[], description="Ajout V2.2.2 : profil recherché.",
                              examples=[["frais", "exotique", "acidulé"]])
    volume: str | None = Field(default=None, description="Volume exprimé par le client, avec son unité.")


class Piste(BaseModel):
    id: str = Field(description="Stable d'un message à l'autre tant que la piste est proposée.",
                    examples=["citron-vert+citron"])
    rang: int = Field(ge=1, le=3)
    nom: str = Field(examples=["Citron vert + citron"])
    description: str = Field(examples=["L'association la plus courante"])
    explication: str
    aromes: list[str]
    nb_produits_marche: int = Field(description="Produits du marché étudié qui justifient la piste.")
    references: list[Reference]
    sans_reference: list[str] = Field(description="Arômes sans référence : création sur mesure.")
    references_sans_label: list[ReferenceSansLabel] = Field(
        default=[], description="Ajout V2.2.2 : arômes dont la référence n'a pas le label demandé.")
    image: None = Field(default=None, description="Toujours null en V2 : visuel par défaut côté front.")


class QuestionAffiner(BaseModel):
    id: str = Field(examples=["gout"], description="« gout » ou « intensite ».")
    question: str = Field(examples=["Quel goût de fraise imaginez-vous ?"])
    choix: list[str] = Field(description="Choix a afficher en boutons ; le dernier est toujours "
                                         "« Je ne sais pas, proposez-moi ». Le choix clique est "
                                         "envoye tel quel comme message.",
                             examples=[["fraise des bois", "fraise mûre", "sucrée", "juteuse",
                                        "Je ne sais pas, proposez-moi"]])


class Brief(BaseModel):
    type_produit: str | None
    piste_id: str
    aromes: list[str]
    contraintes: list[str]
    codes_references: list[str]
    codes_solutions: list[str]
    creation_sur_mesure: list[str]
    references_sans_label: list[ReferenceSansLabel] = Field(
        default=[], description="Ajout V2.2.2 : arômes dont la référence n'a pas le label demandé.")
    profil: list[str] = Field(default=[], description="Ajout V2.2.2 : profil recherché.")
    volume: str | None = Field(default=None, description="Ajout V2.2.2 : volume cité par le client, "
                                                         "tel quel (ex. « 5 000 bouteilles »).")


class Echantillons(Brief):
    statut: Literal["brouillon_non_envoye"]
    date: str = Field(examples=["2026-11-12"])
    brief_client: str = Field(description="Messages du client qui ont construit le brief.")


class QuestionClarification(BaseModel):
    id: str
    question: str
    choix: list[str] = Field(default_factory=list)


class ReponseConversation(BaseModel):
    session_id: str
    etape: Etape = Field(description="État de la session après ce message.")
    intention: Intention = Field(description="Intention du dernier message du client.")
    reponse: str = Field(description="Texte à afficher (paragraphes séparés par \\n).")
    compris: Compris
    questions: list[QuestionAffiner] = Field(
        default=[], description="Ajout V2.3 : questions Affiner quand etape = affiner ; avec "
                    "guidage, question de type de produit sur une relance ; vide sinon.")
    pistes: list[Piste]
    solutions: list[Reference]
    brief: Brief | None = Field(description="null tant qu'aucune piste n'est choisie.")
    echantillons: Echantillons | None = Field(
        description="Brouillon de demande d'échantillons ; rien n'est envoyé.")
    version_modele: str
    attribution: str


DESCRIPTIONS_PISTE = {"principal": "L'arôme seul", "association_frequente": "L'association la plus courante",
                      "association_originale": "L'association originale"}
EXEMPLES_CONVERSATION = {
    "debut": {"summary": "Nouvelle session",
              "value": {"session_id": None, "message": "je voudrais créer une boisson"}},
    "suite": {"summary": "Suite d'une session",
              "value": {"session_id": "remplacer-par-l-id-recu",
                        "message": "pétillante, goût citron vert, pas trop sucrée"}},
    "choix": {"summary": "Choix d'une piste (bouton)",
              "value": {"session_id": "remplacer-par-l-id-recu", "message": "",
                        "piste_id": "citron-vert"}},
}


def _session(session_id: str | None) -> tuple[str, dict]:
    """Session existante, ou nouvelle si l'identifiant est absent, inconnu ou expire."""
    maintenant = time.time()
    with verrou_sessions:
        for cle in [c for c, v in sessions.items() if maintenant - v["vu"] > DUREE_SESSION]:
            del sessions[cle]
        if session_id not in sessions:
            if len(sessions) >= MAX_SESSIONS:
                del sessions[min(sessions, key=lambda c: sessions[c]["vu"])]
            # Un identifiant oublié doit signaler une nouvelle session au front.
            session_id = uuid.uuid4().hex
            sessions[session_id] = {"assistant": AssistantV22(moteur_v22, noms_du_commerce),
                                    "verrou": threading.Lock()}
        sessions[session_id]["vu"] = maintenant
        return session_id, sessions[session_id]


def vers_contrat(session_id: str, r: dict) -> ReponseConversation:
    """Sortie de AssistantV22.repondre() -> contrat V2 envoye aux Tech (objet complet)."""
    pistes = [Piste(id=p["id"], rang=p["numero"], nom=p["aromes"][0].upper() + p["aromes"][1:],
                    description=DESCRIPTIONS_PISTE[p["type"]], explication=p["explication"],
                    aromes=p["liste_aromes"], nb_produits_marche=p["nb_produits"],
                    references=p["references"], sans_reference=p["sans_reference"],
                    references_sans_label=p["references_sans_label"])
              for p in r["pistes"]]
    brief = None
    if r["brief_final"]:
        b = r["brief_final"]
        brief = {"type_produit": b["type_de_produit"], "piste_id": pistes[b["piste"] - 1].id,
                 "aromes": b["aromes"], "contraintes": b["contraintes"],
                 "codes_references": b["codes_references"], "codes_solutions": b["codes_solutions"],
                 "creation_sur_mesure": b["creation_sur_mesure"],
                 "references_sans_label": b["references_sans_label"], "profil": b["profil"],
                 "volume": b["volume"]}
    echantillons = None
    if r["demande_echantillons"] and brief:  # brouillon renvoye tant qu'il est valide
        echantillons = {**brief, "statut": "brouillon_non_envoye",
                        "date": r["demande_echantillons"]["date"],
                        "brief_client": r["demande_echantillons"]["brief_du_client"]}
    compris = {**r["compris"], "volume": r["projet"].get("volume")}
    return ReponseConversation(
        session_id=session_id, etape=r["etape"], intention=r["intention"], reponse=r["texte"],
        questions=r["questions"],
        compris=compris, pistes=pistes, solutions=r["solutions"], brief=brief,
        echantillons=echantillons, version_modele=VERSION_V22, attribution=ATTRIBUTION_V22)


def _normaliser_question(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower())
                   if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def _references_questions() -> list[dict]:
    return pd.read_csv(BANQUE_DEFAUT).fillna("").to_dict("records")


def _guider(reponse: ReponseConversation, session: dict, demande: MessageConversation) -> ReponseConversation:
    """Guidage optionnel : les choix viennent des types et des profils Data, pas du front."""
    if not demande.guidage:
        return reponse
    compris = reponse.compris
    if reponse.intention == "nouvelle_demande":
        session.pop("guidage_cle", None)
        session.pop("question_profil", None)
    if reponse.etape == "relance":
        produit = compris.type_produit
        if not produit or produit in SOUS_TYPES:
            choix = [nom for nom, configuration in TYPES.items()
                     if configuration[-1] == produit][:6]
            reponse.questions = [QuestionClarification(id="type_produit", question=reponse.reponse,
                                                       choix=choix)]
        return reponse
    if reponse.etape != "pistes" or demande.piste_id:
        return reponse
    if session["assistant"].projet.get("affiner_fait"):
        return reponse  # etape Affiner du moteur (V2.3) deja faite : pas de 2e serie de questions
    pending = session.pop("question_profil", None)
    if pending and demande.message.strip() != "Je ne sais pas, proposez-moi" and reponse.intention in ("question", "question_piste", "hors_sujet"):
        reponse.etape = "affiner"
        reponse.pistes = []
        reponse.questions = [pending]
        reponse.reponse += "\n" + pending.question
        session["question_profil"] = pending
        return reponse
    cle = (compris.type_produit, tuple(compris.aromes))
    if compris.profil or compris.contraintes or session.get("guidage_cle") == cle:
        return reponse
    textes = " ".join(str(reference["profil_sensoriel"]) for reference in _references_questions()
                      if compris.arome and _normaliser_question(compris.arome)
                      in _normaliser_question(str(reference["nom"])))
    choix = [profil for profil, motif in PROFILS.items()
             if re.search(motif, _normaliser_question(textes))][:3]
    if not choix:
        return reponse
    question = QuestionClarification(id="profil", question=f"Quel profil recherchez-vous pour {compris.arome} ?",
                                     choix=[*choix, "Je ne sais pas, proposez-moi"])
    session["guidage_cle"] = cle
    session["question_profil"] = question
    reponse.etape = "affiner"
    reponse.pistes = []
    reponse.questions = [question]
    reponse.reponse = question.question
    session["assistant"].historique[-1]["content"] = reponse.reponse
    return reponse


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
          summary="Assistant V2.2 : un message du client, la réponse et l'état complet de la session",
          responses={422: {"description": "message vide sans piste_id, ou piste_id inconnu"}})
def conversation(demande: MessageConversation = Body(openapi_examples=EXEMPLES_CONVERSATION)
                 ) -> ReponseConversation:
    session_id, session = _session(demande.session_id)
    with session["verrou"]:  # messages d'une meme session traites dans l'ordre
        try:
            r = session["assistant"].repondre(demande.message.strip(), piste_id=demande.piste_id)
        except ValueError as erreur:
            raise HTTPException(status_code=422, detail=str(erreur)) from erreur
        return _guider(vers_contrat(session_id, r), session, demande)

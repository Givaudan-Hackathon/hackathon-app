"""Appli Streamlit « Givaudan AI Challenge » : parcours client en 4 etapes, avec l'API actuelle.

Usage (depuis data-brique/, l'API lancee sur le port 8000) :
  .venv/Scripts/streamlit run demo_parcours.py --server.port 8502
Etapes : 1 Decrire · 2 Affiner · 3 Choisir · 4 Demander un echantillon. L'appli n'appelle que
POST /conversation (contrat V2) : elle ne charge aucun modele et n'importe pas le moteur.
Les choix « Affiner » n'envoient que des mots que le moteur comprend deja (PROFILS et
CONTRAINTES de src/moteur_v22.py). Les coordonnees saisies ne sont ni envoyees ni enregistrees.
"""
import os
import time

import requests
import streamlit as st

API = os.environ.get("API_DATA_URL", "http://127.0.0.1:8000").rstrip("/")
DELAI = 60
ETAPES = ["Décrire", "Affiner", "Choisir", "Demander un échantillon"]
EXEMPLES = ["une boisson pétillante au citron vert, pas trop sucrée",
            "un kombucha d'été au fruit de la passion, naturel"]
# mots compris par le moteur : PROFILS et CONTRAINTES de src/moteur_v22.py
PROFILS = ["frais", "gourmand", "fruité", "acidulé", "doux", "intense", "exotique"]
CONTRAINTES = ["peu sucré", "bio", "vegan", "naturel"]
BADGES = {1: ("Très proche", "#1f6f43", "#e3f2e9"), 2: ("Proche", "#1d4f7a", "#e2edf7"),
          3: ("Alternative", "#6b4e16", "#f5edde")}
STADES = ["Je teste une recette", "Je prépare un lancement", "Je produis déjà"]
QUANTITES = {"Moins de 500 kg": "moins de 500 kg par mois",
             "500 kg à 5 t": "entre 500 kg et 5 tonnes par mois",
             "Plus de 5 t": "plus de 5 tonnes par mois", "Je ne sais pas encore": None}
ATTRIBUTION = "Étude de marché réalisée sur des données d'Open Food Facts (ODbL)"

st.set_page_config(page_title="Givaudan AI Challenge · parcours", page_icon="🍋", layout="wide")
st.markdown("""
<style>
.barre {display:flex; gap:.5rem; margin:.2rem 0 1rem 0; flex-wrap:wrap}
.barre span {padding:.35rem .8rem; border-radius:999px; background:#f1f1ef; color:#777; font-size:.9rem}
.barre span.active {background:#1d1d1b; color:#fff}
.barre span.faite {background:#e6e3dc; color:#333}
.chip {display:inline-block; padding:.15rem .6rem; margin:.15rem; border-radius:999px;
       background:#f1efe9; border:1px solid #e0dcd2; font-size:.85rem}
.badge {display:inline-block; padding:.1rem .55rem; border-radius:6px; font-size:.8rem; font-weight:600}
.sous-titre {color:#666; margin-top:-.6rem}
.ref {font-size:.9rem; margin:.2rem 0}
</style>""", unsafe_allow_html=True)


# --- etat ---------------------------------------------------------------------------------------

def nouvelle_recherche() -> None:
    st.session_state.update(session_id=None, etat=None, ecran=0, pile=[], erreur=None,
                            secondes=None, description="", pas_convenu=False, quantite=None)


if "ecran" not in st.session_state:
    nouvelle_recherche()


def aller(ecran: int) -> None:
    st.session_state.pile.append(st.session_state.ecran)
    st.session_state.ecran = ecran


def retour() -> None:
    if st.session_state.pile:
        st.session_state.ecran = st.session_state.pile.pop()


def envoyer(message: str, piste_id: str | None = None) -> dict | None:
    """POST /conversation (contrat V2) ; garde la derniere reponse complete dans l'etat."""
    st.session_state.erreur = None
    corps = {"session_id": st.session_state.session_id, "message": message, "piste_id": piste_id}
    debut = time.perf_counter()
    try:
        reponse = requests.post(f"{API}/conversation", json=corps, timeout=DELAI)
    except requests.RequestException:
        st.session_state.erreur = (f"L'API ne répond pas sur {API}. Lancez-la depuis data-brique/ : "
                                   "`.venv/Scripts/uvicorn api.main:app --host 127.0.0.1 --port 8000`")
        return None
    st.session_state.secondes = time.perf_counter() - debut
    if reponse.status_code != 200:
        try:
            detail = reponse.json().get("detail")
        except ValueError:
            detail = reponse.text[:300]
        st.session_state.erreur = f"Erreur HTTP {reponse.status_code} : {detail}"
        return None
    etat = reponse.json()
    st.session_state.session_id = etat["session_id"]
    st.session_state.etat = etat
    return etat


def decrire(message: str) -> None:
    if not message.strip():
        st.session_state.erreur = "Décrivez votre produit en quelques mots."
        return
    st.session_state.description = message
    etat = envoyer(message)
    if etat and etat["etape"] == "pistes":
        aller(2)
    elif etat and etat["etape"] == "affiner":  # questions de l'API avant les pistes
        aller(1)


def affiner(mot: str) -> None:
    etat = envoyer(mot)
    if etat and etat["etape"] == "pistes" and st.session_state.ecran == 1:
        aller(2)  # reponse a une question Affiner : les pistes arrivent


def choisir(piste: dict) -> None:
    envoyer("", piste_id=piste["id"])


def pas_convenu(texte: str) -> None:
    if texte.strip():
        envoyer(texte)
        st.session_state.pas_convenu = False


def demander_echantillon() -> None:
    message = QUANTITES.get(st.session_state.quantite or "")
    if message:
        envoyer(message)  # remplit brief.volume
    envoyer("je veux des échantillons")


# --- elements communs ---------------------------------------------------------------------------

def barre() -> None:
    cases = []
    for i, nom in enumerate(ETAPES):
        classe = "active" if i == st.session_state.ecran else "faite" if i < st.session_state.ecran else ""
        cases.append(f'<span class="{classe}">{i + 1} {nom}</span>')
    st.markdown('<div class="barre">' + "".join(cases) + "</div>", unsafe_allow_html=True)


def compris() -> None:
    etat = st.session_state.etat
    if not etat:
        return
    c = etat["compris"]
    chips = ([c["type_produit"]] if c["type_produit"] else []) + ([c["arome"]] if c["arome"] else []) \
        + c.get("profil", []) + c["contraintes"]
    if chips:
        st.markdown("**Ce que nous avons compris** " + "".join(f'<span class="chip">{x}</span>' for x in chips),
                    unsafe_allow_html=True)


def navigation() -> None:
    gauche, droite, _ = st.columns([1, 1.4, 5])
    gauche.button("← Retour", on_click=retour, disabled=not st.session_state.pile, width="stretch")
    droite.button("Nouvelle recherche", on_click=nouvelle_recherche, width="stretch")


def reference(r: dict) -> None:
    labels = " ".join(f'<span class="chip">{l}</span>' for l in r["labels"])
    st.markdown(f'<div class="ref"><b>{r["code"]}</b> · {r["nom"]}<br>'
                f'<span style="color:#555">{r["profil_sensoriel"]} · {r["forme"]}</span><br>{labels}</div>',
                unsafe_allow_html=True)


# --- ecrans -------------------------------------------------------------------------------------

def ecran_decrire() -> None:
    st.header("Décrivez votre produit, nous trouvons les arômes qui lui ressemblent")
    st.markdown('<p class="sous-titre">Avec vos mots, comme à un collègue. Pas besoin de fiche technique.</p>',
                unsafe_allow_html=True)
    texte = st.text_area("Votre produit", value=st.session_state.description, height=110,
                         label_visibility="collapsed",
                         placeholder="Ex. une boisson pétillante au citron vert, pas trop sucrée")
    st.button("Trouver mes arômes", type="primary", on_click=decrire, args=(texte,))
    st.caption("Exemples :")
    for i, exemple in enumerate(EXEMPLES):
        st.button(f"« {exemple} »", key=f"exemple-{i}", on_click=decrire, args=(exemple,))
    etat = st.session_state.etat
    if etat and etat["etape"] == "relance":
        st.info(etat["reponse"])
        compris()
        st.button("Affiner avec des choix", on_click=aller, args=(1,))
    elif etat and etat["etape"] != "relance":
        st.button("Voir mes arômes →", on_click=aller, args=(2,))


def ecran_affiner() -> None:
    st.header("Affinons votre projet")
    compris()
    etat = st.session_state.etat
    if etat and etat["etape"] == "affiner" and etat.get("questions"):
        # questions generees par l'API (variantes du catalogue, profils DEMO, intensite)
        for question in etat["questions"]:
            st.markdown(f"**{question['question']}**")
            colonnes = st.columns(len(question["choix"]))
            for colonne, choix in zip(colonnes, question["choix"]):
                colonne.button(choix, key=f"question-{question['id']}-{choix}", on_click=affiner,
                               args=(choix,), width="stretch",
                               type="secondary" if choix.startswith("Je ne sais pas") else "primary")
        return
    if etat and etat["etape"] == "relance":
        st.info(etat["reponse"])
    st.markdown("**Quel profil recherchez-vous ?**")
    colonnes = st.columns(len(PROFILS))
    for colonne, mot in zip(colonnes, PROFILS):
        colonne.button(mot, key=f"profil-{mot}", on_click=affiner, args=(mot,), width="stretch")
    st.markdown("**Des contraintes ?**")
    colonnes = st.columns(len(CONTRAINTES) + 1)
    for colonne, mot in zip(colonnes, CONTRAINTES):
        colonne.button(mot, key=f"contrainte-{mot}", on_click=affiner, args=(mot,), width="stretch")
    colonnes[-1].button("Je ne sais pas", key="passer",
                        on_click=aller, args=(2 if etat and etat["pistes"] else 0,), width="stretch")
    if etat and etat["pistes"]:
        st.button("Voir mes arômes →", type="primary", on_click=aller, args=(2,))


def ecran_choisir() -> None:
    etat = st.session_state.etat
    if not etat or not etat["pistes"]:
        st.warning("Décrivez d'abord votre produit.")
        st.button("Modifier ma description", on_click=aller, args=(0,))
        return
    if not any(p["references"] for p in etat["pistes"]):
        st.header("Nous n'avons pas encore d'arôme assez proche de votre projet")
        st.write(etat["reponse"].split("\n")[0])
        compris()
        st.button("Modifier ma description", type="primary", on_click=aller, args=(0,))
        return
    st.header("Voici 3 arômes qui ressemblent à votre projet")
    compris()
    brief = etat["brief"]
    colonnes = st.columns(len(etat["pistes"]))
    for colonne, piste in zip(colonnes, etat["pistes"]):
        texte, couleur, fond = BADGES.get(piste["rang"], BADGES[3])
        choisie = brief and brief["piste_id"] == piste["id"]
        with colonne, st.container(border=True):
            st.markdown(f'<span class="badge" style="color:{couleur};background:{fond}">{texte}</span>'
                        + (' <span class="badge" style="background:#1d1d1b;color:#fff">Choisi</span>'
                           if choisie else ""), unsafe_allow_html=True)
            st.subheader(piste["nom"])
            for r in piste["references"]:
                reference(r)
            st.markdown(f"**Pourquoi :** {piste['explication']}")
            if piste["sans_reference"]:
                st.caption(f"Création sur mesure : {', '.join(piste['sans_reference'])}")
            for s in piste.get("references_sans_label", []):
                st.caption(f"Pas en version {s['label_manquant']} : {s['code']} ({s['arome']})")
            st.button("Choisir", key=f"choisir-{piste['id']}", on_click=choisir, args=(piste,),
                      type="secondary" if choisie else "primary", width="stretch")
    if etat["solutions"]:
        st.markdown("**Ajouté pour vos contraintes**")
        for s in etat["solutions"]:
            reference(s)
    if brief:
        nom = next(p["nom"] for p in etat["pistes"] if p["id"] == brief["piste_id"])
        st.success(etat["reponse"])
        st.button(f"Demander un échantillon de « {nom} »", type="primary", on_click=aller, args=(3,))
    st.divider()
    if st.session_state.pas_convenu:
        texte = st.text_area("Dites-nous ce qui ne convient pas", key="pas-convenu-texte")
        st.button("Envoyer", on_click=pas_convenu, args=(texte,))
    else:
        st.button("Aucun ne me convient", on_click=lambda: st.session_state.update(pas_convenu=True))


def ecran_echantillon() -> None:
    etat = st.session_state.etat
    if not etat or not etat["brief"]:
        st.warning("Choisissez d'abord un arôme.")
        st.button("Voir les arômes", on_click=aller, args=(2,))
        return
    if etat["echantillons"]:
        e = etat["echantillons"]
        st.header("Votre demande d'échantillon")
        st.success("Demande prête — prototype : rien n'est envoyé. Un expert Givaudan reprendrait contact.")
        with st.container(border=True):
            st.markdown(f"- **Produit :** {e['type_produit']}\n- **Arômes :** {', '.join(e['aromes'])}\n"
                        f"- **Références :** {', '.join(e['codes_references'] + e['codes_solutions']) or '—'}\n"
                        f"- **Contraintes :** {', '.join(e['contraintes']) or '—'}\n"
                        f"- **Quantité :** {st.session_state.quantite or '—'}"
                        + (f" (brief : {e['volume']})" if e.get("volume") else "")
                        + (f"\n- **Création sur mesure :** {', '.join(e['creation_sur_mesure'])}"
                           if e["creation_sur_mesure"] else "")
                        + f"\n- **Date :** {e['date']} · statut `{e['statut']}`")
        return
    st.header("Demander un échantillon")
    st.radio("Où en êtes-vous ?", STADES, key="stade", index=None)
    st.radio("Quelle quantité de produit fini par mois ?", list(QUANTITES), key="quantite", index=None)
    st.markdown("**Vos coordonnées**")
    st.caption("Prototype : ces informations ne sont ni envoyées ni enregistrées.")
    gauche, droite = st.columns(2)
    gauche.text_input("Nom", key="nom")
    droite.text_input("Société", key="societe")
    gauche.text_input("E-mail", key="email")
    droite.text_input("Téléphone (facultatif)", key="telephone")
    st.button("Préparer ma demande", type="primary", on_click=demander_echantillon)


# --- page ---------------------------------------------------------------------------------------

st.warning("**Codes DEMO fictifs — prototype.** Les références DEMO-xxx ne sont pas de vraies "
           "références Givaudan ; aucune demande n'est envoyée.")
barre()
[ecran_decrire, ecran_affiner, ecran_choisir, ecran_echantillon][st.session_state.ecran]()
if st.session_state.erreur:
    st.error(st.session_state.erreur)
st.divider()
navigation()
attribution = st.session_state.etat["attribution"] if st.session_state.etat else ATTRIBUTION
temps = f" · réponse en {st.session_state.secondes:.1f} s" if st.session_state.secondes else ""
st.caption(f"{attribution} · Codes DEMO fictifs — prototype{temps}")

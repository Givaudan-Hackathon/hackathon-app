"""Appli Streamlit de test du contrat V2 : chat avec l'assistant via POST /conversation.

Usage (depuis data-brique/, l'API lancee sur le port 8000) :
  .venv/Scripts/streamlit run demo_streamlit.py --server.port 8501
L'appli n'appelle que l'API (variable d'environnement API_DATA_URL, defaut
http://127.0.0.1:8000) : elle ne charge aucun modele et n'importe pas le moteur.
"""
import os
import time

import requests
import streamlit as st

API = os.environ.get("API_DATA_URL", "http://127.0.0.1:8000").rstrip("/")
DELAI = 60  # secondes : un message qui demande le modele prend environ 5 s
COULEURS_LABELS = {"bio": "green", "vegan": "green", "naturel": "blue", "halal": "violet",
                   "casher": "violet", "sans allergène": "orange"}

st.set_page_config(page_title="Assistant arômes · test API V2", page_icon="🍋", layout="wide")


# --- etat de la session Streamlit -----------------------------------------------------------------

def nouvelle_conversation() -> None:
    st.session_state.session_id = None
    st.session_state.historique = []  # [{"role", "texte", "donnees", "secondes"}]
    st.session_state.erreur = None


if "historique" not in st.session_state:
    nouvelle_conversation()


def envoyer(message: str, piste_id: str | None = None, affiche: str | None = None) -> None:
    """Appelle POST /conversation (contrat V2) et ajoute l'echange a l'historique."""
    st.session_state.erreur = None
    corps = {"session_id": st.session_state.session_id, "message": message, "piste_id": piste_id}
    debut = time.perf_counter()
    try:
        reponse = requests.post(f"{API}/conversation", json=corps, timeout=DELAI)
    except requests.ConnectionError:
        st.session_state.erreur = (f"L'API ne répond pas sur {API}. Lancez-la depuis data-brique/ : "
                                   "`.venv/Scripts/uvicorn api.main:app --host 127.0.0.1 --port 8000`")
        return
    except requests.Timeout:
        st.session_state.erreur = f"L'API n'a pas répondu en {DELAI} s ({API})."
        return
    secondes = time.perf_counter() - debut
    if reponse.status_code != 200:
        try:
            detail = reponse.json().get("detail")
        except ValueError:
            detail = reponse.text[:300]
        st.session_state.erreur = f"Erreur HTTP {reponse.status_code} : {detail}"
        return
    donnees = reponse.json()
    st.session_state.session_id = donnees["session_id"]
    st.session_state.historique += [
        {"role": "user", "texte": affiche or message},
        {"role": "assistant", "texte": donnees["reponse"], "donnees": donnees, "secondes": secondes}]


def choisir(piste: dict) -> None:
    envoyer("", piste_id=piste["id"], affiche=f"Je choisis la piste {piste['rang']} : {piste['nom']}")


# --- affichage d'une reponse ---------------------------------------------------------------------

def labels(liste: list[str]) -> str:
    return " ".join(f":{COULEURS_LABELS.get(l, 'gray')}-badge[{l}]" for l in liste)


def reference(r: dict) -> None:
    st.markdown(f"**{r['code']}** · {r['nom']}  \n{r['profil_sensoriel']} · *{r['forme']}*")
    if r["labels"]:
        st.markdown(labels(r["labels"]))


def carte_piste(piste: dict, cle: str, active: bool) -> None:
    with st.container(border=True):
        st.markdown(f"#### {piste['rang']}. {piste['nom']}")
        st.caption(f"{piste['description']} · {piste['nb_produits_marche']} produit(s) du marché")
        st.markdown(" + ".join(f"`{a}`" for a in piste["aromes"]))
        st.write(piste["explication"])
        if piste["references"]:
            st.markdown("**Références DEMO**")
            for r in piste["references"]:
                reference(r)
        if piste["sans_reference"]:
            st.info(f"Création sur mesure : aucune référence pour {', '.join(piste['sans_reference'])}.")
        if active:
            st.button("Choisir", key=cle, on_click=choisir, args=(piste,), type="primary",
                      width="stretch")


def details(donnees: dict, index: int, secondes: float, dernier: bool) -> None:
    st.caption(f"étape **{donnees['etape']}** · intention **{donnees['intention']}** · "
               f"⏱ {secondes:.2f} s")
    if donnees["pistes"]:
        # boutons « Choisir » seulement sous la derniere reponse (les pistes ont pu changer depuis)
        with st.expander(f"Pistes ({len(donnees['pistes'])})", expanded=dernier):
            colonnes = st.columns(len(donnees["pistes"]))
            for colonne, piste in zip(colonnes, donnees["pistes"]):
                with colonne:
                    carte_piste(piste, f"choisir-{index}-{piste['id']}",
                                active=dernier and donnees["etape"] == "pistes")
    if donnees["solutions"] and dernier:
        st.markdown("**Solutions ajoutées pour vos contraintes**")
        for s in donnees["solutions"]:
            with st.container(border=True):
                reference(s)
    if donnees["brief"] and dernier:
        b = donnees["brief"]
        with st.container(border=True):
            st.markdown("**Brief**")
            st.markdown(f"- Type de produit : {b['type_produit']}\n- Piste : `{b['piste_id']}`\n"
                        f"- Arômes : {', '.join(b['aromes'])}\n"
                        f"- Contraintes : {', '.join(b['contraintes']) or '—'}\n"
                        f"- Références : {', '.join(b['codes_references']) or '—'}\n"
                        f"- Solutions : {', '.join(b['codes_solutions']) or '—'}"
                        + (f"\n- Création sur mesure : {', '.join(b['creation_sur_mesure'])}"
                           if b["creation_sur_mesure"] else ""))
    if donnees["echantillons"] and dernier:
        e = donnees["echantillons"]
        with st.container(border=True):
            st.markdown("**Demande d'échantillons** :orange-badge[brouillon, non envoyé]")
            st.markdown(f"- Codes : {', '.join(e['codes_references'] + e['codes_solutions'])}\n"
                        f"- Type de produit : {e['type_produit']} · piste `{e['piste_id']}`\n"
                        f"- Contraintes : {', '.join(e['contraintes']) or '—'}\n"
                        f"- Date : {e['date']} · statut `{e['statut']}`\n"
                        f"- Brief du client : {e['brief_client']}")
            st.caption("L'enregistrement réel de la demande relève de l'API applicative (équipe Tech).")


# --- page ----------------------------------------------------------------------------------------

st.title("Assistant arômes · test de l'API V2")
st.warning("**Codes DEMO fictifs — prototype.** Les références DEMO-xxx ne sont pas de vraies "
           "références Givaudan ; aucune demande d'échantillons n'est envoyée.")

with st.sidebar:
    st.subheader("Session")
    st.button("Nouvelle conversation", on_click=nouvelle_conversation, width="stretch")
    st.caption(f"session_id : `{st.session_state.session_id}`")
    st.subheader("API")
    st.caption(f"{API}/conversation")
    try:
        sante = requests.get(f"{API}/sante", timeout=3).json()
        st.success(f"API en ligne ({sante.get('version_modele')})")
    except (requests.RequestException, ValueError):
        st.error("API injoignable")
    reponses = [m for m in st.session_state.historique if m["role"] == "assistant"]
    if reponses:
        temps = [m["secondes"] for m in reponses]
        st.caption(f"{len(temps)} réponse(s) · moyenne {sum(temps) / len(temps):.2f} s · "
                   f"max {max(temps):.2f} s")

if not st.session_state.historique:
    st.info("Exemple : « je voudrais créer une boisson », puis « pétillante, goût citron vert, pas "
            "trop sucrée », « elle doit être bio »…")

dernier_assistant = max((i for i, m in enumerate(st.session_state.historique)
                         if m["role"] == "assistant"), default=None)
for i, m in enumerate(st.session_state.historique):
    with st.chat_message(m["role"]):
        st.markdown(m["texte"].replace("\n", "  \n"))
        if m["role"] == "assistant":
            details(m["donnees"], i, m["secondes"], dernier=i == dernier_assistant)

if st.session_state.erreur:
    st.error(st.session_state.erreur)

attribution = (reponses[-1]["donnees"]["attribution"] if reponses else
               "Étude de marché réalisée sur des données d'Open Food Facts (ODbL)")
st.caption(f"{attribution} · Codes DEMO fictifs — prototype")

if message := st.chat_input("Décrivez votre projet…"):
    envoyer(message)
    st.rerun()

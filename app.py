import streamlit as st
import sqlite3
from datetime import datetime
import base64
import requests

st.set_page_config(page_title="Gestion Fiches GMB", layout="wide")

# --- Connexion à la base de données ---
DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# --- GitHub ---
GITHUB_TOKEN = st.secrets["GH_TOKEN"]
GITHUB_REPO = "Lucas2882-byte/fiches-gmb"
GITHUB_BRANCH = "main"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents"

def upload_db_to_github(filepath, repo_filename):
    with open(filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_resp = requests.get(f"{GITHUB_API_URL}/{repo_filename}", headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    payload = {
        "message": f"Update {repo_filename}",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(f"{GITHUB_API_URL}/{repo_filename}", headers=headers, json=payload)
    if put_resp.status_code >= 400:
        st.error(f"❌ Upload échoué : {put_resp.status_code}")
        st.json(put_resp.json())
    else:
        st.success("📤 Base mise à jour sur GitHub avec succès ✅")

# --- Formulaire pour ajouter une fiche ---
st.title("📋 Ajouter une fiche GMB")

with st.form("ajout_fiche"):
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nom de la fiche")
        ville = st.text_input("Ville")
        adresse = st.text_input("Adresse")
    with col2:
        telephone = st.text_input("Téléphone")
        image_url = st.text_input("URL de l'image")

    submitted = st.form_submit_button("Ajouter")
    if submitted and nom and ville:
        now = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO fiches (nom, ville, adresse, telephone, image_url, date_creation) VALUES (?, ?, ?, ?, ?, ?)",
            (nom, ville, adresse, telephone, image_url, now)
        )
        conn.commit()
        upload_db_to_github(DB_FILE, DB_FILE)
        st.success("✅ Fiche ajoutée avec succès")

# --- Affichage des fiches enregistrées ---
st.subheader("📁 Fiches enregistrées")
fiches = cursor.execute("SELECT * FROM fiches").fetchall()

if fiches:
    for fiche in fiches:
        st.markdown(f"**{fiche[1]}** - {fiche[2]} - {fiche[3]} - {fiche[4]}")
        if fiche[5]:
            st.image(fiche[5], width=100)
        st.markdown(f"📅 Ajoutée le : {fiche[7]}")
        st.divider()
else:
    st.info("Aucune fiche enregistrée pour le moment.")

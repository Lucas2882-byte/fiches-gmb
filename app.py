import streamlit as st
import sqlite3
from datetime import datetime
import base64
import requests

st.set_page_config(page_title="Gestion Fiches GMB", layout="wide")

# --- Connexion SQLite ---
DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# --- Paramètres GitHub ---
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
        "message": f"update {repo_filename}",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(f"{GITHUB_API_URL}/{repo_filename}", headers=headers, json=payload)
    if put_resp.status_code >= 400:
        st.error(f"❌ Erreur lors de l’upload GitHub : {put_resp.status_code}")
        st.json(put_resp.json())
    else:
        st.toast("📤 Base envoyée sur GitHub ✅")

# --- Formulaire multiple ---
st.title("📋 Ajouter plusieurs fiches GMB")
volume = st.selectbox("Nombre de fiches à ajouter", list(range(1, 11)), index=0)

with st.form("ajout_fiches_multiple"):
    fiches_data = []

    for i in range(volume):
        st.markdown(f"### 📍 Fiche #{i+1}")
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input(f"Nom de la fiche #{i+1}", key=f"nom_{i}")
            ville = st.text_input(f"Ville #{i+1}", key=f"ville_{i}")
            adresse = st.text_input(f"Adresse #{i+1}", key=f"adresse_{i}")
        with col2:
            telephone = st.text_input(f"Téléphone #{i+1}", key=f"tel_{i}")
            image_url = st.text_input(f"URL de l'image #{i+1}", key=f"img_{i}")
        fiches_data.append((nom, ville, adresse, telephone, image_url))

    submitted = st.form_submit_button("Ajouter les fiches")
    if submitted:
        now = datetime.now().strftime("%Y-%m-%d")
        ajoutées = 0
        for nom, ville, adresse, tel, img in fiches_data:
            if nom and ville:
                cursor.execute("""
                    INSERT INTO fiches (nom, ville, adresse, telephone, image_url, date_creation)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (nom, ville, adresse, tel, img, now)
                )
                ajoutées += 1
        conn.commit()
        upload_db_to_github(DB_FILE, DB_FILE)
        st.success(f"✅ {ajoutées} fiche(s) ajoutée(s) et synchronisée(s) sur GitHub")

# --- Affichage des fiches ---
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
    st.info("Aucune fiche enregistrée.")

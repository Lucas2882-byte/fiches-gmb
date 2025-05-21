import streamlit as st
import sqlite3
from datetime import datetime
import base64
import requests

st.set_page_config(page_title="Gestion Fiches GMB", layout="wide")
st.title("📋 Ajouter plusieurs fiches GMB")

DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

GITHUB_TOKEN = st.secrets["GH_TOKEN"] if "GH_TOKEN" in st.secrets else ""
GITHUB_REPO = "Lucas2882-byte/fiches-gmb"
GITHUB_BRANCH = "main"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents"

def upload_db_to_github(filepath, repo_filename):
    if not GITHUB_TOKEN:
        st.warning("Pas de GH_TOKEN détecté")
        return
    with open(filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_resp = requests.get(f"{GITHUB_API_URL}/{repo_filename}", headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
    data = {
        "message": f"update {repo_filename}",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha
    put_resp = requests.put(f"{GITHUB_API_URL}/{repo_filename}", headers=headers, json=data)
    if put_resp.status_code >= 400:
        st.error(f"❌ Upload échoué : {put_resp.status_code}")
    else:
        st.toast("📤 Base envoyée sur GitHub avec succès ✅")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fiches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ville TEXT,
    nom TEXT,
    adresse TEXT,
    telephone TEXT,
    image_url TEXT,
    date_creation TEXT,
    statut TEXT DEFAULT 'À faire',
    nom_ok BOOLEAN DEFAULT 0,
    adresse_ok BOOLEAN DEFAULT 0,
    telephone_ok BOOLEAN DEFAULT 0,
    site_ok BOOLEAN DEFAULT 0,
    image_ok BOOLEAN DEFAULT 0
)
""")
conn.commit()

st.subheader("➕ Ajouter plusieurs fiches")
nb_fiches = st.selectbox("Nombre de fiches à ajouter", options=list(range(1, 11)), index=0)

with st.form("ajout_multi_fiches"):
    fiches_data = []
    for i in range(nb_fiches):
        st.markdown(f"### 📍 Fiche #{i+1}")
        col1, col2 = st.columns(2)
        with col1:
            ville = st.text_input(f"Ville #{i+1}", key=f"ville_{i}")
            telephone = st.text_input(f"Téléphone #{i+1}", key=f"tel_{i}")
        with col2:
            uploaded_images = st.file_uploader(f"Image pour la fiche #{i+1}", type=["jpg", "jpeg", "png"], key=f"img_{i}", accept_multiple_files=True)

        fiches_data.append({
            "ville": ville,
            "telephone": telephone,
            "images": uploaded_images
        })

    submit = st.form_submit_button("Ajouter les fiches")

    if submit:
        for data in fiches_data:
            now = datetime.now().strftime("%Y-%m-%d")
            nom = "à toi de choisir pour optimisation"
            adresse = "à toi de choisir pour optimisation"
            image_urls = ", ".join([img.name for img in data["images"]]) if data["images"] else ""
            cursor.execute(
                "INSERT INTO fiches (ville, nom, adresse, telephone, image_url, date_creation) VALUES (?, ?, ?, ?, ?, ?)",
                (data["ville"], nom, adresse, data["telephone"], image_urls, now)
            )
        conn.commit()
        upload_db_to_github(DB_FILE, "fiches_gmb.db")
        st.success("✅ Fiches ajoutées avec succès")

st.subheader("📁 Fiches enregistrées")
df = conn.execute("SELECT * FROM fiches").fetchall()

if df:
    for fiche in df:
        st.markdown(f"**{fiche[2]}** - {fiche[1]} - {fiche[3]} - {fiche[4]}")
        st.markdown(f"📅 Ajoutée le : {fiche[6]}")
        st.markdown("📌 Statut : " + fiche[7])
        st.divider()
else:
    st.info("Aucune fiche enregistrée pour le moment.")

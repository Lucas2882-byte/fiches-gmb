import streamlit as st 
import sqlite3
import base64
import requests
import os
from datetime import datetime
import zipfile
from io import BytesIO

st.set_page_config(page_title="Fiches GMB", layout="wide")

# --- Connexion à la base ---
DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# S'assurer que la table contient bien la colonne image_url si elle n'existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS fiches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    ville TEXT,
    adresse TEXT,
    telephone TEXT,
    image_url TEXT,
    statut TEXT DEFAULT 'à faire',
    date_creation TEXT
)
""")
conn.commit()

# --- GitHub Upload Function ---
GITHUB_TOKEN = st.secrets["GH_TOKEN"]
GITHUB_REPO = "Lucas2882-byte/fiches-gmb"
GITHUB_BRANCH = "main"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/images"

def upload_image_to_github(file, filename):
    content = base64.b64encode(file.read()).decode()
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_resp = requests.get(f"{GITHUB_API_URL}/{filename}", headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
    payload = {
        "message": f"upload {filename}",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha
    put_resp = requests.put(f"{GITHUB_API_URL}/{filename}", headers=headers, json=payload)
    if put_resp.status_code in [200, 201]:
        return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{filename}"
    else:
        st.error("Erreur d'upload GitHub")
        st.json(put_resp.json())
        return None

# --- Upload DB to GitHub ---
def upload_db_to_github():
    with open(DB_FILE, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    db_path = "fiches_gmb.db"
    get_resp = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{db_path}", headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
    payload = {
        "message": f"update {db_path}",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{db_path}", headers=headers, json=payload)

# --- Interface ---
st.title("📍 Ajouter plusieurs fiches GMB")
nb_fiches = st.number_input("Nombre de fiches à ajouter", min_value=1, max_value=10, value=1)

fiches = []
with st.form("form_ajout"):
    for i in range(nb_fiches):
        st.markdown(f"### 📍 Fiche #{i+1}")
        col1, col2 = st.columns(2)
        with col1:
            ville = st.text_input(f"Ville #{i+1}", key=f"ville_{i}")
            telephone = st.text_input(f"Téléphone #{i+1}", key=f"tel_{i}")
        with col2:
            images = st.file_uploader(f"Images pour la fiche #{i+1}", type=["png", "jpg", "jpeg"], key=f"img_{i}", accept_multiple_files=True)
        fiches.append({
            "ville": ville,
            "telephone": telephone,
            "images": images
        })

    submitted = st.form_submit_button("Ajouter les fiches")

if submitted:
    now = datetime.now().strftime("%Y-%m-%d")
    for fiche in fiches:
        if not fiche["ville"] or not fiche["telephone"]:
            st.warning("⚠️ Merci de remplir tous les champs obligatoires (ville et téléphone).")
            continue

        nom = "à toi de choisir pour optimisation"
        adresse = "à toi de choisir pour optimisation"
        image_urls = []

        if fiche["images"]:
            for img_file in fiche["images"][:60]:  # Limit to 60 images max
                safe_filename = f"{fiche['ville']}_{now.replace('-', '')}_{img_file.name}"
                url = upload_image_to_github(img_file, safe_filename)
                if url:
                    image_urls.append(url)

        cursor.execute(
            "INSERT INTO fiches (nom, ville, adresse, telephone, image_url, statut, date_creation) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nom, fiche["ville"], adresse, fiche["telephone"], ";".join(image_urls), "à faire", now)
        )
    conn.commit()
    upload_db_to_github()
    rows_after = cursor.execute("SELECT COUNT(*) FROM fiches").fetchone()[0]
    st.success("✅ Fiches ajoutées avec succès")
    st.info(f"📊 Total de fiches enregistrées : {rows_after}")

# --- Affichage ---
st.subheader("📁 Fiches enregistrées")
rows = cursor.execute("SELECT * FROM fiches ORDER BY id DESC").fetchall()
for row in rows:
    st.markdown(f"**{row[1]}** - {row[2]} - {row[3]} - {row[4]}")
    
    if row[5]:
        urls = row[5].split(";")
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for url in urls:
                try:
                    filename = url.split("/")[-1].split("?")[0]
                    st.write("📸 URL à télécharger :", url)
                    response = requests.get(url)
                    if response.status_code == 200:
                        response = requests.get(url)
                        st.write("✅ Status", response.status_code, "Taille:", len(response.content))
                        st.write(url, response.status_code, len(response.content))
                        zip_file.writestr(filename, response.content)
                except Exception as e:
                    st.warning(f"⚠️ Erreur sur {url} : {e}")
    
        zip_buffer.seek(0)
        st.download_button(
            label="📦 Télécharger toutes les images de cette fiche",
            data=zip_buffer,
            file_name=f"fiche_{row[0]}_images.zip",
            mime="application/zip"
        )

import streamlit as st 
import sqlite3
import base64
import requests
import os
from datetime import datetime
import zipfile
from io import BytesIO
import re
import unicodedata  # ← requis pour slugify
import time

st.set_page_config(page_title="Fiches GMB", layout="wide")

# --- Fonction pour nettoyer les noms de fichiers (sans accents, espaces, etc.) ---
def slugify(value):
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '_', value)

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

import time  # à mettre tout en haut du fichier si ce n’est pas encore importé

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
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{filename}"

        # 🔁 Attendre que le lien raw fonctionne (jusqu'à 10s)
        for _ in range(10):
            check = requests.get(raw_url)
            if check.status_code == 200 and len(check.content) > 0:
                break
            time.sleep(1)

        st.success(f"✅ Upload réussi sur GitHub : {filename}")
        return raw_url
    else:
        st.error(f"❌ Upload échoué pour : {filename}")
        st.code(put_resp.text)
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
                safe_filename = slugify(f"{fiche['ville']}_{now.replace('-', '')}_{img_file.name}")  # ✅ safe name
                url = upload_image_to_github(img_file, safe_filename)
                if url:
                    image_urls.append(url)
                    st.write("🔗 URL sauvegardée :", url)

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
# --- Affichage ---
st.subheader("📁 Fiches enregistrées")
rows = cursor.execute("SELECT * FROM fiches ORDER BY id DESC").fetchall()
for row in rows:
    st.markdown(f"**{row[1]}** - {row[2]} - {row[3]} - {row[4]}")
    
    if row[5]:
        urls = row[5].split(";")
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, url in enumerate(urls):
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0"
                    }
                    response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                    ext = url.split(".")[-1].split("?")[0]
                    filename = f"image_{i+1}.{ext}"

                    if response.status_code == 200 and len(response.content) > 0:
                        zip_file.writestr(filename, response.content)
                        st.success(f"✅ {filename} ajouté ({len(response.content)} octets)")
                    else:
                        st.warning(f"❌ Erreur {response.status_code} ou fichier vide : {url}")

                except Exception as e:
                    st.error(f"💥 Erreur lors du téléchargement de {url} : {e}")

        zip_buffer.seek(0)
        st.download_button(
            label="📦 Télécharger toutes les images de cette fiche",
            data=zip_buffer,
            file_name=f"fiche_{row[0]}_images.zip",
            mime="application/zip"
        )


import streamlit as st
import sqlite3
import os
from datetime import datetime

st.set_page_config(page_title="Gestion Fiches", layout="wide")

# --- Setup upload directory ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Connexion à la base de données ---
DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()


st.title("📋 Ajouter plusieurs fiches GMB")

nb_fiches = st.selectbox("Nombre de fiches à ajouter", list(range(1, 11)), index=0)

fiches = []

with st.form("ajout_fiches"):
    for i in range(nb_fiches):
        st.markdown(f"### 📍 Fiche #{i+1}")
        col1, col2 = st.columns(2)

        with col1:
            ville = st.text_input(f"Ville #{i+1}", key=f"ville_{i}")
        with col2:
            telephone = st.text_input(f"Téléphone #{i+1}", key=f"tel_{i}")

        image_file = st.file_uploader(f"Image pour la fiche #{i+1}", type=["jpg", "jpeg", "png"], key=f"img_{i}")

        image_path = ""
        if image_file:
            image_path = os.path.join(UPLOAD_DIR, f"fiche_{i+1}_{image_file.name}")
            with open(image_path, "wb") as f:
                f.write(image_file.read())

        fiches.append({
            "nom": "à toi de choisir pour optimisation",
            "ville": ville,
            "adresse": "à toi de choisir pour optimisation",
            "telephone": telephone,
            "image_url": image_path,
            "date_creation": datetime.now().strftime("%Y-%m-%d")
        })

    submitted = st.form_submit_button("Ajouter les fiches")

    if submitted:
        for fiche in fiches:
            if fiche["ville"]:
                cursor.execute("""
                    INSERT INTO fiches (nom, ville, adresse, telephone, image_url, date_creation)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    fiche["nom"], fiche["ville"], fiche["adresse"], fiche["telephone"], fiche["image_url"], fiche["date_creation"]
                ))
        conn.commit()
        st.success(f"📋 {len(fiches)} fiche(s) ajoutée(s) avec succès")

# --- Affichage des fiches enregistrées ---
st.subheader("📁 Fiches enregistrées")
all_fiches = cursor.execute("SELECT * FROM fiches").fetchall()
if all_fiches:
    for fiche in all_fiches:
        st.markdown(f"**{fiche[2]}** - {fiche[1]} - {fiche[3]} - {fiche[4]}")
        if fiche[5] and os.path.exists(fiche[5]):
            st.image(fiche[5], width=100)
        st.markdown(f"📅 Ajoutée le : {fiche[7]}")
        st.divider()
else:
    st.info("Aucune fiche enregistrée pour le moment.")

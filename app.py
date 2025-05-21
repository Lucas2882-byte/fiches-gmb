import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Gestion Fiches", layout="wide")

DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

st.title("📋 Ajouter plusieurs fiches GMB")

nb_fiches = st.selectbox("Nombre de fiches à ajouter", list(range(1, 11)), index=0)

fiches = []  # <- nécessaire avant la boucle

with st.form("ajout_fiches"):
    for i in range(nb_fiches):
        st.markdown(f"### 📍 Fiche #{i+1}")
        col1, col2 = st.columns(2)
        with col1:
            ville = st.text_input(f"Ville #{i+1}", key=f"ville_{i}")
        with col2:
            telephone = st.text_input(f"Téléphone #{i+1}", key=f"tel_{i}")
            image_url = st.text_input(f"URL de l'image #{i+1}", key=f"img_{i}")

        # Valeurs automatiques pour nom & adresse
        fiches.append({
            "nom": "à toi de choisir pour optimisation",
            "ville": ville,
            "adresse": "à toi de choisir pour optimisation",
            "telephone": telephone,
            "image_url": image_url
        })

    submitted = st.form_submit_button("Ajouter les fiches")

    if submitted:
        for fiche in fiches:
            now = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO fiches (nom, ville, adresse, telephone, image_url, date_creation) VALUES (?, ?, ?, ?, ?, ?)",
                (fiche["nom"], fiche["ville"], fiche["adresse"], fiche["telephone"], fiche["image_url"], now)
            )
        conn.commit()
        st.success("✅ Toutes les fiches ont été ajoutées avec succès.")

# --- Affichage des fiches enregistrées ---
st.subheader("📁 Fiches enregistrées")
rows = cursor.execute("SELECT * FROM fiches").fetchall()

if rows:
    for fiche in rows:
        st.markdown(f"**{fiche[1]}** - {fiche[2]} - {fiche[3]} - {fiche[4]}")
        if fiche[5]:
            st.image(fiche[5], width=100)
        st.markdown(f"📅 Ajoutée le : {fiche[7]}")
        st.divider()
else:
    st.info("Aucune fiche enregistrée pour le moment.")

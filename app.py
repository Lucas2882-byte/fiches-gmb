import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Gestion Fiches", layout="wide")

# --- Connexion à la base existante ---
DB_FILE = "fiches_gmb.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

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

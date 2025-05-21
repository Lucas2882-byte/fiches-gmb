
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# --- DATABASE ---
conn = sqlite3.connect("fiches_gmb.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS fiches (
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
)''')
conn.commit()

# --- PAGE CONFIG ---
st.set_page_config(page_title="GMB Tracker", layout="wide")
st.title("📍 Suivi des Fiches GMB")

# --- FORMULAIRE D'AJOUT ---
st.subheader("➕ Ajouter une fiche")
with st.form("ajouter_fiche"):
    col1, col2 = st.columns(2)
    with col1:
        ville = st.text_input("Ville")
        nom = st.text_input("Nom de la fiche")
        adresse = st.text_input("Adresse")
    with col2:
        telephone = st.text_input("Téléphone")
        image_url = st.text_input("URL de l'image")
    submit = st.form_submit_button("Ajouter")

    if submit and ville and nom:
        c.execute(
            "INSERT INTO fiches (ville, nom, adresse, telephone, image_url, date_creation) VALUES (?, ?, ?, ?, ?, ?)",
            (ville, nom, adresse, telephone, image_url, datetime.now().strftime("%Y-%m-%d"))
        )
        conn.commit()
        st.success("Fiche ajoutée ✅")

# --- TABLEAU DE BORD ---
st.subheader("📋 Fiches en cours")

# --- STATUT ---
statuts = ["À faire", "En cours", "Terminé"]
choix_statut = st.selectbox("Voir les fiches par statut", statuts)

# --- AUTO-MISE À JOUR DU STATUT SI +30 JOURS ---
today = datetime.now()
fiches = c.execute("SELECT * FROM fiches WHERE statut != 'Terminé'").fetchall()
for fiche in fiches:
    id_, _, _, _, _, _, date_creation, statut, *_ = fiche
    date_fiche = datetime.strptime(date_creation, "%Y-%m-%d")
    if today - date_fiche > timedelta(days=30):
        c.execute("UPDATE fiches SET statut = 'Terminé' WHERE id = ?", (id_,))
conn.commit()

# --- AFFICHAGE DES FICHES ---
df = pd.read_sql_query("SELECT * FROM fiches WHERE statut = ?", conn, params=(choix_statut,))
if df.empty:
    st.info("Aucune fiche dans cette catégorie.")
else:
    for index, row in df.iterrows():
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f'''
                    <div style='padding: 10px; background-color: #f0f2f6; border-left: 5px solid #4CAF50; border-radius: 6px;'>
                        <strong>{row["nom"]}</strong> ({row["ville"]})<br>
                        🏠 {row["adresse"]}<br>
                        📞 {row["telephone"]}<br>
                        🌐 <a href="{row["image_url"]}" target="_blank">Image</a><br>
                        🗓️ Créée le : {row["date_creation"]}
                    </div>
                ''', unsafe_allow_html=True)

            with col2:
                st.write("Champs faits :")
                nom_ok = st.checkbox("Nom", value=row["nom_ok"], key=f"nom_{row['id']}")
                adresse_ok = st.checkbox("Adresse", value=row["adresse_ok"], key=f"adr_{row['id']}")
                telephone_ok = st.checkbox("Téléphone", value=row["telephone_ok"], key=f"tel_{row['id']}")
                site_ok = st.checkbox("Site", value=row["site_ok"], key=f"site_{row['id']}")
                image_ok = st.checkbox("Image", value=row["image_ok"], key=f"img_{row['id']}")
                if st.button("💾 Sauvegarder", key=f"save_{row['id']}"):
                    c.execute(
                        '''UPDATE fiches SET nom_ok=?, adresse_ok=?, telephone_ok=?, site_ok=?, image_ok=?, statut='En cours' WHERE id=?''',
                        (nom_ok, adresse_ok, telephone_ok, site_ok, image_ok, row["id"])
                    )
                    conn.commit()
                    st.success("Mise à jour effectuée ✅")

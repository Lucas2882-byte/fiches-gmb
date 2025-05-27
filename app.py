import streamlit as st 
import sqlite3
import base64
import requests
import os
from datetime import datetime, timedelta
import zipfile
from io import BytesIO
import re
import unicodedata
import time
import smtplib
from email.mime.text import MIMEText
import hashlib

st.set_page_config(page_title="Fiches GMB", layout="wide")

PALETTE_COULEURS = [
    "#2c3e50",  # Bleu nuit
    "#34495e",  # Gris foncé bleuté
    "#7f8c8d",  # Gris modéré
    "#16a085",  # Vert sarcelle foncé
    "#27ae60",  # Vert profond
    "#2980b9",  # Bleu moyen
    "#8e44ad",  # Violet foncé
    "#2ecc71",  # Vert clair sobre
    "#3498db",  # Bleu classique
    "#9b59b6",  # Lavande foncé
    "#c0392b",  # Rouge foncé
    "#d35400",  # Orange brun
    "#e67e22",  # Orange moyen
    "#1abc9c",  # Turquoise foncé
    "#95a5a6",  # Gris clair
    "#bdc3c7",  # Gris doux
    "#f39c12",  # Jaune doré
    "#e74c3c",  # Rouge doux
    "#ecf0f1",  # Blanc cassé
    "#f1c40f",  # Jaune foncé
    "#7d3c98",  # Violet profond
    "#5dade2",  # Bleu léger
    "#48c9b0",  # Menthe foncée
    "#52be80",  # Vert doux
    "#a569bd",  # Lavande moyen
    "#f5b041",  # Orange clair
    "#d98880",  # Rose brun
    "#f7dc6f",  # Jaune pâle
    "#85929e",  # Bleu-gris
    "#abb2b9"   # Gris pastel
]

def envoyer_notification_discord(message):
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ Message envoyé à Discord.")
        else:
            print(f"❌ Erreur Discord : {response.status_code}")
    except Exception as e:
        print(f"💥 Exception lors de l'envoi à Discord : {e}")



def couleur_depuis_nom(nom_client):
    if nom_client == "—":
        return "#999"  # Gris par défaut pour "inconnu"
    index = abs(hash(nom_client)) % len(PALETTE_COULEURS)
    return PALETTE_COULEURS[index]


def envoyer_email_smtp(host, port, login, mot_de_passe, destinataire, sujet, message):
    msg = MIMEText(message)
    msg["Subject"] = sujet
    msg["From"] = login
    msg["To"] = destinataire

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(login, mot_de_passe)
        server.send_message(msg)

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
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{filename}"
        st.success(f"✅ Upload réussi sur GitHub : {filename}")
        return raw_url
    else:
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
st.title("📍 Gestion fiches GMB")
numero_client = st.text_input("🔢 N° Commande nouvelles fiches")  # ← AJOUT ICI
nb_fiches = st.number_input("Nombre de fiches à ajouter", min_value=1, max_value=10, value=1)

fiches = []
with st.form("form_ajout"):
    for i in range(nb_fiches):
        st.markdown(f"### 📍 Fiche #{i+1}")
        col1, col2 = st.columns(2)
        with col1:
            ville = st.text_input(f"Ville #{i+1}", key=f"ville_{i}")
            adresse = st.text_input(f"Adresse #{i+1}", value="à toi de choisir pour optimisation", key=f"adresse_{i}")
            telephone = st.text_input(f"Téléphone #{i+1}", value="En attente", key=f"tel_{i}")
            site_web = st.text_input(f"Lien du site internet pour la fiche #{i+1}", value="En attente", key=f"site_{i}")
        with col2:
            images = st.file_uploader(f"Images pour la fiche #{i+1}", type=["png", "jpg", "jpeg"], key=f"img_{i}", accept_multiple_files=True)
            
        fiches.append({
            "ville": ville,
            "telephone": telephone,
            "images": images,
            "adresse": adresse,
            "site_web": site_web
        })

    submitted = st.form_submit_button("Ajouter les fiches")

if submitted:
    now = datetime.now().strftime("%Y-%m-%d")
    for fiche in fiches:
        if not fiche["ville"] or not fiche["telephone"]:
            st.warning("⚠️ Merci de remplir tous les champs obligatoires (ville et téléphone).")
            continue

        nom = "à toi de choisir pour optimisation"
        adresse = fiche["adresse"]
        image_urls = []

        if fiche["images"]:
            for img_file in fiche["images"][:60]:
                name, ext = os.path.splitext(img_file.name)
                ext = ext.lower()
                base_name = slugify(f"{fiche['ville']}_{now.replace('-', '')}_{name}")
                safe_filename = f"{base_name}{ext}"
                url = upload_image_to_github(img_file, safe_filename)
                if url:
                    image_urls.append(url)
        taille = len(";".join(image_urls))
        st.write("Taille image_url :", taille)
        
        if taille > 10000:
            st.warning("⚠️ Attention : La liste d'URLs est très longue, cela peut poser problème à l'enregistrement.")
        st.write("DEBUG:", {
            "nom": nom,
            "ville": fiche.get("ville"),
            "adresse": adresse,
            "tel": fiche.get("telephone"),
            "site": fiche.get("site_web"),
            "numero_client": numero_client,
            "image_urls": image_urls,
            "taille image_url": len(";".join(image_urls))
        })

        cursor.execute(
            "INSERT INTO fiches (nom, ville, adresse, telephone, image_url, statut, date_creation, demande_site_texte, numero_client) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nom, fiche["ville"], adresse, fiche["telephone"], ";".join(image_urls), "à faire", now, fiche["site_web"], numero_client)
        )

    conn.commit()
    upload_db_to_github()
    rows_after = cursor.execute("SELECT COUNT(*) FROM fiches").fetchone()[0]
    st.success("✅ Fiches ajoutées avec succès")
    st.info(f"📊 Total de fiches enregistrées : {rows_after}")
    try:
        envoyer_email_smtp(
            host="smtp.hostinger.com",
            port=465,
            login="contact@lucas-freelance.fr",
            mot_de_passe=st.secrets["SMTP_PASSWORD"],
            destinataire="lucaswebsite28@gmail.com",
            sujet="📌 Nouvelles fiches GMB ajoutées",
            message=f"{len(fiches)} fiche(s) ont été ajoutées par le formulaire Streamlit."
        )

        st.success("📧 Email de notification envoyé.")
    except Exception as e:
        st.warning(f"⚠️ Échec de l'envoi de l'email : {e}")


# --- Affichage ---
st.subheader("📁 Fiches enregistrées")
rows = cursor.execute("SELECT * FROM fiches ORDER BY id DESC").fetchall()
stats = {"à faire": [], "en cours": [], "terminé": []}
for row in rows:
    if row[7] in stats:
        stats[row[7]].append(row)
    else:
        stats["à faire"].append(row)  # 🔁 fallback pour les valeurs inattendues

couleurs = {
    "à faire": "red",
    "en cours": "orange",
    "terminé": "green"
}

for statut in ["à faire", "en cours", "terminé"]:
    statut_maj = statut.upper()

    with st.expander(f"📌 {statut_maj} ({len(stats[statut])})"):

        for row in stats[statut]:
            col_left, col_right = st.columns([3, 1])
            # Dictionnaire de mois en français
            mois_fr = {
                "01": "janvier", "02": "février", "03": "mars", "04": "avril",
                "05": "mai", "06": "juin", "07": "juillet", "08": "août",
                "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre"
            }
            
            # Convertir date ajout + calcul date de fin
            date_creation = datetime.strptime(row[6], "%Y-%m-%d")
            date_fin = date_creation + timedelta(days=30)
            
            # Formater en "21 mai 2025"
            def date_en_fr(dt):
                return f"{dt.day} {mois_fr[dt.strftime('%m')]} {dt.year}"
            
            date_creation_str = date_en_fr(date_creation)
            date_fin_str = date_en_fr(date_fin)
            
            with col_left:
                nom_client = row[18] if row[18] else "—"
                couleur_client = couleur_depuis_nom(nom_client) if nom_client != "—" else "#555"
            
                # Badge au-dessus
                st.markdown(f"""
                <div style='background-color: {couleur_client}; color: white; 
                            padding: 6px 12px; border-radius: 10px; 
                            font-weight: bold; display: inline-block; margin-bottom: 10px;'>
                    🔢 {nom_client}
                </div>
                """, unsafe_allow_html=True)
            
                # Carte fiche
                st.markdown(f"""
                <div style='padding: 15px; border: 1px solid #444; border-radius: 12px; margin-bottom: 15px; background-color: #111;'>
                    <p>📄 <strong>Nom :</strong> {row[2]}</p>
                    <p>🏙️ <strong>Ville :</strong> {row[1]}</p>
                    <p>📍 <strong>Adresse :</strong> {row[3]}</p>
                    <p>📞 <strong>Téléphone :</strong> {row[4]}</p>
                    <p>🌐 <strong>Site :</strong> {row[17] if row[17] else "—"}</p>
                    <p>📅 <strong>Date d'ajout :</strong> {date_creation_str}</p>
                    <p style='color: #ff4444;'>🛑 <strong>Date de fin :</strong> {date_fin_str}</p>
                </div>
                """, unsafe_allow_html=True)


            

                
                

            
            with col_right:
                fiche_id = row[0]
                st.markdown(
                    """
                    <style>
                    .block-container select {
                        margin-top: 20px;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                action = st.selectbox(
                    "🔧 Action sur la fiche",
                    ["Mettre à jour la progression", "Modifier les informations de la fiche"],
                    key=f"action_{fiche_id}"
                )
                
                if action == "Mettre à jour la progression":
                    # ✅ Section checkboxes en 2 colonnes
                    col_cb1, col_cb2 = st.columns(2)
                    with col_cb1:
                        fiche_creee = st.checkbox("🆕 Création de la fiche", value=int(row[13]) == 1, key=f"fiche_creee_{fiche_id}")
                        photos_ajoutees = st.checkbox("🖼️ Ajout des photos", value=int(row[15]) == 1, key=f"photos_ajoutees_{fiche_id}")
                    with col_cb2:
                        tel_ajoute = st.checkbox("📞 Ajout du numéro", value=int(row[14]) == 1, key=f"tel_ajoute_{fiche_id}")
                        site_web_ajoute = st.checkbox("🌐 Ajout du site internet", value=int(row[16]) == 1, key=f"site_web_ajoute_{fiche_id}")
                    
                    # ✅ Affichage de l'avancement
                    # Calcul de l’avancement
                    # Calcul initial de progression
                    total_checked = sum([fiche_creee, tel_ajoute, photos_ajoutees, site_web_ajoute])
                    progress_percent = total_checked * 20
                    
                    # Initialiser le lien final
                    lien_final_key = f"lien_fiche_{fiche_id}"
                    
                    # Si à 80%, proposer le champ + checkbox
                    if progress_percent == 80:
                        st.session_state[lien_final_key] = st.text_input(
                            "🔗 Lien final de la fiche", 
                            key=f"lien_termine_{fiche_id}", 
                            value=st.session_state.get(lien_final_key, "")
                        )
                        if st.checkbox("✅ Confirmer la mise en ligne de la fiche", key=f"confirm_termine_{fiche_id}"):
                            total_checked += 1
                            progress_percent = 100
                    
                    # Récupération du lien final (si rempli)
                    lien_final = st.session_state.get(lien_final_key, "")
                    
                    # Affichage final unique de la progression
                    st.markdown(f"<b>📊 Avancement de la fiche : {progress_percent}%</b>", unsafe_allow_html=True)
                    st.progress(progress_percent)

                    # ✅ Ligne de boutons "Sauvegarder" et "Supprimer"
                    col_btn1, col_btn2 = st.columns([0.8, 1.4])
                    with col_btn1:
                        if st.button("💾 Sauvegarder", key=f"save_btn_{fiche_id}"):
                            # Déterminer le statut à enregistrer selon le pourcentage
                            if progress_percent == 100:
                                nouveau_statut = "terminé"
                            elif progress_percent >= 20:
                                nouveau_statut = "en cours"
                            else:
                                nouveau_statut = "à faire"
                    
                            # Mise à jour dans la BDD
                            cursor.execute("""
                                UPDATE fiches
                                SET creation_fiche = ?, ajout_numero = ?, ajout_photos = ?, ajout_site = ?, statut = ?, lien_fiche_terminee = ?
                                WHERE id = ?
                            """, (
                                int(fiche_creee),
                                int(tel_ajoute),
                                int(photos_ajoutees),
                                int(site_web_ajoute),
                                nouveau_statut,
                                lien_final,  # 👈 très important
                                fiche_id
                            ))
                            conn.commit()
                            upload_db_to_github()
                            if nouveau_statut == "terminé":
                                try:
                                    nom_client = row[18] if row[18] else f"id_{fiche_id}"
                                    ville = row[1]
                                    adresse = row[3]
                                    lien_fiche = st.session_state.get(f"lien_fiche_{fiche_id}", "—")
                            
                                    envoyer_notification_discord(
                                        f"✅ **Fiche Client terminée : {nom_client}**\n\n"
                                        f"🏙️ **Ville :** {ville}\n\n"
                                        f"📍 **Adresse :** {adresse}\n\n"
                                        f"🔗 **Lien final :** {lien_fiche}\n\n"
                                        f"<@314729858863464448> <@1222133249824915509>"
                                    )
                                except Exception as e:
                                    st.error(f"💥 Erreur lors de l'envoi de la notification Discord : {e}")

                            st.success(f"✅ État mis à jour avec succès – statut : {nouveau_statut}")
                            st.rerun()

                            
                    
                    with col_btn2:
                        if row[5]:
                            urls = row[5].split(";")
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                                for i, url in enumerate(urls):
                                    try:
                                        headers = {"User-Agent": "Mozilla/5.0"}
                                        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                                        ext = url.split(".")[-1].split("?")[0]
                                        filename = f"image_{i+1}.{ext}"
                                        if response.status_code == 200 and len(response.content) > 0:
                                            zip_file.writestr(filename, response.content)
                                        else:
                                            st.warning(f"❌ Erreur {response.status_code} ou fichier vide : {url}")
                                    except Exception as e:
                                        st.error(f"💥 Erreur lors du téléchargement de {url} : {e}")
                    
                            zip_buffer.seek(0)
                            nom_client = row[18] if row[18] else f"id_{row[0]}"
                            nom_fichier_zip = f"Fiche_{slugify(nom_client)}_images.zip"
                    
                            st.download_button(
                                label="📦 Télécharger les images",
                                data=zip_buffer,
                                file_name=nom_fichier_zip,
                                mime="application/zip",
                                key=f"download_btn_{fiche_id}"
                            )
                    
                    # ➕ Ligne complète : case à cocher + bouton suppression conditionnel
                    confirm_delete = st.checkbox("☑️ Je confirme la suppression", key=f"confirm_delete_{fiche_id}")
                    if confirm_delete:
                        if st.button("🗑️ Supprimer cette fiche", key=f"delete_btn_{fiche_id}"):
                            cursor.execute("DELETE FROM fiches WHERE id = ?", (fiche_id,))
                            conn.commit()
                            upload_db_to_github()
                            st.warning("❌ Fiche supprimée")
                            st.rerun()

            
                  
                        
                    
                        
                elif action == "Modifier les informations de la fiche":
                    col1, col2 = st.columns(2)
                
                    with col1:
                        nouveau_nom = st.text_input("📄 Nom", value=row[2], key=f"edit_nom_{fiche_id}")
                        nouveau_tel = st.text_input("📞 Téléphone", value=row[4], key=f"edit_tel_{fiche_id}")
                
                    with col2:
                        nouvelle_adresse = st.text_input("🏙️ Adresse", value=row[3], key=f"edit_adresse_{fiche_id}")
                        nouveau_site = st.text_input("🌐 Site web", value=row[18] if row[18] else "", key=f"edit_site_{fiche_id}")
                
                    if st.button("✅ Enregistrer les modifications", key=f"btn_save_infos_{fiche_id}"):
                        # ⬅️ Récupérer les anciennes valeurs
                        ancien_nom = row[2]
                        ancienne_adresse = row[3]
                
                        # 🔄 Mise à jour
                        cursor.execute("""
                            UPDATE fiches
                            SET nom = ?, ville = ?, adresse = ?, telephone = ?, demande_site_texte = ?
                            WHERE id = ?
                        """, (nouveau_nom, row[1], nouvelle_adresse, nouveau_tel, nouveau_site, fiche_id))
                        conn.commit()
                        upload_db_to_github()
                        st.success("📝 Informations mises à jour avec succès")
                
                        if (
                            nouveau_nom != ancien_nom or
                            nouvelle_adresse != ancienne_adresse or
                            nouveau_tel != row[4] or
                            nouveau_site != (row[8] if row[8] else "")
                        ):
                            envoyer_notification_discord(
                                f"✏️ **Fiche Client : {row[18] if row[18] else f'id_{fiche_id}'} modifiée**\n\n"
                                f"📄 **Nom :** {ancien_nom} → {nouveau_nom}\n\n"
                                f"📍 **Adresse :** {ancienne_adresse} → {nouvelle_adresse}\n\n"
                                f"📞 **Téléphone :** {row[4]} → {nouveau_tel}\n\n"
                                f"🌐 **Site web :** {(row[17] if row[17] else '—')} → {nouveau_site}\n\n"
                                f"<@314729858863464448> <@1222133249824915509>"
                            )
                            # ✉️ Envoi email si téléphone ou site web modifié
                            if nouveau_tel != row[4] or nouveau_site != (row[8] if row[8] else ""):
                                try:
                                    envoyer_email_smtp(
                                        host="smtp.hostinger.com",
                                        port=465,
                                        login="contact@lucas-freelance.fr",
                                        mot_de_passe=st.secrets["SMTP_PASSWORD"],
                                        destinataire="lucaswebsite28@gmail.com",
                                        sujet=f"🔔 Modification fiche client : {row[18] if row[18] else f'id_{fiche_id}'}",
                                        message=(
                                            f"📄 Nom : {ancien_nom} → {nouveau_nom}\n"
                                            f"📍 Adresse : {ancienne_adresse} → {nouvelle_adresse}\n"
                                            f"📞 Téléphone : {row[4]} → {nouveau_tel}\n"
                                            f"🌐 Site web : {(row[17] if row[17] else '—')} → {nouveau_site}"
                                        )
                                    )
                                except Exception as e:
                                    st.warning(f"⚠️ Erreur lors de l'envoi de l'email : {e}")
                
                        st.rerun()



                    

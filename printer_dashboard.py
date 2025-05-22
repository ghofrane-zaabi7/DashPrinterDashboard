import streamlit as st
import pandas as pd
from PIL import Image
import base64
import serial
import serial.tools.list_ports
from printer_connection import get_printer_status
from utils import (
    load_logs, display_temperature_plotly,
    load_settings, log_impression, reset_logs, generate_report_pdf
)

# ✅ Fonction pour lister les ports disponibles
def get_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# ✅ Fonction pour envoyer des commandes G-code à l'imprimante
def envoyer_commande_gcode(cmd, port, baudrate=115200):
    try:
        with serial.Serial(port, baudrate, timeout=2) as ser:
            ser.write((cmd + "\n").encode())
            return f"✅ Commande envoyée au port {port}: {cmd}"
    except Exception as e:
        return f"❌ Erreur de communication avec {port}: {e}"

# Personnalisation du style de la page Streamlit
st.set_page_config(page_title="Dashboard Imprimante 3D à granulés", layout="wide")

# Logo
logo = Image.open("assets/logo.png")
st.image(logo, width=120)

# Actualiser les données
if st.button("🔁 Actualiser les données"):
    st.rerun()

# Sélection du port d'imprimante
ports = get_ports()
selected_port = st.sidebar.selectbox("🔌 Choisir le port d'imprimante", ports)

# Affichage du port sélectionné
st.sidebar.write(f"🔌 Port sélectionné : {selected_port}")

# Définition de la variable `page` pour la navigation dans les différentes sections
page = st.sidebar.radio("Menu", ["🖥️ État machine", "📊 Historique", "⚙️ Maintenance", "📂 G-code"])

# Récupérer le statut de l'imprimante
status = get_printer_status()

def play_audio(file_path):
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        b64 = base64.b64encode(audio_bytes).decode()
        md = f"""
        <audio autoplay>
        <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)

def analyser_statut(status):
    diagnostics = []

    if status["etat"] == "Erreur de connexion":
        diagnostics.append({
            "gravité": "critique",
            "problème": "Connexion perdue avec la machine",
            "solution": "Vérifiez le port USB ou la liaison série."
        })

    if status["etat"] == "En impression" and status["temp_buse"] < 170:
        diagnostics.append({
            "gravité": "critique",
            "problème": "Buse trop froide pendant l'impression",
            "solution": "Vérifiez la cartouche chauffante ou la thermistance."
        })

    if status["temp_bed"] < 40 and "abs" in status["materiau"].lower():
        diagnostics.append({
            "gravité": "moyenne",
            "problème": "Température du plateau trop basse pour l'ABS",
            "solution": "Augmentez le lit chauffant à 60–80°C."
        })

    if status["fichier"] == "N/A" and status["etat"] == "En attente":
        diagnostics.append({
            "gravité": "info",
            "problème": "Aucun fichier chargé",
            "solution": "Veuillez charger un fichier G-code."
        })

    return diagnostics

if page == "🖥️ État machine":
    st.markdown("## 🖥️ État en temps réel")

    if status["etat"] == "En impression":
        st.success("✅ Impression en cours.")
    elif status["etat"] == "Pause":
        st.warning("⏸️ L’imprimante est en pause.")
    else:
        st.error("❌ Problème détecté avec l’état de l’imprimante.")

    if "alerte" in status and "instable" in status["alerte"].lower():
        st.error(f"🧯 Alerte critique : {status['alerte']}")
        play_audio("assets/alert.wav")

    col1, col2, col3 = st.columns(3)
    col1.metric("🔥 Buse", f"{status['temp_buse']}°C", f"Cible : {status['cible_buse']}°C")
    col2.metric("🌡️ Plateau", f"{status['temp_bed']}°C", f"Cible : {status['cible_bed']}°C")
    col3.metric("🎛️ Vitesse", f"{status['vitesse']} mm/s")

    col4, col5, col6 = st.columns(3)
    col4.metric("⏱️ Temps restant", status['temps_restant'])
    col5.metric("📦 Matériau", status['materiau'])
    col6.metric("📄 Fichier", status['fichier'])

    # Diagnostic affichage
    diagnostics = analyser_statut(status)
    if diagnostics:
        st.markdown("### 🧠 Diagnostic automatique")
        for d in diagnostics:
            if d["gravité"] == "critique":
                st.error(f"🚨 {d['problème']} — {d['solution']}")
            elif d["gravité"] == "moyenne":
                st.warning(f"⚠️ {d['problème']} — {d['solution']}")
            else:
                st.info(f"ℹ️ {d['problème']} — {d['solution']}")

    # 🎮 Contrôle à distance
    st.markdown("## 🎮 Contrôle de l'imprimante")
    col1, col2, col3 = st.columns(3)

    if col1.button("🛑 Pause"):
        st.write(envoyer_commande_gcode("M25", selected_port))

    if col2.button("▶️ Reprendre"):
        st.write(envoyer_commande_gcode("M24", selected_port))

    if col3.button("⛔ Stop d'urgence"):
        if st.confirm ("Es-tu sûr de vouloir forcer l'arrêt ?"):
            st.write(envoyer_commande_gcode("M112", selected_port))

elif page == "📊 Historique":
    st.markdown("## 📊 Historique des impressions")
    log_df = load_logs()
    st.dataframe(log_df.tail(5))

    with open("data/logs.csv", "rb") as f:
        st.download_button("📥 Télécharger les logs", f, file_name="logs.csv", mime="text/csv")

    if st.button("🗑️ Réinitialiser les logs"):
        reset_logs()
        st.success("✅ Fichier logs.csv réinitialisé avec succès.")
        st.rerun()

    st.subheader("📈 Températures récentes")
    display_temperature_plotly()
    st.metric("⚙️ Taux de réussite", f"{status['taux_reussite']} %")

    if st.button("📄 Générer rapport PDF"):
        file_path = generate_report_pdf({
            "Fichier": status["fichier"],
            "Durée estimée": status["temps_restant"],
            "Statut": status["etat"],
            "Matériau": status["materiau"],
            "Temp. buse": status["temp_buse"],
            "Temp. plateau": status["temp_bed"]
        })
        with open(file_path, "rb") as f:
            st.download_button("📥 Télécharger le rapport PDF", f, file_name="rapport_impression.pdf")

elif page == "⚙️ Maintenance":
    st.markdown("## 🛠️ Maintenance & Alertes")
    st.markdown(f"""
    <ul style='font-size:20px; line-height:1.8'>
      <li>🧽 <b>Prochaine maintenance</b> : {status['maintenance']}</li>
      <li>🧯 <b>Dernière alerte</b> : {status['alerte']}</li>
      <li>🛠️ <b>Utilisation totale</b> : {status['heures_totales']} heures</li>
      <li>📦 <b>Granulés restants</b> : {status['granules_restants']} kg</li>
      <li>🔄 <b>Conso moyenne</b> : {status['moyenne_consommation']} g</li>
      <li>💰 <b>Coût estimé</b> : {status['cout_impression']} €</li>
    </ul>
    """, unsafe_allow_html=True)

elif page == "📂 G-code":
    st.markdown("## 📂 Analyse G-code")
    uploaded_gcode = st.file_uploader("Charger un fichier .gcode", type=["gcode"])
    if uploaded_gcode:
        gcode_lines = uploaded_gcode.read().decode("latin-1").splitlines()
        st.success(f"✅ Fichier chargé : {uploaded_gcode.name}")
        st.write(f"📄 Nombre de lignes : {len(gcode_lines)}")
        estimation_minutes = len(gcode_lines) * 2 / 60
        st.write(f"⏱️ Durée estimée : {round(estimation_minutes)} minutes")

        if st.button("✅ Simuler fin d’impression"):
            log_impression(uploaded_gcode.name, "Réussie", f"{round(estimation_minutes)} min", "2025-05-13")
            st.success("Impression enregistrée dans les logs.")
            st.rerun()
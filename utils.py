import pandas as pd
import os
import plotly.express as px
from fpdf import FPDF
import streamlit as st
import serial

def envoyer_commande_gcode(cmd, port="COM3", baudrate=115200):
    try:
        with serial.Serial(port, baudrate, timeout=2) as ser:
            ser.write((cmd + "\n").encode())
            return f"✅ Commande envoyée au port {port}: {cmd}"
    except Exception as e:
        return f"❌ Erreur de communication avec {port}: {e}"





# Fonction pour afficher le graphique des températures
def display_temperature_plotly():
    # Exemple de données
    data = {
        "Temps (min)": [0, 1, 2, 3, 4, 5],
        "Température buse (°C)": [0, 50, 100, 150, 200, 220],
        "Température plateau (°C)": [0, 40, 60, 80, 100, 120]
    }

    df = pd.DataFrame(data)

    fig = px.line(df, x="Temps (min)", y=["Température buse (°C)", "Température plateau (°C)"],
                  labels={"Temps (min)": "Temps (min)", "value": "Température (°C)", "variable": "Composant"})
    fig.update_layout(title="Évolution des températures")
    st.plotly_chart(fig)


# Fonction pour charger les logs d'impressions
def load_logs():
    if os.path.exists("data/logs.csv"):
        return pd.read_csv("data/logs.csv")
    else:
        return pd.DataFrame(columns=["Fichier", "Durée", "Statut", "Date"])


# Fonction pour charger les paramètres
def load_settings():
    return {
        "nozzle_temp": 220,
        "bed_temp": 65,
        "material": "Granulés PLA",
        "cost_per_kg": 12.0
    }


# Fonction pour enregistrer une impression dans le fichier de logs
def log_impression(fichier, statut="Réussie", durée="2h15", date="2025-05-13"):
    df = load_logs()
    df.loc[len(df)] = [fichier, durée, statut, date]
    df.to_csv("data/logs.csv", index=False)


# Fonction pour réinitialiser les logs
def reset_logs():
    df = pd.DataFrame(columns=["Fichier", "Durée", "Statut", "Date"])
    df.to_csv("data/logs.csv", index=False)


# Fonction pour générer un rapport PDF
def generate_report_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Titre du rapport
    pdf.cell(200, 10, txt="Rapport d'impression 3D", ln=True, align="C")
    pdf.ln(10)

    # Ajout des données
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

    # Enregistrement du fichier PDF
    file_path = "report_impression.pdf"
    pdf.output(file_path)

    return file_path
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
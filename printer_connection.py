import serial
import re

# Fonction pour récupérer l'état de l'imprimante
def get_printer_status():
    try:
        # Connexion au port série
        ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=2)
        ser.flushInput()
        ser.write(b"M105\n")  # Envoie de la commande pour obtenir les températures
        response = ser.readline().decode(errors='ignore')  # Lecture de la réponse
        ser.close()

        # Extraction des informations via expression régulière
        match = re.search(r"T:(\d+\.?\d*) /?(\d+\.?\d*)? B:(\d+\.?\d*) /?(\d+\.?\d*)?", response)
        if match:
            temp_buse = float(match.group(1))
            cible_buse = float(match.group(2)) if match.group(2) else 0.0
            temp_bed = float(match.group(3))
            cible_bed = float(match.group(4)) if match.group(4) else 0.0
        else:
            temp_buse = cible_buse = temp_bed = cible_bed = 0.0

        # Retourner les informations sous forme de dictionnaire
        return {
            "etat": "En impression",
            "temp_buse": temp_buse,
            "cible_buse": cible_buse,
            "temp_bed": temp_bed,
            "cible_bed": cible_bed,
            "vitesse": 35,
            "temps_restant": "2 h 15 min",
            "materiau": "Granulés de PLA",
            "poids_utilise": 153,
            "fichier": "boitier_capteur_v2.gcode",
            "taux_reussite": 85,
            "maintenance": "changer buse (5 h restantes)",
            "alerte": "Température buse instable",
            "heures_totales": 123,
            "granules_restants": 0.8,
            "moyenne_consommation": 120,
            "cout_impression": 0.75
        }

    except Exception as e:
        # Retourner les valeurs par défaut en cas d'erreur
        return {
            "etat": "Erreur de connexion",
            "temp_buse": 0, "cible_buse": 0,
            "temp_bed": 0, "cible_bed": 0,
            "vitesse": 0,
            "temps_restant": "--",
            "materiau": "Indéfini",
            "poids_utilise": 0,
            "fichier": "N/A",
            "taux_reussite": 0,
            "maintenance": "Inconnue",
            "alerte": str(e),
            "heures_totales": 0,
            "granules_restants": 0,
            "moyenne_consommation": 0,
            "cout_impression": 0
        }

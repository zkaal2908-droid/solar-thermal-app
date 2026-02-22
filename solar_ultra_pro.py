import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CONSTANTES PHYSIQUES
# =========================
Cp = 4180
kWh_conv = 3.6e6
rho = 1000

# =========================
# FONCTIONS SCIENTIFIQUES
# =========================

def besoin_journalier(nb, conso, T_use, T_cold):
    masse = nb * conso
    Q = masse * Cp * (T_use - T_cold)
    return Q / kWh_conv

def rendement_capteur(eta0, a1, Tm, Ta, G):
    return max(0, eta0 - a1 * (Tm - Ta) / G)

def energie_mensuelle(surface, eta, irradiation):
    return surface * eta * irradiation * 30

def pertes_stockage(volume, T_stock, T_amb):
    U = 0.8
    pertes = U * volume * (T_stock - T_amb) * 0.001
    return pertes

def simulation_annuelle(surface, volume, df, Q_jour, eta0, a1):
    resultats = []
    Q_total = 0
    
    for i in range(len(df)):
        G = df["Irradiation"][i]
        Ta = df["Temperature"][i]
        Tm = 50
        
        eta = rendement_capteur(eta0, a1, Tm, Ta, G)
        Q_mois = energie_mensuelle(surface, eta, G)
        
        pertes = pertes_stockage(volume, 60, Ta)
        Q_mois = max(0, Q_mois - pertes)
        
        Q_total += Q_mois
        resultats.append(Q_mois)
    
    Q_annuel = Q_jour * 365
    fraction = Q_total / Q_annuel
    
    return resultats, Q_total, fraction

def optimisation(df, Q_jour, eta0, a1, cout_m2):
    best = None
    
    for surface in np.arange(2, 20, 0.5):
        for volume in np.arange(100, 800, 50):
            
            _, Q_sol, frac = simulation_annuelle(
                surface, volume, df, Q_jour, eta0, a1)
            
            if 0.6 <= frac <= 0.9:
                investissement = surface * cout_m2
                score = frac / investissement
                
                if best is None or score > best["score"]:
                    best = {
                        "surface": surface,
                        "volume": volume,
                        "fraction": frac,
                        "investissement": investissement,
                        "score": score
                    }
    return best

# =========================
# INTERFACE STREAMLIT
# =========================

st.title("Outil Intelligent Ultra Pro – Dimensionnement Solaire Thermique ECS")

st.sidebar.header("Paramètres utilisateur")

nb = st.sidebar.number_input("Nombre occupants", 1, 10, 4)
conso = st.sidebar.number_input("Consommation L/j/personne", 30, 100, 50)
T_use = st.sidebar.number_input("Température utilisation °C", 40, 70, 55)
T_cold = st.sidebar.number_input("Température eau froide °C", 5, 25, 18)

type_capteur = st.sidebar.selectbox(
    "Type capteur",
    ["Plan vitré", "Tube sous vide"]
)

if type_capteur == "Plan vitré":
    eta0 = 0.75
    a1 = 3.5
else:
    eta0 = 0.85
    a1 = 2.0

cout_m2 = st.sidebar.number_input("Coût par m² (€)", 200, 1200, 450)

df = pd.read_csv("climat_essaouira.csv.txt")


Q_jour = besoin_journalier(nb, conso, T_use, T_cold)

best = optimisation(df, Q_jour, eta0, a1, cout_m2)

if best:

    resultats_mensuels, Q_solaire_annuel, fraction = simulation_annuelle(
        best["surface"], best["volume"], df, Q_jour, eta0, a1)

    economie = Q_solaire_annuel * 0.15
    TR = best["investissement"] / economie

    st.subheader("Résultats optimisés")

    st.write(f"Surface optimale : {best['surface']:.2f} m²")
    st.write(f"Volume optimal ballon : {best['volume']} L")
    st.write(f"Fraction solaire annuelle : {fraction*100:.1f} %")
    st.write(f"Energie solaire annuelle : {Q_solaire_annuel:.0f} kWh")
    st.write(f"Investissement estimé : {best['investissement']:.0f} €")
    st.write(f"Temps de retour : {TR:.1f} ans")

    # Graphique production mensuelle
    plt.figure()
    plt.plot(df["Mois"], resultats_mensuels)
    plt.title("Production solaire mensuelle")
    plt.xlabel("Mois")
    plt.ylabel("Energie (kWh)")
    st.pyplot(plt)

    # Analyse paramétrique
    surfaces = np.arange(2, 20, 1)
    fractions = []

    for s in surfaces:
        _, _, frac = simulation_annuelle(
            s, best["volume"], df, Q_jour, eta0, a1)
        fractions.append(frac)

    plt.figure()
    plt.plot(surfaces, fractions)
    plt.title("Influence surface sur fraction solaire")
    plt.xlabel("Surface (m²)")
    plt.ylabel("Fraction solaire")
    st.pyplot(plt)

else:
    st.warning("Aucune configuration optimale trouvée.")

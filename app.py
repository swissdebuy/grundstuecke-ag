import streamlit as st
import pandas as pd
import requests
import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🔍 Herrenlose Grundstücke finden – Kanton Aargau (LIVE Daten)")
st.markdown("Filtere mögliche herrenlose Grundstücke anhand echter Open-Data-Datenquellen")

# Eingaben im Sidebar
with st.sidebar:
    st.header("🔧 Filter")
    min_flaeche = st.number_input("Minimale Fläche (m²)", min_value=0, value=300)
    eigentuemer_bekannt = st.selectbox("Eigentümer vorhanden?", ["Egal", "Nein (möglicherweise herrenlos)"])
    eigene_name = st.text_input("Dein Name (für PDF)")
    eigene_mail = st.text_input("Deine E-Mail (optional)")

# Beispielhafter Zugriff auf öffentlich verfügbare GeoJSON-Daten (Open Data AG)
@st.cache_data

def lade_parzellen():
    url = "https://geo.ag.ch/api/ggg/Parzellen.json"  # Beispiel-URL – ersetzt durch echte Quelle
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['features'])
            return df
        else:
            st.error(f"Fehler beim Laden der Daten: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return pd.DataFrame()

raw_df = lade_parzellen()

if not raw_df.empty:
    # Vereinfachtes Extrahieren der Inhalte (anpassen je nach echter Struktur)
    df = pd.json_normalize(raw_df["properties"])
    if "Flaeche_m2" in df.columns:
        df = df.rename(columns={"Flaeche_m2": "Flaeche"})

    # Simuliere: Wenn EGRID leer, dann möglicherweise herrenlos
    df["EGRID"] = df.get("EGRID", pd.Series(["" for _ in range(len(df))]))
    df = df[df["Flaeche"] >= min_flaeche]
    if eigentuemer_bekannt == "Nein (möglicherweise herrenlos)":
        df = df[df["EGRID"] == ""]

    st.subheader("📋 Gefundene Grundstücke:")
    st.write(f"{len(df)} Treffer")
    st.dataframe(df)

    # Karte
    if "lat" in df.columns and "lon" in df.columns:
        st.subheader("🗺️ Lagekarte der Grundstücke")
        m = folium.Map(location=[47.38, 8.04], zoom_start=10)
        for _, row in df.iterrows():
            folium.Marker(
                [row["lat"], row["lon"]],
                tooltip=f"Parzelle: {row.get('Parzelle','')}\nFläche: {row.get('Flaeche','')} m²"
            ).add_to(m)
        st_data = st_folium(m, width=1200, height=600)

    # PDF Download
    if not df.empty:
        text = f"Bericht – Herrenlose Grundstücke Kanton Aargau\nErstellt am: {datetime.date.today()}\n"
        text += f"Name: {eigene_name}\nE-Mail: {eigene_mail}\n\n"
        for _, row in df.iterrows():
            text += f"Parzelle {row.get('Parzelle','')} – Fläche: {row.get('Flaeche','')} m²\n"
            text += f"EGRID: {row.get('EGRID','')}\n\n"
        st.download_button("📄 Bericht als TXT", text, file_name="bericht.txt")

else:
    st.warning("Noch keine Grundstücke gefunden oder Verbindung fehlgeschlagen.")

st.caption("© 2025 Automatisierte Recherchehilfe Schweiz")

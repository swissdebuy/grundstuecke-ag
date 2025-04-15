import streamlit as st
import pandas as pd
import datetime

# Titel und Beschreibung
st.title("🔍 Herrenlose Grundstücke finden – Kanton Aargau")
st.markdown("Finde Grundstücke ohne EGRID/Eigentümerangabe – basierend auf öffentlich zugänglichen Daten")

# Eingabefelder
with st.sidebar:
    st.header("🔧 Filter")
    min_flaeche = st.number_input("Minimale Fläche (m²)", min_value=0, value=300)
    eigentuemer_bekannt = st.selectbox("Eigentümer vorhanden?", ["Egal", "Nein (möglicherweise herrenlos)"])
    eigene_name = st.text_input("Dein Name (für PDF)")
    eigene_mail = st.text_input("Deine E-Mail (für Behörde optional)")

# Beispielhafte Daten
data = pd.DataFrame({
    "Parzelle": ["1234", "5678", "8765"],
    "Gemeinde": ["Aarau", "Baden", "Zofingen"],
    "Flaeche_m2": [560, 420, 310],
    "EGRID": ["", "", ""],
    "Geoportal": [
        "https://geo.ag.ch/parzelle/1234",
        "https://geo.ag.ch/parzelle/5678",
        "https://geo.ag.ch/parzelle/8765"
    ],
    "Behoerde": [
        "grundbuchamt@aarau.ch",
        "grundbuchamt@baden.ch",
        "grundbuchamt@zofingen.ch"
    ]
})

# Filter anwenden
filtered = data[data["Flaeche_m2"] >= min_flaeche]
if eigentuemer_bekannt == "Nein (möglicherweise herrenlos)":
    filtered = filtered[filtered["EGRID"] == ""]

# Ergebnisse anzeigen
st.subheader("📋 Gefundene Grundstücke:")
st.write(f"{len(filtered)} Treffer gefunden")
st.dataframe(filtered)

# PDF-Download vorbereiten (Textformat für Demo)
if not filtered.empty:
    text = f"Herrenlose Grundstücke – Aargau (erstellt am {datetime.date.today()})\n"
    text += f"Name: {eigene_name}\nE-Mail: {eigene_mail}\n\n"
    text += f"Filter: Fläche > {min_flaeche} m², Eigentümer unbekannt = {eigentuemer_bekannt}\n\n"
    for _, row in filtered.iterrows():
        text += f"Parzelle {row['Parzelle']} – {row['Gemeinde']} – {row['Flaeche_m2']} m²\n"
        text += f"Verdacht: herrenlos\n"
        text += f"Geoportal: {row['Geoportal']}\n"
        text += f"Kontakt: {row['Behoerde']}\n\n"
    st.download_button("📄 PDF-Bericht erstellen", text, file_name="grundstuecke_bericht.txt")
else:
    st.warning("Keine Grundstücke gefunden mit diesen Filtern.")

st.caption("© 2025 Automatisierte Recherchehilfe Schweiz")

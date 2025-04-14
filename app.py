import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import time
import io
import csv

st.set_page_config(page_title="Grundstücks-Finder AG", layout="wide")
st.title("🏡 Automatischer Grundstücks-Finder – Kanton Aargau")

st.markdown("Bitte gib deine Kontaktdaten ein. Diese werden für das PDF-Anschreiben und die E-Mail-Links verwendet:")
user_name = st.text_input("Vollständiger Name")
user_address = st.text_input("Adresse")
user_email = st.text_input("E-Mail")

st.markdown("---")
st.markdown("### Gemeindedaten (CSV hochladen oder integrierte Demo verwenden)")

default_csv = """Gemeinde,xmin,ymin,xmax,ymax,email
Aarau,2635000,1250000,2637000,1252000,info@aarau.ch
Baden,2670000,1252000,2672000,1254000,info@baden.ch
Brugg,2640000,1250000,2642000,1252000,info@brugg.ch
Lenzburg,2637000,1248000,2639000,1250000,info@lenzburg.ch
Zofingen,2626000,1246000,2628000,1248000,info@zofingen.ch
"""

gemeinden = []

uploaded_file = st.file_uploader("Optional: Eigene CSV-Datei hochladen", type="csv")
if uploaded_file is not None:
    reader = csv.DictReader(io.StringIO(uploaded_file.getvalue().decode("utf-8")))
else:
    reader = csv.DictReader(io.StringIO(default_csv))

for row in reader:
    try:
        gemeinden.append({
            "name": row["Gemeinde"],
            "bbox": (float(row["xmin"]), float(row["ymin"]), float(row["xmax"]), float(row["ymax"])),
            "email": row.get("email", "")
        })
    except:
        continue

if st.button("🔍 Gesamten Kanton Aargau durchsuchen"):
    if not (user_name and user_address and user_email):
        st.error("Bitte alle Felder ausfüllen.")
    else:
        st.info("Suche läuft... bitte etwas Geduld.")
        grundstuecke = []
        headers = {"User-Agent": "Mozilla/5.0"}

        for idx, gemeinde in enumerate(gemeinden):
            xmin, ymin, xmax, ymax = gemeinde["bbox"]
            query_url = f"https://api.geo.ag.ch/services/rest/featurelayer/AVParzellen/MapServer/0/query?f=json&where=1%3D1&geometryType=esriGeometryEnvelope&geometry={{\"xmin\":{xmin},\"ymin\":{ymin},\"xmax\":{xmax},\"ymax\":{ymax}}}&inSR=2056&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false"

            try:
                response = requests.get(query_url, headers=headers)
                data = response.json()
                features = data.get("features", [])

                for f in features:
                    attr = f["attributes"]
                    if not attr.get("EGRID"):
                        grundstuecke.append({
                            "Parzelle": attr.get("PARZELLENNUMMER", "-"),
                            "Gemeinde": gemeinde["name"],
                            "Fläche (m²)": attr.get("Flaeche_QM", 0),
                            "Status": "Verdacht auf herrenlos",
                            "Kontakt": gemeinde.get("email", "")
                        })

                st.write(f"✓ {gemeinde['name']} durchsucht ({idx+1}/{len(gemeinden)})")
            except Exception as e:
                st.warning(f"Fehler bei {gemeinde['name']}: {e}")
            time.sleep(1.0)

        if not grundstuecke:
            st.warning("Keine herrenlosen Grundstücke gefunden.")
        else:
            df = pd.DataFrame(grundstuecke)
            st.success(f"{len(df)} mögliche herrenlose Grundstücke gefunden.")
            st.dataframe(df)

            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button("📥 CSV herunterladen", data=csv_buf.getvalue(), file_name="grundstuecke_ag.csv")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Grundstücksanalyse Kanton Aargau", ln=True, align='C')

            for g in grundstuecke:
                pdf.ln(6)
                pdf.set_font("Arial", size=11)
                pdf.cell(200, 10, txt=f"Parzelle: {g['Parzelle']}", ln=True)
                pdf.cell(200, 10, txt=f"Gemeinde: {g['Gemeinde']}", ln=True)
                pdf.cell(200, 10, txt=f"Fläche: {g['Fläche (m²)']} m²", ln=True)
                pdf.cell(200, 10, txt=f"Behörde: {g['Kontakt']}", ln=True)
                pdf.set_font("Arial", style='B', size=11)
                pdf.cell(200, 10, txt="Kontaktanfrage", ln=True)
                pdf.set_font("Arial", size=11)
                anschreiben = (
                    f"Sehr geehrte Damen und Herren,\\n\\n"
                    f"ich habe festgestellt, dass die Parzelle {g['Parzelle']} in {g['Gemeinde']} möglicherweise keinen eingetragenen Eigentümer hat.\\n"
                    f"Bitte teilen Sie mir mit, ob dieses Grundstück als herrenlos gilt und ob ich ein Aneignungsgesuch stellen kann.\\n\\n"
                    f"Mit freundlichen Grüßen\\n{user_name}\\n{user_address}\\n{user_email}"
                )
                pdf.multi_cell(0, 10, txt=anschreiben)

                if g['Kontakt']:
                    mailto = f"mailto:{g['Kontakt']}?subject=Anfrage%20zu%20Parzelle%20{g['Parzelle']}&body={anschreiben.replace(chr(10), '%0A')}"
                    st.markdown(f"[📧 E-Mail an {g['Gemeinde']}]({mailto})")

            pdf_bytes = pdf.output(dest='S').encode('latin1')
            st.download_button("📄 PDF Bericht mit Anfragen", data=pdf_bytes, file_name="grundstuecke_ag_bericht.pdf")

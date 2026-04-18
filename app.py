import streamlit as st
import os

# ── CONFIGURATION PAGE ───────────────────────────────────────
st.set_page_config(
    page_title="GeoClimate Mini - Lyon",
    page_icon="🌡️",
    layout="wide"
)

# ── TITRE ────────────────────────────────────────────────────
st.title("GeoClimate Mini")
st.subheader("Analyse des ilots de chaleur urbains - Lyon, 19 aout 2023")
st.markdown("---")

# ── DONNEES EN DUR (calculees localement) ────────────────────
temp_min  = 29.9
temp_max  = 60.3
temp_moy  = 45.8
seuil     = 50.8
pct_ilots = 4.4

# ── INDICATEURS CLES ─────────────────────────────────────────
st.header("Indicateurs cles")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Temp. minimale",  f"{temp_min} C", "Fleuves, parcs")
col2.metric("Temp. maximale",  f"{temp_max} C", "Toits, bitume")
col3.metric("Temp. moyenne",   f"{temp_moy} C", "Moyenne urbaine")
col4.metric("Seuil ICU",       f"{seuil} C",    "Moy. + 5C")
col5.metric("Surface ICU",     f"{pct_ilots} %","En surchauffe")

st.markdown("---")

# ── CARTES ───────────────────────────────────────────────────
st.header("Cartographie thermique")

col_carte1, col_carte2 = st.columns(2)

with col_carte1:
    st.subheader("Temperature de surface complete")
    if os.path.exists("LST_lyon.png"):
        st.image("LST_lyon.png", use_container_width=True)
    else:
        st.warning("LST_lyon.png non trouve")

with col_carte2:
    st.subheader("Carte interactive Folium")
    if os.path.exists("ilots_chaleur_lyon.html"):
        with open("ilots_chaleur_lyon.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=500)
    else:
        st.warning("ilots_chaleur_lyon.html non trouve")

st.markdown("---")

# ── RAPPORT PDF ──────────────────────────────────────────────
st.header("Rapport PDF")

if os.path.exists("rapport_geoclimate_lyon.pdf"):
    with open("rapport_geoclimate_lyon.pdf", "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="Telecharger le rapport PDF",
        data=pdf_bytes,
        file_name="rapport_geoclimate_lyon.pdf",
        mime="application/pdf"
    )
    st.success("Rapport disponible au telechargement")
else:
    st.warning("Rapport PDF non trouve")

st.markdown("---")

# ── METHODOLOGIE ─────────────────────────────────────────────
st.header("Methodologie")

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.markdown("**Donnees**")
    st.markdown("""
- Satellite : Landsat 9
- Date : 19 aout 2023
- Bande : ST B10 (thermique)
- Resolution : 30m x 30m
- Source : USGS / Copernicus
    """)

with col_m2:
    st.markdown("**Traitement**")
    st.markdown("""
- Lecture : rasterio
- Calcul LST : formule USGS C2L2
- Decoupage : contour Lyon IGN
- Visualisation : matplotlib, folium
    """)

with col_m3:
    st.markdown("**Intelligence artificielle**")
    st.markdown("""
- Modele : Llama 3.2 (Ollama)
- Execution : 100% locale
- Usage : generation rapport texte
- Cout : 0 euro
    """)

st.markdown("---")

# ── A PROPOS ─────────────────────────────────────────────────
st.header("A propos")
st.markdown("""
**GeoClimate Mini** est une application beta demontrant la faisabilite d'une 
analyse automatisee des ilots de chaleur urbains a partir de donnees satellite gratuites.

**Stack technique :**
Python - rasterio - GeoPandas - Folium - Ollama (LLM local) - Streamlit

**Budget total du projet : moins de 20 euros**

**Code source :** [github.com/c7rta95/geoclimate-mini](https://github.com/c7rta95/geoclimate-mini)
""")

st.caption("GeoClimate Mini - Beta v1.0 - Donnees : Landsat 9 / USGS - IA : Ollama llama3.2")
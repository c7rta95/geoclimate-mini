import numpy as np
import requests
from fpdf import FPDF, XPos, YPos
import os

# ── CHARGEMENT DES STATISTIQUES ─────────────────────────────
print("Chargement des donnees Lyon...")
LST_lyon = np.load("LST_lyon.npy")

temp_min  = round(float(np.nanmin(LST_lyon)), 1)
temp_max  = round(float(np.nanmax(LST_lyon)), 1)
temp_moy  = round(float(np.nanmean(LST_lyon)), 1)
seuil     = round(temp_moy + 5, 1)

total     = int(np.sum(~np.isnan(LST_lyon)))
ilots     = int(np.sum(LST_lyon > seuil))
pct_ilots = round(ilots / total * 100, 1)

print(f"Temp min    : {temp_min} C")
print(f"Temp max    : {temp_max} C")
print(f"Temp moy    : {temp_moy} C")
print(f"Seuil ICU   : {seuil} C")
print(f"Surface ICU : {pct_ilots} % de Lyon")

# ── GENERATION DU TEXTE PAR OLLAMA ──────────────────────────
print("\nGeneration du rapport par IA...")

prompt = f"""Tu es un expert en climatologie urbaine et en amenagement du territoire.
Voici les resultats d'une analyse thermique satellite de Lyon (Landsat 9, 19 aout 2023) :

- Temperature de surface minimale : {temp_min} C (zones fraiches : fleuves, parcs)
- Temperature de surface maximale : {temp_max} C (toits sombres, bitume)
- Temperature de surface moyenne : {temp_moy} C
- Seuil ilot de chaleur urbain (ICU) : {seuil} C (moyenne + 5 C)
- Surface en ICU : {pct_ilots} % du territoire lyonnais

Redige un rapport structure en 3 paragraphes en francais, sans caracteres speciaux, sans tirets longs, sans puces :
1. CONSTAT : decris la situation thermique observee le 19 aout 2023 a Lyon
2. CAUSES : explique les causes probables des ilots de chaleur identifies
3. RECOMMANDATIONS : propose 4 recommandations concretes de vegetalisation et d'amenagement

Sois precis et professionnel. Cite les donnees chiffrees. Maximum 400 mots.
N'utilise pas de caracteres speciaux, uniquement des lettres, chiffres, virgules et points."""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }
)

rapport_brut = response.json()["response"]

# Nettoyage complet du texte
def nettoyer(texte):
    remplacements = {
        "\u2014": "-", "\u2013": "-", "\u2012": "-",
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u00e9": "e", "\u00e8": "e", "\u00ea": "e", "\u00eb": "e",
        "\u00e0": "a", "\u00e2": "a", "\u00e4": "a",
        "\u00ee": "i", "\u00ef": "i",
        "\u00f4": "o", "\u00f6": "o",
        "\u00f9": "u", "\u00fb": "u", "\u00fc": "u",
        "\u00e7": "c",
        "\u00c9": "E", "\u00c0": "A", "\u00c8": "E",
        "\u2022": "-", "\u2023": "-", "\u25cf": "-",
        "\u00b0": " degres",
        "\n\n": "\n",
        "**": "", "*": "",
    }
    for ancien, nouveau in remplacements.items():
        texte = texte.replace(ancien, nouveau)
    texte = texte.encode("ascii", errors="replace").decode("ascii")
    texte = texte.replace("?", " ")
    return texte

rapport_propre = nettoyer(rapport_brut)

print("\n--- RAPPORT GENERE ---")
print(rapport_propre)
print("----------------------")

# ── GENERATION DU PDF ────────────────────────────────────────
print("\nGeneration du PDF...")

class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 80, 50)
        self.rect(0, 0, 210, 28, "F")
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.set_y(8)
        self.cell(0, 8, "GeoClimate Mini - Analyse thermique urbaine",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 11)
        self.cell(0, 6, "Lyon - Landsat 9 - 19 aout 2023",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, "Source : Landsat 9 / USGS - Rapport genere automatiquement par IA",
                  align="C")

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Indicateurs cles
pdf.set_font("Helvetica", "B", 13)
pdf.set_text_color(30, 80, 50)
pdf.cell(0, 8, "Indicateurs cles",
         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_draw_color(30, 80, 50)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

indicateurs = [
    ("Temperature minimale",   f"{temp_min} C",   "Zones fraiches : Rhone, Saone, parcs"),
    ("Temperature maximale",   f"{temp_max} C",   "Toits sombres, surfaces bitumees"),
    ("Temperature moyenne",    f"{temp_moy} C",   "Moyenne urbaine Lyon"),
    ("Seuil ilot de chaleur",  f"{seuil} C",      "Moyenne + 5 C"),
    ("Surface en ICU",         f"{pct_ilots} %",  "Part du territoire en surchauffe"),
]

for label, valeur, note in indicateurs:
    pdf.set_fill_color(240, 248, 240)
    pdf.rect(10, pdf.get_y(), 190, 10, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(80, 10, label)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(180, 30, 30)
    pdf.cell(30, 10, valeur)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, note,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

pdf.ln(6)

# Rapport IA
pdf.set_font("Helvetica", "B", 13)
pdf.set_text_color(30, 80, 50)
pdf.cell(0, 8, "Analyse et recommandations",
         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(0, 0, 0)
pdf.multi_cell(0, 6, rapport_propre)
pdf.ln(6)

# Carte thermique
if os.path.exists("LST_lyon.png"):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 80, 50)
    pdf.cell(0, 8, "Cartographie thermique",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.image("LST_lyon.png", x=10, w=190)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Gauche : LST complete - Droite : ilots de chaleur",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Sauvegarde
pdf.output("rapport_geoclimate_lyon.pdf")
print("\nRapport sauvegarde : rapport_geoclimate_lyon.pdf")
print("Ouvrez-le dans l'explorateur Windows !")
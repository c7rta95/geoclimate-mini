import numpy as np
import folium
from folium.plugins import HeatMap
from affine import Affine
import geopandas as gpd
from pyproj import Transformer
import warnings
warnings.filterwarnings("ignore")

# ── CHARGEMENT DES DONNÉES ───────────────────────────────────
print("Chargement des données Lyon...")
LST_lyon = np.load("LST_lyon.npy")
tf_array = np.load("transform_lyon.npy")
transform = Affine(tf_array[0], tf_array[1], tf_array[2],
                   tf_array[3], tf_array[4], tf_array[5])

print(f"Dimensions : {LST_lyon.shape}")
print(f"Temp min   : {np.nanmin(LST_lyon):.1f} °C")
print(f"Temp max   : {np.nanmax(LST_lyon):.1f} °C")
print(f"Temp moy   : {np.nanmean(LST_lyon):.1f} °C")

# ── CONVERSION PIXELS → COORDONNÉES GPS ─────────────────────
print("\nConversion en coordonnées GPS...")

transformer = Transformer.from_crs("EPSG:32631", "EPSG:4326", always_xy=True)

# 1 pixel sur 3 pour une nappe fluide (~15 000 points)
pas = 3
points = []

rows, cols = LST_lyon.shape
for i in range(0, rows, pas):
    for j in range(0, cols, pas):
        valeur = LST_lyon[i, j]
        if np.isnan(valeur):
            continue
        x_utm = transform.c + j * transform.a
        y_utm = transform.f + i * transform.e
        lon, lat = transformer.transform(x_utm, y_utm)
        poids = float((valeur - 20) / (55 - 20))
        poids = max(0.0, min(1.0, poids))  # forcer entre 0 et 1
        points.append([lat, lon, poids])

print(f"Points générés : {len(points):,}")

# ── CRÉATION DE LA CARTE FOLIUM ──────────────────────────────
print("\nCréation de la carte Folium...")

carte = folium.Map(
    location=[45.75, 4.85],
    zoom_start=13,
    tiles="CartoDB positron"
)

# Contour de Lyon
lyon_gdf = gpd.read_file("lyon.geojson")
folium.GeoJson(
    lyon_gdf,
    style_function=lambda x: {
        "fillColor": "none",
        "color": "#222222",
        "weight": 2.5,
    },
    name="Contour Lyon"
).add_to(carte)

# HeatMap fluide
HeatMap(
    points,
    min_opacity=0.35,
    max_opacity=0.9,
    radius=18,
    blur=15,
    gradient={
        "0.0": "#313695",
        "0.3": "#74add1",
        "0.5": "#fee090",
        "0.7": "#f46d43",
        "0.9": "#d73027",
        "1.0": "#a50026"
    },
    name="Température de surface"
).add_to(carte)

# Légende
legende_html = """
<div style="
    position: fixed;
    bottom: 30px; left: 30px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: Arial, sans-serif;
    font-size: 13px;
    z-index: 1000;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    line-height: 1.8;
">
    <b style="font-size:14px">Température de surface</b><br>
    <b>Lyon — 19 août 2023</b><br>
    <hr style="margin:6px 0; border-color:#eee">
    <span style="background:#a50026;padding:2px 12px;border-radius:3px;display:inline-block;width:16px">&nbsp;</span>&nbsp; &gt; 52°C<br>
    <span style="background:#d73027;padding:2px 12px;border-radius:3px;display:inline-block;width:16px">&nbsp;</span>&nbsp; 48–52°C<br>
    <span style="background:#f46d43;padding:2px 12px;border-radius:3px;display:inline-block;width:16px">&nbsp;</span>&nbsp; 44–48°C<br>
    <span style="background:#fee090;padding:2px 12px;border-radius:3px;display:inline-block;width:16px">&nbsp;</span>&nbsp; 38–44°C<br>
    <span style="background:#74add1;padding:2px 12px;border-radius:3px;display:inline-block;width:16px">&nbsp;</span>&nbsp; 30–38°C<br>
    <span style="background:#313695;padding:2px 12px;border-radius:3px;display:inline-block;width:16px">&nbsp;</span>&nbsp; &lt; 30°C<br>
    <hr style="margin:6px 0; border-color:#eee">
    <i style="color:#888">Source : Landsat 9 / USGS</i>
</div>
"""
carte.get_root().html.add_child(folium.Element(legende_html))

# Contrôle des couches
folium.LayerControl().add_to(carte)

# ── SAUVEGARDE ───────────────────────────────────────────────
carte.save("ilots_chaleur_lyon.html")
print("\nCarte sauvegardée : ilots_chaleur_lyon.html ✓")
print("Double-cliquez sur ilots_chaleur_lyon.html pour l'ouvrir !")
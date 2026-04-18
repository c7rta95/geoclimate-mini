import requests
import json
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from rasterio.mask import mask as rio_mask
from affine import Affine
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# ── ÉTAPE 1 : contour de Lyon uniquement (code 69123) ────────
print("Téléchargement du contour de Lyon...")

url = "https://geo.api.gouv.fr/communes/69123?fields=nom,code,contour&format=geojson&geometry=contour"
response = requests.get(url)
with open("lyon.geojson", "wb") as f:
    f.write(response.content)

data = json.loads(response.content)
print(f"Commune : {data['properties']['nom']} ({data['properties']['code']})")
print("lyon.geojson sauvegardé ✓")

# ── ÉTAPE 2 : chargement des données du vendredi ─────────────
print("\nChargement des données LST...")
LST      = np.load("LST_celsius.npy")
tf_array = np.load("transform_info.npy")

transform = Affine(tf_array[0], tf_array[1], tf_array[2],
                   tf_array[3], tf_array[4], tf_array[5])
crs_source = CRS.from_epsg(32631)  # UTM zone 31N

print(f"LST chargée       : {LST.shape}")
print(f"Transform         : {transform}")

# ── ÉTAPE 3 : découpage sur Lyon ─────────────────────────────
print("\nDécoupage sur Lyon...")

lyon_gdf = gpd.read_file("lyon.geojson")
print(f"CRS GeoJSON       : {lyon_gdf.crs}")

# Reprojeter Lyon en UTM 31N pour correspondre à l'image
lyon_utm = lyon_gdf.to_crs(epsg=32631)
geometries = [geom.__geo_interface__ for geom in lyon_utm.geometry]

# Sauvegarder temporairement la LST comme fichier raster
print("Création du raster temporaire...")
with rasterio.open(
    "LST_temp.tif", "w",
    driver="GTiff",
    height=LST.shape[0],
    width=LST.shape[1],
    count=1,
    dtype="float32",
    crs=crs_source,
    transform=transform,
    nodata=np.nan
) as dst:
    dst.write(LST.astype("float32"), 1)

# Découper
with rasterio.open("LST_temp.tif") as src:
    LST_lyon, transform_lyon = rio_mask(src, geometries, crop=True, nodata=np.nan)
    LST_lyon = LST_lyon[0].astype("float32")
    LST_lyon[LST_lyon == 0] = np.nan

print(f"Dimensions Lyon   : {LST_lyon.shape}")
print(f"\n=== Températures sur Lyon ===")
print(f"Min  : {np.nanmin(LST_lyon):.1f} °C")
print(f"Max  : {np.nanmax(LST_lyon):.1f} °C")
print(f"Moy  : {np.nanmean(LST_lyon):.1f} °C")

# ── ÉTAPE 4 : carte matplotlib de vérification ───────────────
print("\nGénération carte de vérification...")
seuil = np.nanmean(LST_lyon) + 5

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

im1 = axes[0].imshow(LST_lyon, cmap="RdYlBu_r", vmin=20, vmax=55)
axes[0].set_title(f"LST Lyon — 19 août 2023")
axes[0].axis("off")
plt.colorbar(im1, ax=axes[0], label="°C", shrink=0.8)

ilots = np.where(LST_lyon > seuil, LST_lyon, np.nan)
axes[1].imshow(LST_lyon, cmap="Greys", alpha=0.4)
im2 = axes[1].imshow(ilots, cmap="Reds", vmin=seuil, vmax=55)
axes[1].set_title(f"Îlots de chaleur Lyon (> {seuil:.1f}°C)")
axes[1].axis("off")
plt.colorbar(im2, ax=axes[1], label="°C", shrink=0.8)

plt.tight_layout()
plt.savefig("LST_lyon.png", dpi=200, bbox_inches="tight")
plt.show()
print("Sauvegardé : LST_lyon.png ✓")

# Sauvegarder pour Folium
np.save("LST_lyon.npy", LST_lyon)
np.save("transform_lyon.npy", np.array(transform_lyon))
print("LST_lyon.npy ✓")
print("transform_lyon.npy ✓")
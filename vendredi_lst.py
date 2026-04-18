import rasterio
import numpy as np
import matplotlib.pyplot as plt

# ── CHEMINS DES FICHIERS ─────────────────────────────────────
chemin_b10 = "landsat_extract/LC09_L2SP_196028_20230819_20230821_02_T1_ST_B10.TIF"
chemin_qa  = "landsat_extract/LC09_L2SP_196028_20230819_20230821_02_T1_QA_PIXEL.TIF"
chemin_b4  = "landsat_extract/LC09_L2SP_196028_20230819_20230821_02_T1_SR_B4.TIF"
chemin_b5  = "landsat_extract/LC09_L2SP_196028_20230819_20230821_02_T1_SR_B5.TIF"

# ── BLOC 1 : lecture de la bande thermique ───────────────────
print("Lecture de ST_B10...")
with rasterio.open(chemin_b10) as src:
    b10       = src.read(1).astype("float32")
    transform = src.transform
    crs       = src.crs

print("Dimensions :", b10.shape)
print("CRS         :", crs)
print("Valeur min  :", b10.min())
print("Valeur max  :", b10.max())
print("Pixels nuls :", (b10 == 0).sum(), "(bords de l'image)")

# Afficher l'image brute
plt.figure(figsize=(10, 8))
plt.imshow(b10, cmap="gray")
plt.colorbar(label="Valeur brute DN")
plt.title("Bande ST_B10 brute — Landsat 9")
plt.savefig("b10_brut.png", dpi=150, bbox_inches="tight")
plt.show()
print("Sauvegardé : b10_brut.png")

# ── BLOC 2 : conversion en températures Celsius ──────────────
print("\nConversion en températures...")

# Masquer les pixels nuls (bords noirs)
b10_masque = np.where(b10 == 0, np.nan, b10)

# Formule officielle USGS Landsat Collection 2 Level-2
LST_kelvin  = b10_masque * 0.00341802 + 149.0
LST_celsius = LST_kelvin - 273.15

print("\n=== Températures de surface ===")
print(f"Min  : {np.nanmin(LST_celsius):.1f} °C")
print(f"Max  : {np.nanmax(LST_celsius):.1f} °C")
print(f"Moy  : {np.nanmean(LST_celsius):.1f} °C")

# ── BLOC 3 : masque nuages ───────────────────────────────────
print("\nApplication du masque nuages...")
with rasterio.open(chemin_qa) as src_qa:
    qa = src_qa.read(1)

masque_nuage = ((qa >> 3) & 1) | ((qa >> 4) & 1)
LST_propre   = np.where(masque_nuage == 1, np.nan, LST_celsius)

print(f"Pixels nuageux masqués  : {(masque_nuage == 1).sum():,}")
print(f"Pixels valides restants : {(~np.isnan(LST_propre)).sum():,}")

# ── BLOC 4 : carte thermique colorée ────────────────────────
print("\nGénération de la carte thermique...")

seuil = np.nanmean(LST_propre) + 5
ilots = np.where(LST_propre > seuil, LST_propre, np.nan)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Carte gauche : températures complètes
im1 = axes[0].imshow(LST_propre, cmap="RdYlBu_r", vmin=10, vmax=55)
axes[0].set_title("Température de surface (°C)\nLandsat 9 — 19 août 2023")
axes[0].axis("off")
plt.colorbar(im1, ax=axes[0], label="°C", shrink=0.8)

# Carte droite : îlots de chaleur mis en évidence
axes[1].imshow(LST_propre, cmap="Greys", alpha=0.4)
im2 = axes[1].imshow(ilots, cmap="Reds", vmin=seuil, vmax=55)
axes[1].set_title(f"Îlots de chaleur (> {seuil:.1f} °C)\nzones au-dessus de la moyenne + 5°C")
axes[1].axis("off")
plt.colorbar(im2, ax=axes[1], label="°C", shrink=0.8)

plt.tight_layout()
plt.savefig("LST_carte.png", dpi=200, bbox_inches="tight")
plt.show()
print("Sauvegardé : LST_carte.png")

# ── BLOC 5 : calcul NDVI (végétation) ───────────────────────
print("\nCalcul du NDVI...")
with rasterio.open(chemin_b4) as src:
    b4 = src.read(1).astype("float32")
with rasterio.open(chemin_b5) as src:
    b5 = src.read(1).astype("float32")

b4   = np.where(b4 == 0, np.nan, b4)
b5   = np.where(b5 == 0, np.nan, b5)
ndvi = (b5 - b4) / (b5 + b4)

print(f"NDVI min : {np.nanmin(ndvi):.2f}  (eau, bitume)")
print(f"NDVI max : {np.nanmax(ndvi):.2f}  (végétation dense)")
print(f"NDVI moy : {np.nanmean(ndvi):.2f}")

# ── BLOC 6 : sauvegarde pour samedi ─────────────────────────
print("\nSauvegarde des données pour samedi...")
np.save("LST_celsius.npy",   LST_propre)
np.save("NDVI.npy",          ndvi)
np.save("transform_info.npy", np.array(transform))
print("LST_celsius.npy  ✓")
print("NDVI.npy         ✓")
print("transform_info.npy ✓")

print("\n=== Vendredi terminé — tout est prêt pour samedi ===")
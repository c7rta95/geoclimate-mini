import tarfile
import os

archive = "landsat_image.tar"
output_dir = "landsat_extract"

os.makedirs(output_dir, exist_ok=True)

with tarfile.open(archive, "r") as tar:
    files = tar.getnames()

    print("Fichiers dans l'archive :")

    for f in files:
        print(f)

    keep_keywords = [
        "ST_B10",
        "SR_B4",
        "SR_B5",
        "QA_PIXEL",
        "MTL.txt"
    ]

    extracted = 0

    print("\nExtraction en cours...\n")

    for f in files:
        if any(k in f for k in keep_keywords):
            tar.extract(f, output_dir)
            print("Extrait :", f)
            extracted += 1

print("\nTerminé")
print("Dossier :", os.path.abspath(output_dir))
print("Nombre de fichiers extraits :", extracted)
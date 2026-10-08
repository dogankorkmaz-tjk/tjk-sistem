from google.colab import drive
drive.mount("/content/drive")
import os, shutil, zipfile, pandas as pd
KOK = "/content/drive/MyDrive/tjk"
HEDEF = "/content/github_veri"
shutil.rmtree(HEDEF, ignore_errors=True)
for tur in ("sonuclar", "temiz", "program"):
    df = pd.read_csv(f"{KOK}/tjk_{tur}.csv", low_memory=False)
    os.makedirs(f"{HEDEF}/data/{tur}", exist_ok=True)
    for ay, g in df.groupby(df.tarih.astype(str).str[:7]):
        g.to_csv(f"{HEDEF}/data/{tur}/{ay}.csv.gz", index=False)
    print(tur, len(df), "satır,", df.tarih.astype(str).str[:7].nunique(), "ay")
shutil.copy(f"{KOK}/model_v1.json", f"{HEDEF}/data/model_v1.json")
ZIP = f"{KOK}/github_veri.zip"
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_STORED) as z:
    for kok, _, dosyalar in os.walk(HEDEF):
        for f in dosyalar:
            tam = os.path.join(kok, f); z.write(tam, os.path.relpath(tam, HEDEF))
print("HAZIR:", ZIP, round(os.path.getsize(ZIP) / 1e6, 1), "MB")

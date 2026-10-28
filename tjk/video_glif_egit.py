"""Rakam şablonlarını başlangıç karelerinden öğrenir (kapı karelerinde şerit 1..N sırasıyla durur). python3 -m tjk.video_glif_egit <şerit_klasörleri...>
Her klasör: s_0001.jpg/png ... (1640x80'e büyütülür), N için klasör adından sonra 'ad:N' verilir."""
import sys, glob, os
import numpy as np
from PIL import Image
from . import video_okuma as VO

def egit(girdi, cikti=VO.YOL, kare=range(0, 4)):
    ham = {str(d): [] for d in range(10)}
    for klasor, n in girdi:
        fr = sorted(glob.glob(os.path.join(klasor, "s_*.*")))
        for i in kare:
            if i >= len(fr): break
            im = Image.open(fr[i]).convert("RGB").resize((1640, 80), Image.LANCZOS)
            for j in range(min(n, 10)):
                g = VO.glifler(im, j)
                if not g: continue
                etiket = str(j + 1)
                if len(g) != len(etiket): continue
                for ch, gg in zip(etiket, g): ham[ch].append(gg)
    sablon = {d: np.mean(v, 0) for d, v in ham.items() if v}
    np.savez(cikti, **sablon)
    return {d: len(v) for d, v in ham.items()}

if __name__ == "__main__":
    girdi = [(a.split(":")[0], int(a.split(":")[1])) for a in sys.argv[1:]]
    print(egit(girdi))

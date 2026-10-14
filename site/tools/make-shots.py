#!/usr/bin/env python3
"""Génère les captures d’écran des cartes de la page d’accueil (versionnées dans src/img/).
Prérequis : `pip install playwright pillow` + Chromium. Chaque application a son scénario dans SHOTS.
Usage : python3 tools/make-shots.py [slug …]"""
import io, json, pathlib, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = json.loads((ROOT / "site.json").read_text())

def clip(pg, js):
    x, y, w, h = pg.evaluate(js)
    return pg.screenshot(clip={"x": x, "y": y, "width": w, "height": h})

def stack(parts, bg, pad=20, ratio=10 / 16, scale=2):
    """Empile des captures (même largeur) sur un fond uni, au format 16:10 (hauteur rognée si besoin)."""
    ims = [Image.open(io.BytesIO(p)).convert("RGB") for p in parts]
    pad *= scale
    W = ims[0].width + 2 * pad
    H = round(W * ratio)
    canvas = Image.new("RGB", (W, H), bg)
    y = pad
    for im in ims:
        canvas.paste(im, (pad, y)); y += im.height + pad
    return canvas

def cahier(pg):
    pg.fill("#src", r"\dfrac{3}{4}+\dfrac{1}{8}=\dfrac{6}{8}+\dfrac{1}{8}=\dfrac{7}{8}")
    pg.click("#src"); pg.keyboard.press("End"); pg.keyboard.press("ArrowLeft")
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(400)
    box = "(e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height]})"
    top = clip(pg, box + "(document.querySelector('.sheet'))")
    ed = clip(pg, box + "(document.querySelector('#src').closest('.card'))")
    return stack([top, ed], (234, 238, 246))

# slug -> (scénario qui renvoie une image PIL, largeur, hauteur de la fenêtre)
SHOTS = {"cahier-latex": (cahier, 1080, 1100)}

def main(slugs):
    apps = {a["slug"]: a for a in CONF["apps"]}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for slug in slugs or SHOTS:
            fn, w, h = SHOTS[slug]
            src = (ROOT / CONF["apps_dir"] / apps[slug]["source"]).resolve()
            ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme="light", device_scale_factor=2)
            pg = ctx.new_page()
            pg.goto(src.as_uri())
            pg.wait_for_timeout(500)
            im = fn(pg)
            out = ROOT / "src/img" / f"{slug}.webp"
            im.save(out, "WEBP", quality=84, method=6)
            print(out.relative_to(ROOT), f"{out.stat().st_size // 1024} Ko", im.size)
            ctx.close()
        b.close()

if __name__ == "__main__":
    main(sys.argv[1:])

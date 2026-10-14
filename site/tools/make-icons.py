#!/usr/bin/env python3
"""Génère les icônes PNG (une seule fois ; les PNG sont versionnés dans src/icons/).
Prérequis : `pip install playwright` + Chromium. Relancer seulement pour changer un dessin.
Usage : python3 tools/make-icons.py"""
import base64, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = base64.b64encode((ROOT / "src/fonts/atkinson-hyperlegible-latin-700-normal.woff2").read_bytes()).decode()

# Un dessin = une fonction (taille, plein_cadre) -> contenu SVG. « plein_cadre » : fond jusqu’aux bords (maskable, iOS).
def cahier(full):
    return ('#2448a8', '<text x="256" y="372" text-anchor="middle" font-size="340" font-weight="700" fill="#fff" '
            'font-family="AH">\\</text>', full)

def tables(full):
    return ('#ffc83d', '<text x="256" y="318" text-anchor="middle" font-size="150" font-weight="700" fill="#3b2a00" '
            'font-family="AH">7×8</text>', full)

def site(full):
    # quatre cases : l’idée d’une petite collection d’outils
    g = ''.join(f'<rect x="{x}" y="{y}" width="108" height="108" rx="24" fill="{c}"/>'
                for x, y, c in [(120, 120, '#ffc83d'), (284, 120, '#ffffff'), (120, 284, '#ffffff'), (284, 284, '#ffc83d')])
    return ('#213a86', g, full)

ICONS = {"cahier-latex": cahier, "tables-en-tete": tables, "site": site}

def svg(draw, full, size):
    bg, body, _ = draw(full)
    # plein cadre : le dessin occupe ~62 % du centre (zone sûre des icônes « maskable »)
    scale = 0.62 if full else 0.9
    inner = f'<g transform="translate(256 256) scale({scale}) translate(-256 -256)">{body}</g>'
    shape = (f'<rect width="512" height="512" fill="{bg}"/>' if full
             else f'<rect width="512" height="512" rx="112" fill="{bg}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 512 512">'
            f'<style>@font-face{{font-family:AH;font-weight:700;src:url(data:font/woff2;base64,{FONT})}}</style>'
            f'{shape}{inner}</svg>')

def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for slug, draw in ICONS.items():
            out = ROOT / "src/icons" / slug
            out.mkdir(parents=True, exist_ok=True)
            for name, size, full in [("icon-192.png", 192, False), ("icon-512.png", 512, False),
                                     ("icon-maskable-512.png", 512, True), ("apple-touch-icon.png", 180, True)]:
                pg.set_viewport_size({"width": size, "height": size})
                pg.set_content(f'<body style="margin:0;background:transparent">{svg(draw, full, size)}</body>')
                pg.wait_for_timeout(120)  # le temps que la police soit prête
                pg.screenshot(path=str(out / name), omit_background=True)
        b.close()
    print("Icônes écrites dans src/icons/")

if __name__ == "__main__":
    main()

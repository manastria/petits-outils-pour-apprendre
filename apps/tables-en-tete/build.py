#!/usr/bin/env python3
"""Construit dist/tables-en-tete.html (artifact claude.ai) et dist/tables-en-tete-hors-ligne.html (autonome).
Prérequis : `npm install` dans ce dossier."""
import base64, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent
NM = ROOT / "node_modules"
SRC = ROOT / "src" / "tables-en-tete.src.html"
DIST = ROOT / "dist"

def fonts():
    d = NM / "@fontsource" / "atkinson-hyperlegible" / "files"
    out = ""
    for w, st in [(400, "normal"), (700, "normal")]:
        b = base64.b64encode((d / f"atkinson-hyperlegible-latin-{w}-{st}.woff2").read_bytes()).decode()
        out += (f'@font-face{{font-family:"Atkinson Hyperlegible";font-style:{st};font-weight:{w};font-display:swap;'
                f'src:url(data:font/woff2;base64,{b}) format("woff2")}}\n')
    return out

def main():
    src = SRC.read_text()
    assert "/*FONTS*/" in src
    page = src.replace("/*FONTS*/", fonts())
    DIST.mkdir(exist_ok=True)
    (DIST / "tables-en-tete.html").write_text(page)
    s = page.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    title, rest = s.split("\n", 1)
    doc = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           + title + "\n" + rest.replace('<div class="app">', '</head>\n<body>\n<div class="app">', 1)
           + "\n</body>\n</html>\n")
    leaks = [u for u in re.findall(r"https?://[\w.-]+", doc) if u != "http://www.w3.org"]
    assert not leaks, f"référence réseau dans la version hors ligne : {set(leaks)}"
    (DIST / "tables-en-tete-hors-ligne.html").write_text(doc)
    for i, js in enumerate(re.findall(r"<script>([\s\S]*?)</script>", doc)):
        tmp = DIST / f".check{i}.js"; tmp.write_text(js)
        try: subprocess.run(["node", "--check", str(tmp)], check=True)
        finally: tmp.unlink(missing_ok=True)
    print("OK :", *(f"{p.name} ({p.stat().st_size // 1024} Ko)" for p in sorted(DIST.glob("*.html"))))

if __name__ == "__main__":
    main()

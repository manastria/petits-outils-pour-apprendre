#!/usr/bin/env python3
"""Construit dist/cahier-latex.html (en ligne) et dist/cahier-latex-hors-ligne.html (autonome).
Prérequis : `npm install` dans ce dossier."""
import base64, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
NM = ROOT / "node_modules"
K = NM / "katex" / "dist"
SRC = ROOT / "src" / "cahier-latex.src.html"
DIST = ROOT / "dist"
CDN_TAG = '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>'

def b64(p): return base64.b64encode(pathlib.Path(p).read_bytes()).decode()

def katex_css():
    css = (K / "katex.min.css").read_text()
    # Ne garder que le woff2 de chaque police, embarqué en data URI
    return re.sub(r'src:url\(fonts/([\w-]+)\.woff2\) format\("woff2"\)[^;}]*',
                  lambda m: f'src:url(data:font/woff2;base64,{b64(K / "fonts" / (m.group(1) + ".woff2"))}) format("woff2")', css)

def atkinson_css():
    out = ""
    for fam, d, faces in [("Atkinson Hyperlegible", "atkinson-hyperlegible", [(400, "normal"), (700, "normal"), (400, "italic")]),
                          ("Atkinson Hyperlegible Mono", "atkinson-hyperlegible-mono", [(400, "normal"), (700, "normal")])]:
        for w, st in faces:
            f = NM / "@fontsource" / d / "files" / f"{d}-latin-{w}-{st}.woff2"
            out += (f'@font-face{{font-family:"{fam}";font-style:{st};font-weight:{w};font-display:swap;'
                    f'src:url(data:font/woff2;base64,{b64(f)}) format("woff2")}}\n')
    return out

def main():
    if not K.exists():
        sys.exit("node_modules absent : lancer `npm install` d’abord.")
    src = SRC.read_text()
    assert "/*KATEX_CSS*/" in src and CDN_TAG in src, "marqueurs de build introuvables dans la source"
    css = katex_css()
    DIST.mkdir(exist_ok=True)

    # 1. Version en ligne (artifact claude.ai : pas de doctype/head/body, KaTeX JS et polices texte par CDN)
    (DIST / "cahier-latex.html").write_text(src.replace("/*KATEX_CSS*/", css))

    # 2. Version hors ligne : tout est embarqué, aucune requête réseau
    s = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n', "", src)
    s = s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    s = s.replace("/*KATEX_CSS*/", css + "\n" + atkinson_css())
    js = (K / "katex.min.js").read_text().replace("</script", "<\\/script")
    s = s.replace(CDN_TAG, "<script>" + js + "</script>")
    title, rest = s.split("\n", 1)
    doc = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           + title + "\n" + rest.replace('<div class="app">', '</head>\n<body>\n<div class="app">', 1)
           + "\n</body>\n</html>\n")
    leaks = [u for u in re.findall(r"https?://[\w.-]+", doc) if u != "http://www.w3.org"]
    assert not leaks, f"la version hors ligne référence encore le réseau : {set(leaks)}"
    (DIST / "cahier-latex-hors-ligne.html").write_text(doc)

    # 3. Vérification syntaxique du script applicatif (dernier <script>)
    app = re.findall(r"<script>([\s\S]*?)</script>", doc)[-1]
    tmp = DIST / ".app-check.js"; tmp.write_text(app)
    try:
        subprocess.run(["node", "--check", str(tmp)], check=True)
    except FileNotFoundError:
        print("node introuvable : vérification syntaxique ignorée")
    finally:
        tmp.unlink(missing_ok=True)
    print("OK :", *(f"{p.name} ({p.stat().st_size // 1024} Ko)" for p in sorted(DIST.glob("*.html"))))

if __name__ == "__main__":
    main()

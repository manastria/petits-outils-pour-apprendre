#!/usr/bin/env python3
"""Test de bout en bout du site construit (site/public/). Prérequis : `pip install playwright` + Chromium.

Sert public/ sous /petits-outils-pour-apprendre/ (comme une page de projet GitHub Pages) et vérifie :
accueil sans requête externe ni erreur, liens internes, pas de défilement horizontal à 390 px (clair et sombre),
pour chaque application en ligne : manifeste, service worker, puis RECHARGEMENT RÉSEAU COUPÉ, fichier à télécharger.
Usage : python3 test/site_test.py [--shots DOSSIER]   (captures de l’accueil et de À propos dans DOSSIER)"""
import functools, http.server, json, pathlib, re, sys, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "public"
CONF = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
PREFIX = "/petits-outils-pour-apprendre"
shots = pathlib.Path(sys.argv[sys.argv.index("--shots") + 1]) if "--shots" in sys.argv else None
if shots:
    shots.mkdir(parents=True, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        return super().translate_path(path[len(PREFIX):] if path.startswith(PREFIX) else "/__absent__")
    def log_message(self, *a): pass

srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(DOCS)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
ORIGIN = f"http://127.0.0.1:{srv.server_address[1]}"
B = ORIGIN + PREFIX + "/"
ok = True

def check(cond, msg):
    global ok
    print(("OK    " if cond else "ÉCHEC ") + msg)
    ok = ok and cond

def no_hscroll(pg):
    return not pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth")

with sync_playwright() as p:
    b = p.chromium.launch()
    # --- Accueil
    ctx = b.new_context(viewport={"width": 1100, "height": 900}, service_workers="block")
    pg = ctx.new_page(); reqs, errs = [], []
    pg.on("request", lambda r: reqs.append(r.url))
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.goto(B); pg.wait_for_load_state("networkidle")
    ext = [u for u in reqs if not u.startswith(ORIGIN) and not u.startswith("data:")]
    check(not ext, f"accueil : aucune requête externe {ext}")
    check(not errs, f"accueil : aucune erreur console {errs}")
    check(pg.evaluate('document.fonts.check("700 18px \\"Atkinson Hyperlegible\\"")'), "accueil : police Atkinson chargée")
    check(no_hscroll(pg), "accueil : pas de défilement horizontal (1100 px)")
    if shots: pg.screenshot(path=str(shots / "accueil-clair.png"), full_page=True)
    bad = []
    for u in sorted({l.split("#")[0] for l in pg.eval_on_selector_all("a[href]", "els=>els.map(e=>e.href)") if l.startswith(B)}):
        s = ctx.request.get(u).status
        if s != 200: bad.append((u, s))
    check(not bad, f"liens internes tous en 200 {bad}")
    ctx.close()
    for scheme in ("light", "dark"):
        c2 = b.new_context(viewport={"width": 390, "height": 800}, color_scheme=scheme, service_workers="block", device_scale_factor=2)
        q = c2.new_page(); q.goto(B); q.wait_for_load_state("networkidle")
        check(no_hscroll(q), f"accueil 390 px ({scheme}) : pas de défilement horizontal")
        if shots: q.screenshot(path=str(shots / f"accueil-390-{scheme}.png"), full_page=True)
        c2.close()
    c3 = b.new_context(viewport={"width": 1100, "height": 900}, service_workers="block"); q = c3.new_page()
    q.goto(B + "apropos/"); q.wait_for_load_state("networkidle")
    check(no_hscroll(q), "À propos : pas de défilement horizontal")
    if shots: q.screenshot(path=str(shots / "apropos.png"), full_page=True)
    c3.close()

    # --- Chaque application en ligne : installation puis hors ligne
    for a in [a for a in CONF["apps"] if a["status"] == "essai"]:
        slug, name = a["slug"], a["name"]
        ctx = b.new_context(viewport={"width": 1100, "height": 800}); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(B + slug + "/"); pg.wait_for_load_state("networkidle")
        pg.evaluate("navigator.serviceWorker.ready.then(()=>1)"); pg.wait_for_timeout(1500)
        keys = pg.evaluate("caches.keys()")
        check(any(k.startswith(f"petits-outils-{slug}-") for k in keys), f"{name} : service worker actif, cache créé {keys}")
        man = ctx.request.get(B + slug + "/manifest.webmanifest").json()
        check(man["name"] == name and len(man["icons"]) == 3, f"{name} : manifeste valide")
        pg.reload(); pg.wait_for_load_state("networkidle")
        check(pg.evaluate("!!navigator.serviceWorker.controller"), f"{name} : page contrôlée par le service worker")
        ctx.set_offline(True)
        pg.reload(); pg.wait_for_load_state("load"); pg.wait_for_timeout(600)
        check(pg.title() != "" and pg.locator("body").inner_text().strip() != "", f"{name} : HORS LIGNE, la page se recharge")
        if slug == "cahier-latex":
            pg.fill("#src", r"\dfrac{12}{24}=\dfrac{1}{2}"); pg.wait_for_timeout(500)
            check(pg.locator(".katex").count() > 0, f"{name} : HORS LIGNE, KaTeX affiche la formule")
        check(not errs, f"{name} : aucune erreur de script hors ligne {errs}")
        ctx.set_offline(False)
        r = ctx.request.get(B + f"{slug}/{slug}-hors-ligne.html")
        check(r.status == 200 and b"serviceWorker" not in r.body(), f"{name} : fichier à télécharger ({len(r.body()) // 1024} Ko), sans service worker")
        ctx.close()
    b.close()

srv.shutdown()
print("\nTOUT PASSE" if ok else "\nÉCHECS")
sys.exit(0 if ok else 1)

#!/usr/bin/env python3
"""Construit le site statique dans site/public/ (publié par GitHub Actions, voir .github/workflows/publier.yml).

Entrées : site.json, src/ (pages, CSS, polices, icônes, captures), les fichiers « hors ligne » des applications
(chemins relatifs à `apps_dir`, soit ../apps : construire d’abord les applications, ou lancer `python3 build.py` à la racine).
Aucune dépendance : bibliothèque standard Python uniquement.

Pour chaque application « en ligne » (status = essai) :
  public/<slug>/index.html                 la page installable (manifeste + service worker injectés)
  public/<slug>/<slug>-hors-ligne.html     le fichier autonome à télécharger (identique à la source)
  public/<slug>/manifest.webmanifest, sw.js, icon-*.png
"""
import hashlib, html, json, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent
CONF = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
REPO = ROOT.parent
OUT = ROOT / "public"
SRC = ROOT / "src"
NB = " "  # espace fine insécable
WARN = []
SITE_URL = CONF["site_url"].rstrip("/") + "/" if CONF.get("site_url") else ""


def seo_head(path, title, desc, image="icon-512.png"):
    """Balises pour les moteurs de recherche et les aperçus de partage. L’URL absolue ne sert qu’aux moteurs :
    les liens de navigation restent relatifs. Sans « site_url », pas d’URL canonique ni d’image de partage."""
    t, ds = esc(title), esc(desc)
    h = (f'<meta name="description" content="{ds}">\n'
         '<meta property="og:type" content="website">\n<meta property="og:locale" content="fr_FR">\n'
         f'<meta property="og:title" content="{t}">\n<meta property="og:description" content="{ds}">\n')
    if SITE_URL:
        h += (f'<link rel="canonical" href="{SITE_URL}{path}">\n<meta property="og:url" content="{SITE_URL}{path}">\n'
              f'<meta property="og:image" content="{SITE_URL}{image}">\n')
    return h


# ---------- Typographie française (règles du Lexique de l’Imprimerie nationale) ----------
# « ; ? ! » : espace fine insécable (U+202F) ; « : » : espace insécable (U+00A0) ; guillemets : U+202F à l’intérieur.
MASK = "\ue000"  # remplace une balise : la ponctuation après un lien reste « collée » au mot précédent


def typo_text(s):
    s = re.sub(r"(?<=\w)'(?=\w)", "’", s)
    s = re.sub(r"«[ \u00a0\u202f]+", "«" + NB, s)
    s = re.sub(r"[ \u00a0\u202f]+»", NB + "»", s)
    s = re.sub(r"(?<=\S)[ \u00a0\u202f]+([;?!])", NB + r"\1", s)
    s = re.sub(r"(?<=\S)[ \u00a0\u202f]+:", "\u00a0:", s)
    return s


def typo_html(h):
    tags = []
    masked = re.sub(r"<[^>]*>", lambda m: (tags.append(m.group(0)), MASK)[1], h)
    masked = typo_text(masked)
    it = iter(tags)
    return re.sub(MASK, lambda m: next(it), masked)


def lint(page, h):
    """Signale ce que la typographie automatique ne peut pas deviner (ponctuation collée au mot, apostrophe droite…)."""
    errs = []
    body = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", h)
    for t in re.split(r"(<[^>]*>)", body):
        if t.startswith("<"):
            continue
        t = re.sub(r"&#?\w+;", "", t)
        for m in re.finditer(r"[^\s\u202f\u00a0][?!;]|[A-Za-zÀ-ÿ)»]:(?=\s|$)|'|\"|«[ \u00a0]|[ \u00a0]»|[ \u202f]:", t):
            errs.append(f"{page} : « …{t[max(0, m.start() - 15):m.end() + 10].strip()}… »")
    return errs


def esc(s):
    return html.escape(typo_text(s), quote=True)


# ---------- Applications ----------
LEAK = re.compile(r"https?://[\w.-]+")


def fail(msg):
    sys.exit(f"ERREUR : {msg}")


def app_source(a):
    p = (ROOT / CONF["apps_dir"] / a["source"]).resolve()
    if not p.exists():
        fail(f"fichier introuvable pour « {a['name']} » : {p}\n  (construire l’application d’abord, ou corriger apps_dir / source dans site.json)")
    return p


def build_app(a):
    slug = a["slug"]
    doc = app_source(a).read_text(encoding="utf-8").replace("\r\n", "\n")
    leaks = {u for u in LEAK.findall(doc) if u != "http://www.w3.org"}
    if leaks:
        fail(f"{a['name']} fait référence au réseau ({leaks}) : la version hors ligne ne doit rien charger.")
    if doc.count("</head>") != 1 or doc.count("</body>") != 1:
        fail(f"{a['name']} : structure HTML inattendue (</head> ou </body> absents ou multiples).")
    d = OUT / slug
    d.mkdir(parents=True)

    # 1. Le fichier à télécharger : la source telle quelle.
    (d / f"{slug}-hors-ligne.html").write_text(doc, encoding="utf-8")

    # 2. La page installable : manifeste, icônes, enregistrement du service worker (sans effet en file://).
    head = (f'<meta name="theme-color" content="{a["theme"]}">\n'
            '<link rel="manifest" href="manifest.webmanifest">\n'
            '<link rel="icon" type="image/png" href="icon-192.png">\n'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n')
    reg = ('<script>if("serviceWorker"in navigator&&/^https?:$/.test(location.protocol))'
           'addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){})})</script>\n')
    # Titre et description pour les moteurs de recherche (page en ligne seulement, pas le fichier téléchargé).
    title = a.get("seo_title") or a["name"]
    head += seo_head(f"{slug}/", title, a.get("description") or a["pitch"], f"{slug}/icon-512.png")
    doc_seo = re.sub(r"<title>[^<]*</title>", lambda m: f"<title>{esc(title)}</title>", doc, count=1)
    page = doc_seo.replace("</head>", head + "</head>", 1).replace("</body>", reg + "</body>", 1)
    (d / "index.html").write_text(page, encoding="utf-8")

    icons = SRC / "icons" / slug
    for f in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"):
        if not (icons / f).exists():
            fail(f"icône manquante : {icons / f} (lancer tools/make-icons.py)")
        shutil.copy(icons / f, d / f)

    manifest = {
        "id": "./", "name": a["name"], "short_name": a["name"], "description": typo_text(a["pitch"]),
        "lang": "fr", "dir": "ltr", "start_url": "./", "scope": "./", "display": "standalone",
        "theme_color": a["theme"], "background_color": a["background"],
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    mtxt = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (d / "manifest.webmanifest").write_text(mtxt, encoding="utf-8")

    # 3. Le service worker. Le nom du cache contient une empreinte du contenu : toute modification de l’application
    #    produit un nouveau cache, l’ancien est supprimé à l’activation. Mise en cache d’abord, réseau en secours.
    h = hashlib.sha256((page + mtxt).encode()).hexdigest()[:10]
    sw = f"""/* Généré par build-site.py — ne pas modifier à la main. */
const PREFIX = 'petits-outils-{slug}-';
const CACHE = PREFIX + '{h}';
const FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png'];

self.addEventListener('install', e => {{
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(FILES.map(f => new Request(f, {{ cache: 'reload' }}))))
    .then(() => self.skipWaiting()));
}});

self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith(PREFIX) && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
}});

self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request, {{ ignoreSearch: true }}).then(r => r || fetch(e.request)));
}});
"""
    (d / "sw.js").write_text(sw, encoding="utf-8")
    return len(page) // 1024


# ---------- Pages ----------
def shell(title, desc, body, rel, path):
    t = esc(title)
    nav = (f'<a href="{rel}#outils">Les outils</a><a href="{rel}#hors-ligne">Sans Internet</a>'
           f'<a href="{rel}apropos/">À propos</a>')
    repo = (f'<a href="{html.escape(CONF["repo_url"])}">Code source</a>' if CONF.get("repo_url") else "")
    foot = " · ".join(x for x in [f'Licence MIT', f'<a href="{rel}apropos/">À propos et crédits</a>', repo] if x)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="theme-color" content="#213a86">
{seo_head(path, title, desc)}<link rel="icon" type="image/png" href="{rel}icon-192.png">
<link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">
<link rel="stylesheet" href="{rel}site.css">
</head>
<body>
<a class="skip" href="#main">Aller au contenu</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="{rel or './'}"><img src="{rel}icon-192.png" alt="" width="40" height="40"><span>{esc(CONF["title"])}</span></a>
<nav aria-label="Navigation principale">{nav}</nav>
</div></header>
<main id="main">
<div class="wrap">
{body}
</div>
</main>
<footer><div class="wrap">
<p>Fait par {esc(CONF["author"])} · {foot.replace(" · ", " · ")}</p>
<p>© {CONF["year"]}</p>
</div></footer>
</body>
</html>
"""


def card(a):
    slug, live = a["slug"], a["status"] == "essai"
    shot = SRC / "img" / f"{slug}.webp"
    if live and shot.exists():
        visual = f'<div class="thumb"><img src="img/{slug}.webp" alt="{esc(a["alt"])}" width="1280" height="800" loading="lazy"></div>'
    else:
        visual = f'<div class="thumb icon" style="background:{a["background"]}"><img src="img/{slug}-icone.png" alt="" width="112" height="112"></div>'
    badge = '<span class="badge">À l’essai</span>' if live else '<span class="badge soon">Bientôt</span>'
    if live:
        actions = (f'<a class="btn" href="{slug}/">Ouvrir {esc(a["name"])}</a>'
                   f'<a class="btn alt" href="{slug}/{slug}-hors-ligne.html" download>Télécharger le fichier</a>')
    else:
        actions = '<p class="muted">Cet outil sera disponible prochainement.</p>'
    return f"""    <article class="card" id="{slug}">
      {visual}
      <div class="card-body">
        <div class="card-head"><h3>{esc(a["name"])}</h3>{badge}</div>
        <p class="pitch">{esc(a["pitch"])}</p>
        <p>{esc(a["details"])}</p>
        <p class="for">{esc(a["for"])}</p>
        <div class="actions">{actions}</div>
      </div>
    </article>"""


def fill(tpl, values):
    for k, v in values.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{\w+\}\}", tpl)
    if left:
        fail(f"marqueurs non remplacés : {left}")
    return tpl


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("")
    apps = CONF["apps"]
    sizes = {a["name"]: build_app(a) for a in apps if a["status"] == "essai"}

    # Fichiers communs
    shutil.copy(SRC / "site.css", OUT / "site.css")
    shutil.copytree(SRC / "fonts", OUT / "fonts")
    for f in ("icon-192.png", "icon-512.png", "apple-touch-icon.png"):
        shutil.copy(SRC / "icons" / "site" / f, OUT / f)
    (OUT / "img").mkdir()
    for a in apps:
        shot = SRC / "img" / f"{a['slug']}.webp"
        if a["status"] == "essai" and shot.exists():
            shutil.copy(shot, OUT / "img" / shot.name)
        else:
            shutil.copy(SRC / "icons" / a["slug"] / "icon-192.png", OUT / "img" / f"{a['slug']}-icone.png")
    shutil.copytree(ROOT / "licences", OUT / "licences")
    shutil.copy(REPO / "LICENSE", OUT / "licences" / "LICENSE.txt")

    # Accueil
    # Contact : les Issues du dépôt (formulaire dans .github/ISSUE_TEMPLATE). Une adresse e-mail reste possible via « contact ».
    if CONF.get("repo_url"):
        issues = CONF["repo_url"].rstrip("/") + "/issues/new/choose"
        contact = (
            '  <p class="prose">Pour signaler un problème ou proposer une idée, ouvrez un ticket sur GitHub. '
            'Cela demande un compte GitHub gratuit. Merci de n’y mettre aucun nom, prénom ni autre information '
            'personnelle : la page est publique.</p>\n'
            f'  <p><a class="btn" href="{html.escape(issues)}">Signaler un problème ou proposer une idée</a></p>')
    elif CONF.get("contact"):
        c = CONF["contact"]
        href = c if re.match(r"https?:|mailto:", c) else "mailto:" + c
        label = re.sub(r"^(mailto:|https?://)", "", c)
        contact = f'  <p class="prose">Écrivez-moi : <a href="{html.escape(href)}">{html.escape(label)}</a>.</p>'
    else:
        contact = ""
        WARN.append("ni « repo_url » ni « contact » dans site.json : la page d’accueil n’indique aucun moyen de te joindre.")
    index = fill((SRC / "index.body.html").read_text(encoding="utf-8"),
                 {"TITLE": esc(CONF["title"]), "CARDS": "\n".join(card(a) for a in apps), "CONTACT": contact})
    (OUT / "index.html").write_text(
        typo_html(shell(CONF.get("seo_title") or CONF["title"],
                        CONF.get("description") or CONF["tagline"] + " Outils d’apprentissage faits par un enseignant.",
                        index, "", "")),
        encoding="utf-8")

    # À propos
    claude = ('  <p class="prose">Ces outils ont été développés avec l’aide de Claude, l’assistant d’Anthropic.</p>'
              if CONF.get("credit_claude") else "")
    if CONF.get("repo_url"):
        source = f'  <p class="prose">Le code source est public : <a href="{html.escape(CONF["repo_url"])}">{html.escape(CONF["repo_url"])}</a>.</p>'
    else:
        source = ""
        WARN.append("« repo_url » est vide dans site.json : aucun lien vers le code source.")
    ap = fill((SRC / "apropos.body.html").read_text(encoding="utf-8"),
              {"AUTHOR": esc(CONF["author"]), "CLAUDE": claude, "SOURCE": source})
    (OUT / "apropos").mkdir()
    (OUT / "apropos" / "index.html").write_text(
        typo_html(shell("À propos et crédits — " + CONF["title"], "Qui a fait ces outils, licence MIT et composants utilisés.", ap, "../", "apropos/")),
        encoding="utf-8")

    # Moteurs de recherche : plan du site et robots.txt (URL absolues, donc seulement avec « site_url »)
    if SITE_URL:
        pages = ["", "apropos/"] + [a["slug"] + "/" for a in apps if a["status"] == "essai"]
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{SITE_URL}{u}</loc></url>\n" for u in pages) + "</urlset>\n", encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    else:
        WARN.append("« site_url » est vide dans site.json : ni URL canonique ni sitemap.xml pour les moteurs de recherche.")

    # Contrôles : typographie des pages, absence de réseau externe (hors liens <a> et licences)
    errs = []
    for p in ("index.html", "apropos/index.html"):
        errs += lint(p, (OUT / p).read_text(encoding="utf-8"))
        for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', (OUT / p).read_text(encoding="utf-8")):
            if re.search(r"<(?:img|link(?![^>]*rel=\"canonical\")|script)\b[^>]*" + re.escape(u), (OUT / p).read_text(encoding="utf-8")):
                errs.append(f"{p} : ressource externe chargée : {u}")
    if errs:
        print("Problèmes de typographie ou de ressources :", *errs, sep="\n  - ")
        sys.exit(1)

    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) // 1024
    print("OK : site/public/ —", ", ".join(f"{n} ({k} Ko)" for n, k in sizes.items()), f"— total {total} Ko")
    for w in WARN:
        print("ATTENTION :", w)


if __name__ == "__main__":
    main()

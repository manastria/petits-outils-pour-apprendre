#!/usr/bin/env python3
"""Génère les captures d’écran des cartes de la page d’accueil (versionnées dans src/img/).
Prérequis : `pip install playwright pillow` + Chromium. Chaque application a son scénario dans SHOTS.
Usage : python3 tools/make-shots.py [slug …]"""
import io, json, pathlib, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))

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
    top = clip(pg, "(()=>{const h=document.querySelector('header').getBoundingClientRect();return [h.x,0,h.width,h.bottom+12]})()")
    sheet = clip(pg, box + "(document.querySelector('.sheet'))")
    ed = clip(pg, "(()=>{const c=document.querySelector('#src').closest('.card').getBoundingClientRect();const e=document.querySelector('#ed').getBoundingClientRect();return [c.x,c.y,c.width,e.bottom-c.y+14]})()")
    return stack([top, sheet, ed], (234, 238, 246))


# Élève fictif : dix jours d’entraînement simulés avec le vrai moteur de l’application (graine fixe).
SIMULE = """(() => {
  let seed = 42; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  const S = TE.defaults(); const know = {};
  const today = () => { const d = new Date(); return Math.floor((d.getTime() - d.getTimezoneOffset() * 60000) / 86400000) };
  for (const k of TE.factKeys(S)) { const [a, b] = TE.parseF(k);
    const hard = [6, 7, 8].includes(a) || [6, 7, 8].includes(b), easy = [2, 5, 10].includes(a) || [2, 5, 10].includes(b);
    know[k] = easy ? .95 : hard ? .3 : .65; }
  const prod = p => Math.min(...TE.sols(S, p).map(([a, b]) => know['f' + a + 'x' + b])) * .9;
  const T0 = today() - 9;
  for (let d = 0; d < 10; d++) { const T = T0 + d, s = TE.newSession(S, null);
    TE.touchStreak(S, T); let guard = 0;
    while (!TE.finished(s) && ++guard < 200) {
      const k = TE.pick(S, s, T, rnd); s.last = k;
      const pk = k[0] === 'f' ? know[k] : prod(+k.slice(1)); let out, t;
      if (rnd() < pk) { out = 'ok'; t = pk > .8 ? 2 + rnd() * 2 : 4 + rnd() * 8 } else if (rnd() < .4) { out = 'ok2'; t = 9 } else { out = 'fail'; t = 0 }
      TE.grade(S, s, k, out, t, T);
      if (k[0] === 'f') know[k] = Math.min(.97, know[k] + (out === 'ok' ? .04 : .12)); }
  }
  TE.newBadges(S); localStorage.setItem('tables-en-tete-v1', JSON.stringify(S));
})()"""

def tables(pg):
    pg.evaluate(SIMULE); pg.reload(); pg.wait_for_timeout(500)
    box = "(e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height+window.scrollY*0]})"
    pg.evaluate("window.scrollTo(0,0)")
    top = clip(pg, "(()=>{const r=document.querySelector('#streak').getBoundingClientRect();const h=document.querySelector('header').getBoundingClientRect();return [h.x,0,h.width,r.bottom+12]})()")
    pyth = clip(pg, box + "(document.querySelector('#pyth').closest('.card'))")
    return stack([top, pyth], (241, 243, 248))

# slug -> (scénario qui renvoie une image PIL, largeur, hauteur de la fenêtre)
SHOTS = {"cahier-latex": (cahier, 1080, 1100), "tables-en-tete": (tables, 1000, 1500)}

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

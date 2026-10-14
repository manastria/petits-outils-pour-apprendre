#!/usr/bin/env python3
"""Applique la typographie française (mêmes règles que build-site.py) à des fichiers texte, en place.
Usage : python3 tools/typo.py fichier [fichier …]
À réserver aux textes de prose (formulaires d’Issue, README…) : ne pas lancer sur du code."""
import importlib.util, pathlib, sys

spec = importlib.util.spec_from_file_location("build_site", pathlib.Path(__file__).resolve().parent.parent / "build-site.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

for f in sys.argv[1:]:
    p = pathlib.Path(f)
    old = p.read_text(encoding="utf-8")
    new = mod.typo_text(old)
    if new != old:
        p.write_text(new, encoding="utf-8")
    print(("corrigé : " if new != old else "inchangé : ") + f)

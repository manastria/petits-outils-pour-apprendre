#!/usr/bin/env python3
"""Construit tout : chaque application (apps/*), puis le site (site/public/).

Usage :
    python3 build.py              construit tout (npm n’est lancé que si node_modules manque)
    python3 build.py --install    force l’installation des dépendances npm (ce que fait la publication)

Prérequis : Python 3.9+, Node.js et npm. La publication sur GitHub passe par le même script
(.github/workflows/publier.yml)."""
import pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
FORCE = "--install" in sys.argv


def run(cmd, cwd):
    print(f"\n$ ({cwd.relative_to(ROOT) if cwd != ROOT else '.'}) {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    npm = shutil.which("npm")
    for app in sorted(p for p in (ROOT / "apps").iterdir() if (p / "build.py").exists()):
        if (app / "package.json").exists() and (FORCE or not (app / "node_modules").exists()):
            if not npm:
                sys.exit("npm introuvable : installer Node.js (https://nodejs.org).")
            run([npm, "ci" if (app / "package-lock.json").exists() else "install"], app)
        run([sys.executable, "build.py"], app)
    run([sys.executable, "build-site.py"], ROOT / "site")


if __name__ == "__main__":
    main()

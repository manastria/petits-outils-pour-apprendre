# Petits outils pour apprendre — notes pour Claude Code

Dépôt unique (public) de petites applications web d’apprentissage, **gratuites, sans compte, fonctionnant sans Internet**, et du site qui les présente aux parents. L’auteur est un enseignant qui développe des outils pédagogiques, parfois pensés pour les élèves dys. Lire le `CLAUDE.md` du dossier concerné avant de modifier quoi que ce soit.

| Dossier | Contenu | Notes |
|---|---|---|
| `apps/cahier-latex/` | Éditeur LaTeX/KaTeX avec aperçu et aide aux accolades | `apps/cahier-latex/CLAUDE.md` |
| `apps/tables-en-tete/` | Tables de multiplication par répétition espacée | `apps/tables-en-tete/CLAUDE.md` |
| `site/` | Page d’accueil, « À propos », construction du site, tests du site | `site/CLAUDE.md` |
| `build.py` | Construit les applications puis le site | |
| `.github/` | Publication (GitHub Actions → Pages), formulaire d’Issues | |

## Règles communes

- **Le dépôt est public : ne jamais y écrire d’information personnelle.** Pas de prénom d’élève, de diagnostic, de lien familial, de classe, d’établissement ni d’adresse e-mail, ni dans le code, ni dans les commentaires, ni dans les `CLAUDE.md`, ni dans les messages de commit. Décrire le public de façon générale (« élèves de collège », « élèves dys »).
- **Hors ligne d’abord** : chaque application est un seul fichier HTML autonome, sans aucune requête réseau (polices et bibliothèques embarquées). Les scripts de construction vérifient l’absence d’URL externe et échouent sinon.
- **Rien de généré n’est versionné** (`dist/`, `site/public/`, `node_modules/`). Ne jamais modifier un fichier généré : modifier la source puis relancer `python3 build.py`.
- **Interface en français**, ton simple et encourageant, jamais punitif.
- **Typographie française** : apostrophe `’`, `« »` avec espace fine insécable (U+202F) à l’intérieur, espace fine insécable avant `;` `?` `!`. Les pages du site sont corrigées automatiquement par `site/build-site.py` ; dans les applications, c’est à écrire correctement à la main.
- **Lisibilité** (public dys) : police Atkinson Hyperlegible, grandes tailles, messages courts et concrets.
- **Scripts Python et Windows** : toujours `read_text(encoding="utf-8")` / `write_text(…, encoding="utf-8")`. Sans cela, Python sous Windows lit en cp1252 et la construction échoue sur les caractères accentués.
- Chaque application garde ses clés `localStorage` **préfixées par son nom** (le site partage une seule origine pour tous les outils).

## Construire et vérifier

```bash
python3 build.py                              # applications puis site
node apps/tables-en-tete/test/simulate.js     # moteur de Tables en tête
python3 site/test/site_test.py                # site complet, dont le rechargement réseau coupé (Playwright)
```

## Publication

`push` sur la branche principale (`main` ou `master`) → `.github/workflows/publier.yml` (test du moteur, `python3 build.py --install`, publication de `site/public/`). Source de Pages réglée sur « GitHub Actions ». Les versions des actions sont suivies par Dependabot (`.github/dependabot.yml`).

## Contact des utilisateurs

Uniquement par les Issues du dépôt (formulaire `.github/ISSUE_TEMPLATE/probleme.yml`, tickets vierges désactivés). Le formulaire demande de ne mettre aucune donnée personnelle ; en cas de ticket qui en contient, le modifier ou le supprimer. Ajouter l’outil concerné dans la liste déroulante du formulaire quand on crée une application.

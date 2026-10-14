# Petits outils pour apprendre

Petites applications web d’apprentissage, **gratuites, sans compte, qui fonctionnent sans Internet**. Faites par un enseignant qui développe des outils pédagogiques, parfois pensés pour les élèves dys.

**Site : <https://manastria.github.io/petits-outils-pour-apprendre/>** (page d’accueil pensée pour les parents, avec les outils à ouvrir ou à télécharger).

| Outil | Dossier | Rôle |
|---|---|---|
| Maths au clavier | [`apps/cahier-latex`](apps/cahier-latex) | Saisie de formules de maths avec aperçu en direct |
| Tables en tête | [`apps/tables-en-tete`](apps/tables-en-tete) | Entraînement aux tables de multiplication (répétition espacée) |

Chaque outil est **un seul fichier HTML autonome** (polices et bibliothèques comprises, aucune requête réseau), ce qui permet de le copier sur une clé USB et de l’ouvrir d’un double-clic.

## Organisation du dépôt

```
.
├── apps/
│   ├── cahier-latex/      source, build.py, CLAUDE.md
│   └── tables-en-tete/    source, build.py, tests, CLAUDE.md
├── site/                  page d’accueil, « À propos », construction du site
├── .github/
│   ├── workflows/publier.yml    publication sur GitHub Pages
│   └── ISSUE_TEMPLATE/          formulaire de signalement
└── build.py               construit tout
```

Rien de généré n’est versionné : `dist/` (applications) et `site/public/` (site) sont produits par la construction.

## Construire en local

Prérequis : Python 3.9 ou plus, Node.js et npm.

```bash
python3 build.py
```

Le script installe les dépendances npm des applications si besoin, construit chaque application, puis assemble le site dans `site/public/`. Pour regarder le résultat, ouvrir `site/public/index.html`, ou servir le dossier avec `python3 -m http.server -d site/public` (le mode « installable » exige `http://localhost` ou HTTPS).

## Publier

### Sur GitHub Pages

À faire une seule fois : dans *Settings* → *Pages* → *Build and deployment*, choisir la source **GitHub Actions**.

Ensuite, chaque `push` sur la branche principale (`main` ou `master`) lance le workflow [`publier.yml`](.github/workflows/publier.yml), qui teste le moteur de *Tables en tête*, construit tout et publie. Le bouton *Run workflow* de l’onglet *Actions* relance la publication à la main. Si la construction échoue, le site déjà en ligne reste en place.

### Chez un autre hébergeur

Lancer `python3 build.py`, puis envoyer **le contenu** de `site/public/` (par SFTP, par exemple). Tous les liens sont relatifs : le site fonctionne à la racine d’un domaine comme dans un sous-dossier. L’hébergement doit servir en HTTPS pour que le mode « installable » fonctionne.

## Ajouter un outil

1. Créer `apps/<nom>/` avec un `build.py` qui produit `dist/<nom>-hors-ligne.html` (un seul fichier, sans requête réseau : la construction du site refuse sinon).
2. Ajouter une entrée dans [`site/site.json`](site/site.json) (statut `bientot` tant que l’outil n’est pas prêt, puis `essai`).
3. Ajouter son dessin dans `site/tools/make-icons.py` et son scénario de capture dans `site/tools/make-shots.py`, puis les lancer (ils demandent `pip install playwright pillow`).
4. Ajouter son option dans le formulaire [`probleme.yml`](.github/ISSUE_TEMPLATE/probleme.yml).

Détails dans [`site/CLAUDE.md`](site/CLAUDE.md).

## Vérifier

```bash
node apps/tables-en-tete/test/simulate.js    # moteur de répétition espacée
python3 site/test/site_test.py               # site : liens, hors ligne… (pip install playwright)
```

## Signaler un problème, proposer une idée

Ouvrir un ticket via l’onglet [*Issues*](../../issues/new/choose). Un compte GitHub gratuit est nécessaire. **La page est publique : n’y mettez aucune information personnelle**, ni nom, ni prénom, ni école, ni adresse e-mail.

## Licence

[MIT](LICENSE). Les composants embarqués ont leur propre licence : voir [`site/licences/`](site/licences/) et la page « À propos » du site.

# Site « Petits outils pour apprendre » — notes pour Claude Code

Site statique qui présente et héberge les applications du dossier `../apps/` : **Cahier LaTeX** et **Tables en tête**, et d’autres à venir. Public visé : des **parents non informaticiens** ; ce qu’ils voient doit se comprendre sans jargon. Règles communes du dépôt (public, pas de données personnelles, hors ligne d’abord, typographie) : voir `../CLAUDE.md`.

Statut actuel : **« à l’essai »**. Le ton est honnête et sans promesse ; l’assistance est « fournie telle quelle ». Contact **uniquement par les Issues** du dépôt (bouton de la section « À l’essai »).

## Fichiers

| Chemin | Rôle |
|---|---|
| `site.json` | **Configuration** : titre, auteur, `repo_url`, liste des applications (statut `essai` ou `bientot`). Un `contact` e-mail est possible mais non utilisé. |
| `build-site.py` | Génère `public/` (bibliothèque standard seulement). Lancé par `../build.py` après les applications. |
| `src/index.body.html`, `src/apropos.body.html` | Contenu des deux pages (marqueurs `{{…}}`). L’enveloppe (en-tête, pied, `<head>`) est dans `shell()` de `build-site.py`. |
| `src/site.css` | Feuille de style commune, mêmes jetons de couleur que les applications. |
| `src/fonts/`, `src/icons/<slug>/`, `src/img/` | Polices Atkinson, icônes PNG, captures WebP. **Versionnés** : produits une fois par `tools/`. |
| `tools/make-icons.py`, `tools/make-shots.py`, `tools/typo.py` | Icônes et captures (Playwright), typographie française d’un fichier de prose. |
| `test/site_test.py` | Test de bout en bout, dont le rechargement hors ligne. |
| `licences/` | Textes de licence des composants (KaTeX MIT, Atkinson OFL). Copiés dans `public/licences/`. La licence du projet est `../LICENSE`. |
| `public/` | **Généré, non versionné.** Publié par `.github/workflows/publier.yml`. |

Les applications sont lues dans `../apps/<slug>/dist/<slug>-hors-ligne.html` (`apps_dir` et `source` dans `site.json`) : les construire d’abord, ou lancer `python3 ../build.py`.

## Ce que fait `build-site.py` pour chaque application « essai »

- `public/<slug>/<slug>-hors-ligne.html` : le fichier source **tel quel** (le téléchargement).
- `public/<slug>/index.html` : le même document avec, en plus, `<link rel="manifest">`, icônes, `theme-color` et un petit script qui enregistre `sw.js` **seulement en http(s)** (donc sans effet quand on ouvre le fichier en `file://`).
- `manifest.webmanifest` et `sw.js` générés. Le **nom du cache contient une empreinte (SHA-256) du contenu** : toute modification de l’application change `sw.js`, le navigateur installe la nouvelle version et supprime l’ancienne. Stratégie : cache d’abord, réseau en secours.
- Le build **échoue** si l’application référence une URL réseau (hors `http://www.w3.org`) ou si la structure HTML est inattendue (`</head>` / `</body>` absents ou multiples).

Les applications ne sont **pas modifiées** par le site : tout ce qui concerne le mode installable est injecté à la construction.

## Ajouter ou activer une application

1. Entrée dans `site.json` (`bientot` : carte sans boutons, icône seule ; `essai` : boutons « Ouvrir » et « Télécharger », capture d’écran).
2. Dessin de l’icône dans `tools/make-icons.py`, scénario de capture dans `tools/make-shots.py` ; les lancer (`pip install playwright pillow`).
3. Option dans la liste déroulante de `../.github/ISSUE_TEMPLATE/probleme.yml`.
4. `python3 ../build.py` puis `python3 test/site_test.py`.

## Pièges à connaître

- **Liens relatifs uniquement** (jamais de `/` initial) : le site doit marcher sur `https://compte.github.io/depot/` comme à la racine d’un domaine ou dans un sous-dossier d’un autre hébergeur.
- **Même origine = même `localStorage`** : sur `compte.github.io`, tous les dépôts partagent l’origine. Les clés de chaque application doivent donc rester préfixées (`cahier-latex-*`, `tables-en-tete-v1`). La portée du service worker est limitée au dossier de l’application.
- **Pas de ressource externe** : ni Google Fonts, ni CDN, ni statistiques. L’accueil affirme « aucun service extérieur » ; `test/site_test.py` le vérifie. Si on en ajoute un, changer le texte de la section « Vos données ».
- Le mode installable exige HTTPS (ou `localhost`).
- Une page qui a déjà un service worker actif sert l’ancien contenu jusqu’à la visite suivante : c’est normal. Pour tester une mise à jour, recharger deux fois.
- Les fins de ligne Windows (`\r\n`) d’un fichier d’application sont normalisées en `\n` par le build.
- **Ne pas parler de l’élève ni d’un diagnostic** dans les pages publiques, et ne pas citer d’établissement : le dépôt et le site sont publics.

## Conventions

- **Interface en français, ton simple et encourageant**, pour des parents : pas de « PWA », « cache », « service worker » dans les pages.
- **Typographie** (règles du Lexique de l’Imprimerie nationale, appliquées par `typo_html()`) :
  - apostrophe typographique `’` ;
  - `;` `?` `!` précédés d’une **espace fine insécable** (U+202F) ;
  - `:` précédé d’une **espace insécable** (U+00A0) ;
  - guillemets `« »` avec U+202F à l’intérieur.
  Écrire le texte avec des espaces ordinaires dans les pages et dans `site.json` : le script corrige, puis `lint()` signale ce qu’il ne peut pas deviner (ponctuation collée au mot, apostrophe droite). Pour un fichier de prose hors pages (formulaire d’Issue, par exemple) : `python3 tools/typo.py fichier`. Les applications utilisent U+202F avant `:` : différence connue.
- **Lisibilité (public dys)** : texte sur fond uni (la bande « papier réglé » du haut est décorative), Atkinson Hyperlegible, 18 px, lignes ≤ 68 caractères, pas de texte justifié, cibles tactiles ≥ 48 px.
- Couleurs uniquement via les jetons de `:root`, avec les deux blocs sombres (`prefers-color-scheme` et `[data-theme="dark"]`) tenus à jour ensemble.

## Vérifier une modification

1. `python3 ../build.py` (doit afficher « OK » ; un « ATTENTION » signale un champ manquant dans `site.json`).
2. `python3 test/site_test.py --shots /tmp/captures` : liens, requêtes externes, service worker, rechargement réseau coupé, largeur téléphone.
3. Regarder les captures (clair, sombre, 390 px) : un seul défaut visible suffit à justifier un correctif.

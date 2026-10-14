# Maths au clavier (dossier et identifiants `cahier-latex`) — notes pour Claude Code

Éditeur LaTeX/KaTeX dans une seule page HTML, conçu pour les élèves de collège qui prennent leurs cours de maths à l’ordinateur, notamment ceux qui ont du mal à écrire à la main (dys). Les formules sont collées dans **Word**, et les élèves **n’ont pas toujours Internet à l’école** : la version hors ligne est la version principale, elle ne doit jamais faire de requête réseau.

Le mainteneur (un enseignant) reçoit les signalements de bugs ; l’utilisateur final est un élève de collège. Toute l’interface est en français.

Ce dossier fait partie du dépôt `petits-outils-pour-apprendre` (règles communes, dont l’interdiction de toute donnée personnelle : `../../CLAUDE.md`). `dist/` n’est pas versionné : `build.py` le produit, puis le site le reprend (`../../site/CLAUDE.md`).

## Fichiers

| Chemin | Rôle |
|---|---|
| `src/cahier-latex.src.html` | **Seule source à modifier.** Contient deux marqueurs de build : `/*KATEX_CSS*/` et la balise `<script src=…katex@0.16.11…>`. |
| `build.py` | Produit les deux versions dans `dist/` et vérifie la syntaxe JS. |
| `dist/cahier-latex-hors-ligne.html` | Fichier autonome (~760 Ko) : KaTeX JS + CSS + polices KaTeX + Atkinson Hyperlegible embarqués en base64. Document HTML complet. |
| `dist/cahier-latex.html` | Version « artifact claude.ai » : pas de `<!doctype>`/`<head>`/`<body>` (ajoutés par l’hébergeur), KaTeX JS via jsDelivr, polices texte via Google Fonts. |

Ne jamais éditer `dist/` à la main.

## Build

```bash
npm install          # katex 0.16.11 (version figée), @fontsource/atkinson-hyperlegible(-mono)
python3 build.py     # ou npm run build
```

`build.py` échoue si la version hors ligne contient une URL autre que `http://www.w3.org` (espaces de noms MathML/SVG). Si on ajoute une dépendance, elle doit être embarquée dans la version hors ligne. Garder la même version de KaTeX entre le CSS embarqué et le JS (CDN et embarqué).

**Alerte `npm audit`** (GHSA-cg87-wmx4-v546 et GHSA-238p-pmpm-9mq7) sur KaTeX 0.16.11 : elle concerne l’option `trust`, jamais activée ici (aucun `trust` dans la source), donc sans effet. Mettre KaTeX à jour (la version 0.16.47 corrige les deux) demande de changer la version dans `package.json`, dans `build.py` (`CDN_TAG`) et dans la balise `<script>` de la source, puis de reconstruire et de retester le rendu, les polices et la copie pour Word.

## Architecture du script (fin de `src/cahier-latex.src.html`)

Un seul IIFE, sans framework. Sections dans l’ordre :

- **Données** : `CMDS` (complétion après `\`), `PALETTE` (boutons), `EXAMPLES`, `ROLE` (nom des arguments : `frac` → numérateur/dénominateur…).
- **Snippets** : chaîne avec `|` = position du curseur, ex. `'\\dfrac{|}{}'`. C’est le **dernier** `|` qui compte (le tableau `array` en contient d’autres dans `{|c|c|c|}`). Si du texte est sélectionné, il est placé à la place du `|`.
- **`analyze(s)`** : un seul passage sur le texte → `depth[]`, `cls[]` (`cmd`, `op`, `cm`, `br`, `bad`, `br bad`), `match[]` (paires d’accolades), `unclosed`, `extra`, `pairs`. `\{`, `\}` et `\\` sont des commandes, pas des accolades. Un `\` seul en fin de texte est marqué `bad`.
- **`enclosing(s,A,p)`** : accolades ouvrantes contenant la position `p`, de l’extérieure vers l’intérieure.
- **`roleOf(s,A,o)`** : remonte depuis une `{` pour trouver la commande propriétaire et l’index d’argument (gère `^`, `_`, `[option]`).
- **`fr(raw)`** : traduit les messages `ParseError` de KaTeX (`e.rawMessage`). Liste de regex ordonnée, **la plus spécifique en premier**. Fallback = message anglais brut.
- **Boucle de rendu** : `schedule()` → `requestAnimationFrame(update)`. `update()` ne relance l’analyse, l’aperçu et la vérification que si le texte a changé ; le surlignage et le chemin sont recalculés à chaque mouvement du curseur.
- **Surlignage** : `<pre id="hl">` et `<textarea id="src">` superposés dans la même cellule de grille (`.ed`). Le texte du textarea est transparent ; le `pre` dessine les couleurs. C’est le `pre` qui donne la hauteur (d’où l’espace ajouté en fin de contenu).
- **Saisie** : `insertAt()` passe par `document.execCommand('insertText'|'delete')` pour **préserver l’annulation (Ctrl+Z)**, avec repli sur `setRangeText`.
- **Complétion** (`updatePopup`, `acceptPop`, `positionPop`) : positionnée grâce au marqueur `<span id="cm">` inséré dans le `pre` à la position du curseur.
- **Vérification** (`renderDiag`, `HINTS`) : accolades, erreur KaTeX, conseils avec bouton « Corriger » (virgule décimale `{,}`, `*`, `<=`, `°`, `/`).
- **Copier pour Word** : `katex.renderToString(…, {output:'mathml'})`, extraction de `<math>…</math>`, suppression de `<annotation>` et `<semantics>`. Word convertit le MathML collé en équation.
- **Stockage** : `localStorage` via `store` (toujours en try/catch). Clés : `cahier-latex-brouillon`, `cahier-latex-formules`, `cahier-latex-taille`. En `file://`, le stockage est lié au chemin du fichier.

## Pièges à connaître

- **Métriques identiques entre `pre` et `textarea`** : même police, taille, interligne, padding, `white-space`, `overflow-wrap`, `tab-size`, ligatures coupées. Dans les `span` du surlignage, **interdits** : gras, italique, padding, bordure, `letter-spacing` — tout ce qui change la largeur décale le curseur. Utiliser seulement couleur, fond, `box-shadow`, `text-decoration`.
- **Clavier AZERTY** : `{` = AltGr+4, envoyé avec `ctrlKey` et `altKey` vrais sous Windows. Ne pas exclure `ctrlKey` dans le test de `e.key === '{'`. `^` est une touche morte.
- **Tab** : capturé dans l’éditeur (case vide `{}` suivante, sinon sortie de l’accolade). `Échap` puis `Tab` permet de quitter l’éditeur (pas de piège clavier) ; ne pas casser ce comportement.
- **Accessibilité dys** : police Atkinson Hyperlegible, taille réglable (A−/A+), messages courts et concrets. Ne pas réduire les tailles ni ajouter de texte en majuscules longues.

## Historique des bugs corrigés

1. Valider `\fr` dans la complétion donnait `\frac{\fr}{}` : `insertSnippet` prenait le préfixe tapé pour une sélection à envelopper. Corrigé avec le paramètre `noWrap` passé par `acceptPop`.
2. « Unexpected character: '\' » non traduit : provoqué par un `\` seul en fin de formule (souvent après avoir fermé la liste avec Échap). Message traduit et `\` final encadré en rouge.
3. Le bandeau d’erreur sous l’aperçu restait affiché une fois la formule corrigée : `.perr{display:flex}` l’emportait sur l’attribut `hidden`. Corrigé par la règle globale `[hidden]{display:none!important}`, à garder.

## Conventions

- **Typographie française stricte** dans tous les textes de l’interface : apostrophe `’`, guillemets `« »`, espace fine insécable U+202F avant `;` `:` `?` `!` et à l’intérieur des guillemets. En JS, utiliser la constante `NB` ; en HTML, `&#8239;`.
- Couleurs uniquement via les jetons CSS de `:root`, avec les deux blocs sombres (`prefers-color-scheme` et `[data-theme="dark"]`) tenus à jour ensemble.
- Pas de bibliothèque supplémentaire sans l’embarquer dans la version hors ligne.

## Vérifier une modification

1. `python3 build.py` (inclut `node --check`).
2. Erreurs KaTeX : tester `\frac{1}{2`, `x}`, `\fracc{1}{2}`, `x^2^3`, `a & b`, `\sqrt`, `\left( x`, `A = \dfrac{1}{2}\` — chacune doit afficher un message français.
3. Ouvrir `dist/cahier-latex-hors-ligne.html` en `file://` **réseau coupé** : l’aperçu, les polices et la complétion doivent fonctionner.
4. Saisie : `{` ferme l’accolade, Retour arrière dans `{}` supprime les deux, `\fr` + Tab donne `\frac{}{}`, Tab passe à la case vide suivante, Ctrl+Z annule une insertion.
5. Mode sombre et largeur téléphone (~400 px) : pas de défilement horizontal de la page.

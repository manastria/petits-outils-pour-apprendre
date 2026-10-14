# Tables en tête — notes pour Claude Code

Application d’entraînement aux tables de multiplication, en une seule page HTML, pour des élèves de primaire et de collège qui ont oublié leurs tables ou ne les ont jamais bien fixées. Principe inspiré d’Anki : on insiste sur les opérations **inconnues ou lentes à restituer**. L’élève **n’a pas toujours Internet à l’école** : la version hors ligne est la version principale et ne doit faire aucune requête réseau.

Le mainteneur (un enseignant) reçoit les signalements de bugs. Toute l’interface est en français, avec un ton encourageant et jamais punitif.

Ce dossier fait partie du dépôt `petits-outils-pour-apprendre` (règles communes, dont l’interdiction de toute donnée personnelle : `../../CLAUDE.md`). `dist/` n’est pas versionné : `build.py` le produit, puis le site le reprend (`../../site/CLAUDE.md`).

## Fichiers

| Chemin | Rôle |
|---|---|
| `src/tables-en-tete.src.html` | **Seule source à modifier.** Marqueur de build `/*FONTS*/`. |
| `build.py` | Embarque la police, produit les deux versions dans `dist/`, vérifie la syntaxe JS et l’absence d’URL réseau. |
| `test/simulate.js` | Simule un élève sur 10 jours avec le vrai moteur et vérifie « cash, carré, duo » (propositions valides, effet sur les cartes, rythme des défis) (extrait entre `/*ENGINE_START*/` et `/*ENGINE_END*/`). Code de sortie non nul si boucle infinie ou séance « table de 7 » hors sujet. |
| `dist/tables-en-tete-hors-ligne.html` | Document HTML complet et autonome (~85 Ko). |
| `dist/tables-en-tete.html` | Version « artifact claude.ai » : sans `<!doctype>`/`<head>`/`<body>` (ajoutés par l’hébergeur). |

## Commandes

```bash
npm install          # @fontsource/atkinson-hyperlegible
python3 build.py     # ou npm run build
node test/simulate.js
```

## Architecture

Deux IIFE dans le `<script>` :

1. **`TE`, le moteur** (pur, sans DOM, testable dans Node). Toutes les fonctions reçoivent l’état `S` en paramètre.
2. **L’interface** : écrans `#home`, `#play`, `#end` affichés avec l’attribut `hidden`.

### Modèle de données (`localStorage`, clé `tables-en-tete-v1`)

```js
S = { v:1, xp, streak:{last,n}, badges:['t7',…],
      settings:{ tables:[2..10], mode:'mix'|'direct'|'reverse', n:20, fast:4, slow:10, newMax:10 },
      cards:{ 'f7x8':{l,due,n,ok,ko,t}, 'r56':{…} } }
```

- **Cartes directes** `f{a}x{b}` avec `a ≤ b` : 7 × 8 et 8 × 7 sont la même carte, présentée dans un sens tiré au hasard.
- **Cartes inversées** `r{p}` : « Quelle multiplication donne p ? ». Toute décomposition valide est acceptée (24 = 3 × 8 = 4 × 6).
- **Domaine des facteurs** : 2 à 10, ou 1 à 10 si la table de 1 est cochée. Une carte existe si au moins un facteur est dans une table cochée.
- `l` est le niveau : −1 = jamais vue, 0 à 6 ensuite. `due` est un numéro de jour local (`today()`), intervalles `INT = [0,1,2,4,7,14,30]` jours. `t` est le temps moyen (moyenne glissante, plafonné à 30 s).
- La table de Pythagore de l’accueil n’affiche que le triangle `a ≤ b` (une case par carte directe). Les cases hors des tables cochées sont en pointillés.
- Couleurs de la table de Pythagore : −1 gris, 0 rouge, 1–2 orange, 3 jaune, 4–5 vert clair (« sue »), 6 vert (« maîtrisée »). Le pourcentage affiché = cartes directes de niveau ≥ 4.

### Notation (`TE.grade`)

Issues : `ok` (juste du premier coup), `ok2` (juste après une erreur), `fail` (réponse affichée après 2 erreurs ou « Je ne sais pas »). La vitesse compare `t` aux seuils réglables (×1,5 pour les cartes inversées) : `fast`, `slow`, `vslow`.

- Nouvelle carte : rapide → niveau 3 (déjà sue), hésitante → 1, très lente → 0 et revient dans la séance.
- Carte connue : rapide → +1 ; hésitante → niveau conservé, intervalle divisé par 2 ; très lente → −1 et revient.
- `ok2` → −2 ; `fail` → 0. Les deux reviennent dans la séance (file `s.learn`, délai en nombre de questions).
- Une carte revue dans la même séance ne monte pas au-delà du niveau 1 (pas de gain artificiel).
- Une carte est remise dans la file au plus 4 fois par séance.

### Choix de la question suivante (`TE.pick`)

Ordre : carte de la file d’apprentissage arrivée à échéance → cartes dues (les plus faibles et les plus lentes d’abord) → nouvelles cartes (limite `newMax`, sauf en entraînement sur une table) → cartes connues non vues dans la séance → nouvelles au-delà de la limite → cartes pas encore réussies rapidement → reste. Jamais deux fois la même carte de suite. La séance dure `n` questions, prolongée de 8 au plus pour vider la file.

En mode `mix`, une carte inversée n’apparaît que lorsque toutes ses décompositions directes sont au niveau ≥ 2.

### Types de séance (`settings.style`, choisi sur l’accueil)

- **Classique** (`classic`) : saisie de la réponse, comme décrit plus haut.
- **Avec défis** (`mix`) : une manche « cash, carré, duo » à la 5e ou 6e question, puis toutes les 5 ou 6 questions (`TE.ccdTurn`, compteur `s.nextC`).
- **Jour calme** (`calm`) : toutes les questions en « cash, carré, duo », pour les jours de fatigue.

Déroulé d’une manche : l’enfant choisit **Cash** (il tape la réponse, jusqu’à 15 points), **Carré** (4 propositions, 6 points) ou **Duo** (2 propositions, 3 points). Cash raté ou carré raté → seconde chance en duo (2 points). Duo raté → la réponse s’affiche, bouton « Continuer ». Touches 1–4 ou A–D pour choisir une proposition.

Effet sur la répétition espacée (`TE.gradeChoice`), volontairement faible :

- **Cash juste** = vraie réponse : `TE.grade` normal avec ×1,5 sur les points.
- **Carré ou duo justes** : ni le niveau ni la date de révision ne changent (seuls `n`, `ok` et `mc` augmentent).
- **Toute erreur** (cash raté, carré raté, duo raté) : −1 niveau, révision le jour même, retour dans la séance.

Les propositions viennent de `TE.choices` : d’abord les voisins dans la table (pour 7 × 8 : 49, 63, 48, 64), puis des produits proches, pour travailler les confusions classiques. En inversé, les propositions sont des multiplications, une seule a le bon produit. `TE.duoOf` garde la bonne réponse et une mauvaise au hasard (jamais celle déjà écartée).

### Gamification

Points : rapide 10, hésitant 7, très lent 5, après erreur 3, échec 1. Bonus de série à partir de 3 bonnes réponses d’affilée. Niveau du joueur : `levelOf(xp)` (paliers de 100, 200, 300… points), avec un titre. Série de jours (`streak`). Badge « Table de n acquise » quand toutes ses cartes sont au niveau ≥ 4. Bilan : 1 à 3 étoiles selon le taux de réussite du premier coup (≥ 70 %, ≥ 90 %).

### Ne jamais bloquer l’enfant

Première erreur : message, éventuelle confusion (« 54, c’est 6 × 9 ») et indice (`TE.hint` : double, moitié de ×10, ×10 − n, voisin + n). Deuxième erreur : la réponse s’affiche ; en direct il la recopie pour continuer, en inversé un bouton « Continuer ».

## Pièges à connaître

- Garder la règle `[hidden]{display:none!important}` : sans elle, les écrans (en `display:flex`) restent visibles en même temps dans la version hors ligne.
- `Entrée` dans un champ appelle `submit()` puis `stopPropagation()` ; le gestionnaire global ignore les boutons. Sinon une seule pression valide **et** passe la correction.
- Les touches du pavé numérique font `preventDefault()` au `mousedown` pour garder le focus dans le champ.
- Champ inversé : passage automatique au second nombre après un chiffre, sauf `1` (début possible de 10).
- Le `localStorage` d’un fichier ouvert en `file://` dépend du chemin : déplacer le fichier perd la progression. D’où la sauvegarde par code (copier / coller) dans les réglages.
- Le moteur `TE` doit rester sans DOM pour que `test/simulate.js` fonctionne.

## Conventions

- **Typographie française stricte** : apostrophe `’`, guillemets `« »`, espace fine insécable U+202F avant `;` `:` `?` `!` (constante `NB` en JS, `&#8239;` en HTML).
- Couleurs uniquement via les jetons de `:root`, blocs sombres tenus à jour ensemble.
- Police Atkinson Hyperlegible (conçue pour la lisibilité), grands chiffres, pas de compte à rebours visible : le temps est mesuré sans mettre de pression.

## Vérifier une modification

1. `python3 build.py` puis `node test/simulate.js`.
2. Ouvrir `dist/tables-en-tete-hors-ligne.html` réseau coupé : faire une séance avec des réponses justes, une erreur puis juste, deux erreurs (recopie), « Je ne sais pas », puis une séance en mode inversé, une séance « Avec défis » (cash, carré raté puis duo, duo raté) et une séance « Jour calme ».
3. Vérifier qu’un seul écran est visible à la fois, le mode sombre et la largeur téléphone (~400 px).

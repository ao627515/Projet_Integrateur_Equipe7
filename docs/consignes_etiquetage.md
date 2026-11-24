# Consignes d'étiquetage du jeu d'évaluation

**Rédaction :** TAPSOBA Faridatou (Responsable données et qualité) | **Validation :** COMPAORE Alexis Awossonoyi (Chef de projet et référent éthique) | **Relecture juridique :** SOULAMA Grace Hope (Juriste, Hakili Lab)  
**Documents associés :** `protocole_evaluation.md`, `plan_projet.md`

Ce guide fixe les règles d'étiquetage de notre jeu d'évaluation ciblant **270 questions** (seuil minimal acceptable d'environ **180 questions** : 150 dans le champ et 30 hors champ) portant sur la **loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso** (441 articles, promulguée par décret n° 2026-0613/PF du **25 mai 2026**, publiée au Journal Officiel Spécial N°23 du **29 mai 2026**). L'objectif de 270 questions réunit **200 questions dans le champ**, **50 questions hors champ** et **20 questions en zone de doute**, dont **`206` à l'aveugle (`76,3 % ≥ 75 %`)**, **`64` `equipe` (`23,7 %`)**, **`30` à renvoi externe (`15 %` du champ)** et **≥ 38 % (`40 %` cible) de questions multi-articles**.

Une fois **100 % des 270 fiches validées** (`statut_relecture_juriste == "valide"`) par `SOULAMA Grace Hope`, le jeu est découpé une seule fois en **70 % Validation (189) / 30 % Test (81)**, stratifié sur `(strate, origine)` et **groupé par `famille_id`** (l'identifiant qui rassemble les reformulations d'un même besoin juridique afin de ne pas les séparer entre Validation et Test), avec une graine fixe `random_state = 42`, puis enregistré dans `data/processed/validation.json` et `data/processed/test.json` (`Test` reste verrouillé jusqu'à l'évaluation finale).

---

## 1. Règle d'attribution des articles : `article_principal` et `articles_complementaires`

Une question de droit du travail mobilise souvent plusieurs articles. Pour chaque question située dans le champ du Code (`statut_champ = dans_le_champ`), l'étiquetage distingue deux niveaux de références, avec au maximum **4 articles pertinents attendus** (plafond absolu `5`) et chaque article complémentaire justifié par son `role` (`condition`, `forme`, `exception`, `sanction`, `renvoi`, `definition`, `procedure`) :

| Champ d'étiquetage | Définition et règle de choix | Exemples concrets (Loi n° 013-2026/ALP) |
| :--- | :--- | :--- |
| **`article_principal`** *(1 seul article obligatoire)* | L'article qui contient la règle de droit répondant directement à la question posée (le chiffre, le délai, l'interdiction ou le droit principal). | Durée de l'essai d'un cadre : **Art. 49**.<br>Préavis de rupture d'un CDI : **Art. 76**.<br>Plafond de renouvellement d'un CDD : **Art. 59**. |
| **`articles_complementaires`** *(0 à 3 articles, max 4, chacun avec son `role`)* | Les articles indispensables pour éviter une réponse incomplète ou trompeuse : condition de forme (exigence d'un écrit), procédure, définition préalable, sanction ou exceptions légales à la règle principale. | Pour l'essai (Art. 49) : **Art. 48** (`forme` : écrit obligatoire sinon CDI) et **Art. 51** (`sanction` : requalification).<br>Pour le préavis (Art. 76) : **Art. 75** (`forme` : notification écrite et motif).<br>Pour le CDD (Art. 59) : **Art. 60** (`exception` au plafond de 2 renouvellements). |

**Lien avec les métriques de recherche (détaillées dans `protocole_evaluation.md`) :**
1. **`Succès@5`** mesure la part des questions où l'`article_principal` figure parmi les 5 premiers articles retournés ;
2. **`Rappel@5`** mesure la proportion moyenne de l'ensemble $R_i = \{\text{article\_principal}\} \cup \text{articles\_complementaires}$ retrouvée dans les 5 premiers résultats ;
3. Les deux métriques sont analysées ensemble via une grille à 6 cas croisant `Succès@5` et deux seuils de `Rappel@5` (`0,40` et `0,80`), où l'absence de l'article principal (`Succès@5 = 0`) bloque systématiquement l'acceptation.

---

## 2. Classement `statut_champ`, `renvoi_externe`, `strate` et `comportement_attendu`

Le classement repose sur deux attributs combinés dans `strate` et associés au `comportement_attendu` :
- `statut_champ` : **`dans_le_champ`**, **`hors_champ`** ou **`doute`** ;
- `renvoi_externe` : **`non`** ou **`oui`** (pour `dans_le_champ`), et **`na`** (pour `hors_champ` et `doute`).

| `strate` (`statut_champ` / `renvoi_externe`) | Quota (`270`) | Critère juridique de classement | Exemples et cas limites tranchés | `comportement_attendu` |
| :--- | :---: | :--- | :--- | :--- |
| **`dans_le_champ__sans_renvoi`** (`dans_le_champ` / `non`) | **170** *(127 aveugle / 43 equipe)* | La question trouve une réponse juridique complète et directe (affirmative, négative ou d'exclusion) dans un ou plusieurs des 441 articles de la Loi n° 013-2026/ALP. | « Combien de fois peut-on renouveler un CDD ? » (Art. 59).<br>**Cas limite tranché :** « Je suis fonctionnaire de l'État, le Code s'applique-t-il à moi ? » relève de **`dans_le_champ` / `non`** (Art. 2) ; l'abrogation de la loi de 2008 relève de l'Art. 440. | `repondre` : citer les articles utiles et expliquer la règle sans extrapoler. |
| **`dans_le_champ__renvoi`** (`dans_le_champ` / `oui`) | **30** *(23 aveugle / 7 equipe ; 15 % du champ)* | Un article pose le principe du droit ou de l'obligation, mais renvoie à une convention collective, un décret ou un arrêté (hors corpus) pour le taux, montant ou modalité. | Indemnité de fin de CDD : Art. 71 (conventions collectives).<br>Indemnité de licenciement : Art. 81 (conventions collectives / textes réglementaires).<br>Taux des heures supplémentaires : Art. 155 et 156 (voie réglementaire). | `repondre_avec_renvoi` : citer l'article, signaler explicitement le renvoi externe et **ne jamais inventer de taux ou barème**. |
| **`hors_champ`** (`hors_champ` / `na`) | **50** *(40 aveugle / 10 equipe)* | Aucun des 441 articles ne traite le sujet : fiscalité (IUTS, TVA), foncier/famille, sociétés OHADA, gestion interne de carrière publique, droit étranger ou loi de 2008 abrogée, barèmes CNSS hors Code, demandes hors droit. | Calcul de l'IUTS ou de la TVA ; titre foncier, divorce, création de SARL ; montant exact d'une pension de retraite CNSS. | `refuser_hors_champ` : refuser clairement et orienter vers l'interlocuteur adapté (DGI, CNSS, notaire, etc.). |
| **`doute`** (`doute` / `na`) | **20** *(16 aveugle / 4 equipe)* | Énoncé trop vague, incomplet ou mêlant plusieurs régimes sans fait déterminant permettant de trancher à partir du Code (`article_principal = null`). | « Mon patron veut me renvoyer parce que j'ai manqué 3 jours, il a le droit ? » (motif, justificatif et type de contrat absents). | `demander_clarification` : identifier les faits manquants et poser 2 à 3 questions de clarification ciblées. |

---

## 3. Traçabilité de l'origine (`origine`), double codage et schéma normalisé

Pour éviter le biais lexical qui favorise artificiellement la recherche par mots-clés (**BM25**), chaque question renseigne obligatoirement **`origine`** :
- **`aveugle`** (**`206` questions = `76,3 % ≥ 75 %`**, indicateur principal) : formulée avec le langage du quotidien sans accès au texte de loi, puis annotée et vérifiée ;
- **`equipe`** (**`64` questions = `23,7 %`**, indicateur secondaire) : rédigée en interne par nos trois contributeurs (un data analyst et deux développeurs comptant deux à trois ans maximum d'expérience en entreprise), sans reprise d'anciennes listes de questions rédigées texte sous les yeux et soumise aux mêmes contrôles anti-fuite lexicale.

**Double annotation indépendante :** 30 % stratifié du jeu (**81 fiches**) est ré-annoté en aveugle pour vérifier la fiabilité de l'étiquetage (accord minimum sur `article_principal` ≥ 85 %, Jaccard moyen sur $R_i \ge 0{,}60$).

**Schéma JSON normalisé (26 champs dans `data/processed/jeu_evaluation_270.json`) :**
`id`, `question`, `origine`, `statut_champ`, `renvoi_externe`, `strate`, `persona`, `registre`, `forme`, `type_question`, `famille_id`, `difficulte`, `comportement_attendu`, `theme_titre`, `source_pdf`, `pages_pdf`, `article_principal`, `articles_complementaires`, `roles_articles_complementaires`, `nombres_cles`, `points_cles`, `variantes_acceptables`, `conditions_exceptions`, `erreurs_frequentes`, `reponse_reference`, `statut_relecture_juriste`.

---

## 4. Protocole de relecture juridique et évaluation des réponses générées

1. **Validation des étiquettes (avant gel du découpage 70/30) :** par lots progressifs via `data/processed/revue_juriste_270.csv`, `SOULAMA Grace Hope` vérifie l'exactitude de l'`article_principal`, des `articles_complementaires`, de `statut_champ`, de `renvoi_externe`, des `nombres_cles` et de la `reponse_reference`. Le gel de `validation.json` (189) et `test.json` (81) reste bloqué tant que 100 % des 270 fiches n'ont pas `statut_relecture_juriste == "valide"`.
2. **Évaluation manuelle de la fidélité des réponses rédigées par le LLM (modèle de langage) :**
   - première vérification du prompt système (`src/generation/prompts.py`, `temperature ≤ 0,1`) sur `Validation` en Phase 2, sans toucher à `Test` ;
   - audit final sur un échantillon stratifié d'**au moins 30 réponses** tirées de `Test` en Phase 3 (majorité `aveugle`, questions multi-articles, **≥ 5 questions avec `renvoi_externe = oui`**), avec **double évaluation sur ≥ 10 réponses** et relecture partielle par la juriste.

**Grille d'évaluation à 5 critères (cohérente avec `protocole_evaluation.md`) :**

| Critère | Valeurs possibles | Règle d'évaluation et cible |
| :--- | :--- | :--- |
| **Verdict de fidélité** | `Fidèle` / `Incomplète` / `Erronée` | **Fidèle (`complet`) :** tous les `points_cles` obligatoires (ou `variantes_acceptables`) sont couverts et conformes ; **Incomplète (`partiel`) :** règle centrale juste mais condition/exception omise ; **Erronée (`faux` / `hors_sujet`) :** contresens, invention ou piège d'`erreurs_frequentes`. **Cible : ≥ 85 % `Fidèle`.** |
| **Nombres exacts** | `Oui` / `Non` / `N/A` | Tous les nombres correspondent exactement aux `nombres_cles` officiels. **Toute erreur numérique classe automatiquement la réponse en `Erronée`.** **Cible : 0 % visé (≤ 5 % toléré).** |
| **Citations valides** *(auto)* | `Oui` / `Non` | Chaque article cité existe dans `1..441` et figure dans les extraits fournis au LLM. **Cible : 0 % de citation inventée.** |
| **Renvoi externe respecté** | `Oui` / `Non` / `N/A` | Lorsque `renvoi_externe = oui`, le renvoi (convention collective / décret) est explicitement signalé sans inventer de montant ni de barème. |
| **Respect du prompt système** | `Oui` / `Partiel` / `Non` | Zéro connaissance extérieure (droit étranger, Code 2008), ton neutre (ni pro-employeur ni pro-salarié), français clair et avertissement documentaire présent. **Cible : ≥ 90 % `Oui`.** |

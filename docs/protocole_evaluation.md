# Protocole d'évaluation : Assistant Code du travail burkinabè

**Corpus évalué :** Loi n° 013-2026/ALP du 6 mai 2026 portant Code du travail au Burkina Faso (441 articles, promulguée par décret n° 2026-0613/PF du 25 mai 2026, publiée au Journal Officiel Spécial N°23 du 29 mai 2026).

Ce protocole fixe l'ensemble des métriques, règles de découpage et critères de succès avant toute modélisation afin de garantir une évaluation reproductible et sans fuite de données (*data leakage*, c'est-à-dire l'utilisation involontaire de données de test pendant les réglages).

---

## 1. Jeu de données d'évaluation et découpage Validation / Test

### 1.1 Composition et étiquetage du jeu d'évaluation
Nous visons un jeu d'évaluation de **270 questions**, réparties en **200 questions dans le champ**, **50 questions hors champ** et **20 questions en zone de doute**, avec un seuil minimal acceptable d'environ **180 questions** (150 dans le champ et 30 hors champ). Nous avons retenu la cible de **270 questions** pour quatre raisons concrètes :
- **Puissance statistique en `Test` :** avec un découpage `70/30`, 270 questions fournissent **81 questions de test** (`60` dans le champ, `15` hors champ, `6` en zone de doute), ce qui limite l'incertitude des intervalles de confiance **bootstrap** (méthode de rééchantillonnage statistique) à 95 % lors de la comparaison entre **BM25** (recherche par mots-clés), recherche sémantique et recherche hybride. Au seuil minimal de 180 questions, le jeu `Test` tomberait à 54 questions (`45` dans le champ et `9` hors champ), rendant les comparaisons par sous-groupe trop instables.
- **Couverture des 441 articles et des strates :** 200 questions dans le champ permettent de couvrir les principaux thèmes des 10 Titres du Code tout en tenant nos quotas de questions multi-articles (`80/200`, soit `40 %`) et de renvois externes (`30/200`, soit `15 %`).
- **Mesure dédiée de la zone de doute :** les 20 questions en zone de doute ajoutent une strate absente du seuil minimal de 180, afin d'évaluer la capacité de l'assistant à demander une précision sur un énoncé ambigu plutôt que de deviner ou refuser à tort.
- **Faisabilité de la relecture juridique :** 270 fiches restent un volume compatible avec une validation juridique à 100 % et une double annotation indépendante sur 30 % du jeu (`81` fiches).

Au moins **75 %** des questions (`206/270`, soit `76,3 %`) sont rédigées **à l'aveugle**, c'est-à-dire formulées par des profils extérieurs sans accès au texte de loi afin de refléter le langage réel des utilisateurs. Les **64 autres questions (`23,7 %`)**, étiquetées `equipe`, sont rédigées en interne par nos trois contributeurs (un data analyst et deux développeurs comptant deux à trois ans maximum d'expérience en entreprise) et soumises aux mêmes contrôles anti-fuite lexicale.

Pour garantir la fiabilité de l'étiquetage, une double annotation indépendante est réalisée sur un échantillon stratifié de **30 % du jeu (81 questions)**, avec un accord minimum de **85 %** sur l'article principal et un **indice de Jaccard moyen** (part des articles communs sur l'ensemble des articles cités par les deux annotateurs) d'au moins **0,60** sur l'ensemble des articles cités. L'ensemble des 270 fiches fait ensuite l'objet d'une relecture juridique complète par `SOULAMA Grace Hope` (Juriste, Hakili Lab).

Chaque question est enregistrée dans `data/processed/jeu_evaluation_270.json` au format normalisé à **26 champs** défini dans `consignes_etiquetage.md`, comprenant notamment :
- `origine` : `aveugle` (`206` questions) ou `equipe` (`64` questions) ;
- `statut_champ` : `dans_le_champ` (incluant les exclusions explicites traitées par le texte, comme les agents publics à l'article 2 ou l'abrogation de la loi de 2008 à l'article 440), `hors_champ` (droit foncier, fiscalité, barèmes de cotisations CNSS) ou `doute` (énoncé ambigu ou incomplet appelant une précision) ;
- `renvoi_externe` : `oui` ou `non` pour les questions dans le champ (cible : `30/200`, soit `15 %`, avec un minimum de `10 %`), et `na` pour `hors_champ` et `doute` ;
- `strate` : `dans_le_champ__sans_renvoi`, `dans_le_champ__renvoi`, `hors_champ` ou `doute` ;
- `comportement_attendu` : `repondre`, `repondre_avec_renvoi`, `refuser_hors_champ` ou `demander_clarification` ;
- `article_principal` et `articles_complementaires` (avec leur rôle dans `roles_articles_complementaires`, au maximum 4 articles attendus en règle générale et 5 au maximum ; cible **40 % de questions multi-articles**, plancher bloquant **≥ 38 %** soit ≥ 76/200) ;
- `persona`, `registre` (`populaire`, `courant`, `soutenu`), `forme`, `type_question`, `famille_id` (identifiant regroupant les paraphrases d'un même besoin juridique), `source_pdf`, `pages_pdf` ;
- `nombres_cles`, `points_cles` (chaque point étant lié à son article et à sa page PDF), `variantes_acceptables`, `conditions_exceptions`, `erreurs_frequentes`, `reponse_reference` et `statut_relecture_juriste` (`a_valider` puis `valide`).

### 1.2 Découpage unique `Validation` / `Test` et proportions cibles
- **Moment du découpage :** effectué **une seule fois**, uniquement après validation juridique à **100 %** (`statut_relecture_juriste == "valide"`) et avant tout réglage de modèle ou d'hyperparamètre, avec une graine aléatoire fixe (`random_state = 42`), puis enregistré dans `data/processed/validation.json` et `data/processed/test.json` avec empreinte SHA-256.
- **Groupement par `famille_id` :** toutes les paraphrases partageant un même `famille_id` sont affectées ensemble soit à `Validation`, soit à `Test`, afin qu'aucun besoin juridique ne fuite entre les deux jeux.
- **Répartition cible (270 questions = 200 dans le champ + 50 hors champ + 20 doute) :** découpage **70 % Validation (189) / 30 % Test (81)** stratifié par `(strate, origine)` :

| # | Strate (`strate`) | Total | `aveugle` | `equipe` | `Validation` (70 %) | `Test` (30 %) |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | `dans_le_champ__sans_renvoi` | **170** | 127 | 43 | **119** *(89 / 30)* | **51** *(38 / 13)* |
| **2** | `dans_le_champ__renvoi` | **30** | 23 | 7 | **21** *(16 / 5)* | **9** *(7 / 2)* |
| **3** | `hors_champ` | **50** | 40 | 10 | **35** *(28 / 7)* | **15** *(12 / 3)* |
| **4** | `doute` | **20** | 16 | 4 | **14** *(11 / 3)* | **6** *(5 / 1)* |
| | **Sous-total `dans_le_champ`** | **200** | **150** *(75,0 %)* | **50** *(25,0 %)* | **140** *(105 / 35)* | **60** *(45 / 15)* |
| | **Total général** | **270** | **206** *(76,3 %)* | **64** *(23,7 %)* | **189** *(144 / 45)* | **81** *(62 / 19)* |

Les effectifs définitifs conservent au moins **75 %** de questions `aveugle`, **≥ 10 %** (`15 %` cible) de questions à renvoi externe dans le champ et **≥ 38 %** (`40 %` cible) de questions multi-articles dans le champ.

- **Règle d'isolation :**
  - `Validation` sert exclusivement à comparer les architectures candidates (modèles de vecteurs sémantiques, pondération hybride BM25 + sémantique), à calibrer les seuils de refus/doute et à ajuster le prompt système du modèle de langage.
  - `Test` reste verrouillé pendant tout le développement et n'est évalué qu'une fois les paramètres figés.

---

## 2. Partie 1 : Évaluation de la recherche d'articles

### 2.1 Systèmes comparés
- **Modèle de référence (baseline) :** **BM25**, un algorithme de recherche lexicale classique basé sur la fréquence et la rareté des mots-clés dans les 441 articles structurés.
- **Systèmes candidats :** recherche sémantique par *embeddings* (vecteurs numériques représentant le sens des phrases en français ou multilingue) et **recherche hybride** combinant BM25 et recherche sémantique.

### 2.2 Deux métriques complémentaires (multi-articles)
Soit $N$ le nombre total de questions dans le champ évaluées. Pour chaque question $i \in \{1, \dots, N\}$, notons :
- $T_5(i)$ l'ensemble des 5 premiers articles retournés par le système ;
- $a_i^*$ l'**article principal** attendu ;
- $C_i$ l'ensemble des **articles complémentaires** attendus (éventuellement vide, $C_i = \emptyset$, lorsqu'un seul article suffit) ;
- $R_i = \{a_i^*\} \cup C_i$ l'ensemble de tous les **articles pertinents** (principal et complémentaires).

1. **`Succès@5` (présence de l'article principal dans le top-5) :**
   $$\text{Succès@5} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{1}\!\left(a_i^* \in T_5(i)\right)$$
   où $\mathbf{1}(a_i^* \in T_5(i))$ vaut `1` si l'article principal figure dans les 5 premiers résultats et `0` sinon.  
   *Exemple :* sur les $N = 60$ questions dans le champ du jeu `Test`, si l'article principal figure dans le top-5 pour 51 questions, `Succès@5 = 85,0 %`.

2. **`Rappel@5` (part moyenne des articles pertinents retrouvés dans le top-5) :**
   $$\text{Rappel@5} = \frac{1}{N} \sum_{i=1}^{N} \frac{|R_i \cap T_5(i)|}{|R_i|}$$
   *Exemple :* si une question attend Art. 49 (principal) et Art. 48 (complémentaire) et que le top-5 ne contient que Art. 49, le rappel sur cette question vaut `1/2 = 50 %`.

### 2.3 Matrice de gestion des cas (`Succès@5` × `Rappel@5`)
Sur les questions dans le champ (`140` en `Validation`, `60` en `Test`), un `Succès@5 = 1` ne garantit pas une couverture suffisante des articles complémentaires, et un `Rappel@5` élevé ne compense pas l'absence de l'article principal (`Succès@5 = 0`).

Pour qualifier chaque question $i$ et guider les réglages sur `Validation`, nous fixons deux seuils sur `Rappel@5` (distincts des seuils de refus en ligne de la Partie 2) :
- **Seuil de refus recherche :** $r_{\text{refus}} = 0{,}40$ (`40 %`) ;
- **Marge de doute :** $0{,}40 < \text{Rappel@5} < 0{,}80$ (incluant `1/2 = 50 %` sur 2 articles et `2/3 = 66,7 %` sur 3 articles) ;
- **Seuil acceptable :** $r_{\text{acc}} = 0{,}80$ (`80 %`).

Le croisement des **2 valeurs de `Succès@5`** (`1` ou `0`) et des **3 zones de `Rappel@5`** définit 6 cas :

| `Succès@5` | Zone de `Rappel@5` | Interprétation | Verdict (évaluation recherche) | Gestion / Action |
| :---: | :--- | :--- | :--- | :--- |
| **`1`** | `Rappel@5 ≥ 0,80` *(acceptable)* | Article principal présent et quasi-totalité (ou totalité) des articles complémentaires dans le top-5. | **Accepté : Succès complet** | Validation côté recherche ; évaluation normale de la réponse rédigée (Partie 3). |
| **`1`** | `0,40 < Rappel@5 < 0,80` *(marge de doute)* | Article principal présent, mais une partie des complémentaires manque (ex. `1/2 = 50 %` ou `2/3 = 66,7 %`). | **Doute : Succès partiel** | Risque de réponse `Incomplète` en Partie 3. Sur `Validation`, inspecter l'article manquant et ajuster les poids hybrides, le reclassement ou le regroupement par section. |
| **`1`** | `Rappel@5 ≤ 0,40` *(seuil de refus)* | Article principal présent, mais la majorité des complémentaires manque (ex. `1/3 = 33,3 %`). | **Refus : Couverture insuffisante** | **Ne pas valider sur le seul `Succès@5 = 1`.** Déclencher une alerte multi-articles, contrôler le risque d'omission d'exception et corriger sur `Validation` (renvois internes, regroupement par sous-section). |
| **`0`** | `Rappel@5 ≥ 0,80` *(acceptable)* | Article principal absent malgré la présence de presque tous les complémentaires (cas rare, ex. 4/5 sans $a_i^*$). | **Refus : Alerte d'inversion** | **Règle hiérarchique :** sans l'article principal, le cas n'est jamais accepté. Analyser pourquoi $a_i^*$ est classé après ses complémentaires (reclassement) et vérifier son étiquetage. |
| **`0`** | `0,40 < Rappel@5 < 0,80` *(marge de doute)* | Article principal absent, seuls quelques articles complémentaires figurent dans le top-5. | **Refus : Ambigu critique** | Fort risque de réponse hors sujet. Classer en échec recherche ; vérifier sur `Validation` si la question ambiguë relève de la zone de doute de la Partie 2. |
| **`0`** | `Rappel@5 ≤ 0,40` *(seuil de refus)* | Article principal absent et aucun (ou presque aucun) complémentaire retrouvé (dont `0 %` sur toute question mono-article ratée). | **Refus : Échec franc** | Échec complet de recherche. En production, la Partie 2 doit privilégier le refus plutôt que l'invention ; sur `Validation`, corriger via embeddings/hybride ou contrôle OCR. |

**Règle de synthèse :** `Succès@5 = 0` bloque systématiquement l'acceptation quel que soit `Rappel@5`. Sur `Validation` ($N = 140$) puis `Test` ($N = 60$), le rapport d'évaluation indique la répartition des questions dans ces 6 cases en plus des moyennes globales.

### 2.4 Séparation `aveugle` vs `equipe`
Les résultats sont présentés **séparément** pour :
- le sous-ensemble **`aveugle`** (**indicateur principal**, exempt de biais lexical lié à la lecture préalable du Code ; cible `45` questions dans le champ sur `Test`) ;
- le sous-ensemble **`equipe`** (**indicateur secondaire**, conservé à titre de comparaison ; cible `15` questions dans le champ sur `Test`).

### 2.5 Intervalles de confiance par bootstrap apparié à 95 %
Un simple écart de score moyen entre deux systèmes peut être dû au hasard du choix des questions. Pour mesurer la fiabilité de cet écart, nous utilisons un **bootstrap apparié à 95 %**, une méthode de rééchantillonnage statistique qui simule de nombreux jeux de test à partir de nos scores réels :
- **Apparié :** le système évalué et la référence BM25 sont comparés **question par question sur exactement les mêmes questions** de `Test`, ce qui élimine l'effet de difficulté propre à chaque question.
- **Bootstrap :** on tire au sort avec remise $B = 10\,000$ échantillons de taille $N$ parmi les écarts observés afin d'estimer la marge d'incertitude sans hypothèse statistique forte (comme la normalité des scores).
- **Intervalle de confiance à 95 % (IC 95 %) :** fourchette qui encadre les 95 % centraux des écarts simulés (entre le percentile `2,5 %` et le percentile `97,5 %`).

**Notations (pour une métrique $m$ donnée : `Succès@5` ou `Rappel@5`) :**
- $m_{\text{système}}(i)$ : score obtenu par le système évalué sur la question $i$ (`0` ou `1` pour `Succès@5` ; valeur entre `0` et `1` pour `Rappel@5`) ;
- $m_{\text{BM25}}(i)$ : score obtenu par BM25 sur cette **même** question $i$ ;
- $d_i = m_{\text{système}}(i) - m_{\text{BM25}}(i)$ : **écart individuel** sur la question $i$.

**Procédure de calcul :**
1. Calculer les $N$ écarts individuels $(d_1, \dots, d_N)$ sur les $N$ questions du jeu `Test`.
2. Répéter **$B = 10\,000$ fois** le tirage aléatoire avec remise de $N$ écarts parmi $(d_1, \dots, d_N)$, et calculer la moyenne $\bar{d}^{(b)}$ de chaque tirage.
3. Trier les $10\,000$ valeurs $\bar{d}^{(b)}$ : la **borne basse** est le percentile `2,5 %` et la **borne haute** est le percentile `97,5 %`.

*Exemple de lecture :* un gain de **`+13,0 pts` (IC 95 % : `[+6,5 ; +19,5]`)** indique une amélioration statistiquement solide car toute la fourchette est strictement supérieure à `0`. Un IC 95 % de **`[-2,0 ; +16,0]`** contient `0` : l'écart observé peut s'expliquer par le hasard.

**Critère de succès technique (recherche) :** sur le jeu `Test` ($N = 60$ questions dans le champ, en particulier les `45` du sous-ensemble `aveugle`), le système retenu dépasse **BM25** d'au moins **+10 points** sur `Succès@5` et/ou `Rappel@5`, avec un IC 95 % dont la borne inférieure reste strictement positive (`> 0`), **sans régression sur `Rappel@5` par rapport à BM25** et avec suivi explicite des cas de couverture insuffisante (`Succès@5 = 1` et `Rappel@5 ≤ 0,40`).

---

## 3. Partie 2 : Évaluation du refus (« hors champ » et « doute »)

### 3.1 Mesure de confiance et règles de décision
Pour chaque requête $q$, le moteur de recherche retourne une liste ordonnée d'articles assortis de leur score de pertinence. Notons $a_1$ et $a_2$ les articles classés respectivement aux rangs 1 et 2, $s_1$ et $s_2$ leurs scores associés, et $\Delta_{12} = s_1 - s_2$ la **marge de séparation** entre ces deux premiers candidats.

La décision de répondre ou de refuser (« *Cette question sort du champ du Code du travail ou ne permet pas de répondre avec certitude* ») repose sur trois seuils calibrés exclusivement sur `Validation` :
- **`τ_score` (seuil bas, refus hors champ) :** score minimal en dessous duquel aucun article du corpus n'est jugé suffisamment proche de la question ;
- **`τ_haut` (seuil haut, certitude forte) :** score au-dessus duquel le système répond directement, même si le 2e article obtient un score proche (cas fréquent des questions multi-articles) ;
- **`τ_marge` (seuil d'écart en zone intermédiaire) :** écart minimal requis entre $s_1$ et $s_2$ lorsque $s_1$ se situe dans la zone intermédiaire (`τ_score ≤ s₁ < τ_haut`).

Trois zones de décision en découlent :
1. **Refus hors champ (`s₁ < τ_score`) :** proximité insuffisante avec le Code du travail, entraînant un refus immédiat.
2. **Zone de doute (`τ_score ≤ s₁ < τ_haut`) :** si $\Delta_{12} < \tau_{\text{marge}}$, les résultats sont moyens et peu différenciés, entraînant un **refus prudent ou une demande de précision** ; sinon ($\Delta_{12} \ge \tau_{\text{marge}}$), le système répond.
3. **Réponse directe (`s₁ ≥ τ_haut`) :** correspondance forte, le système répond sans contrainte de marge.

La mesure de score utilisée pour `s₁` et `Δ₁₂` dépend de la méthode de recherche évaluée :

| Méthode de recherche | Score utilisé pour le classement | Mesure utilisée pour le refus (`s₁` et `Δ₁₂`) | Justification |
| :--- | :--- | :--- | :--- |
| **BM25** *(référence)* | Score BM25 brut (`[0, +∞[`) | Score BM25 maximal `s₁` (brut ou normalisé par le nombre de termes de la requête) | Le score BM25 n'est pas borné et dépend de la longueur de la question ; la normalisation améliore la comparabilité entre requêtes courtes et longues. |
| **Embeddings** *(sémantique)* | Similarité cosinus (`[-1, 1]`, en pratique `[0, 1]`) | `s₁ = cos(q, a₁)` et `Δ₁₂ = cos(q, a₁) - cos(q, a₂)` | Échelle bornée et directement comparable d'une question à l'autre, adaptée à la détection du hors champ. |
| **Hybride** *(BM25 + Embeddings)* | Fusion de rangs (**RRF**, combinaison de classements) ou somme pondérée | **Règle principale :** classement par fusion hybride, mais **refus décidé sur la similarité cosinus sémantique** du meilleur article retenu *(variante testée sur `Validation` : score hybride normalisé)* | Une fusion par rangs (RRF) dépend uniquement des positions et non de la proximité absolue avec le corpus ; la similarité cosinus conserve un signal fiable pour rejeter les requêtes hors champ. |

Le choix final entre le seuil simple (`s₁ < τ_score` seul) et la règle combinée (`s₁` + `Δ₁₂`), ainsi que les valeurs numériques de `τ_score`, `τ_haut` et `τ_marge`, sont fixés **uniquement sur `Validation`**.

### 3.2 Métriques et critères de succès (refus et zone de doute)
Sur le jeu `Test` (`15` questions `hors_champ`, `6` questions `doute` et `60` questions `dans_le_champ`) :
- **Taux de refus correct (`hors_champ`)** = part des questions `hors_champ` effectivement refusées. **Cible : ≥ 80 %.**
- **Taux de faux refus (questions légitimes)** = part des questions `dans_le_champ` refusées à tort. **Cible : ≤ 10 %.**
- **Taux de clarification pertinente (`doute`)** = part des `6` questions `doute` donnant lieu à une demande de précision pertinente, sans réponse péremptoire erronée.

---

## 4. Partie 3 : Évaluation manuelle de la fidélité des réponses rédigées (LLM)

Le contrôle automatique des numéros d'articles vérifie que chaque article cité existe dans la loi et provient bien des extraits fournis (objectif : 0 % de citation inventée). Ce contrôle automatique ne suffit toutefois pas à vérifier que l'explication rédigée par le **LLM** (*Large Language Model*, le modèle de langage générant la synthèse) est juridiquement fidèle et respecte son prompt système.

### 4.1 Prompt système et paramètres de génération
La synthèse générée est encadrée par un **prompt système versionné** (`src/generation/prompts.py`), réglé avec une température basse (`temperature = 0` ou `≤ 0,1`) pour limiter les variations et les inventions. Toute évolution du prompt est testée exclusivement sur `Validation`, puis figée avant l'évaluation sur `Test`.

```text
Tu es un assistant documentaire dédié uniquement à la loi n° 013-2026/ALP du 6 mai 2026
(promulguée le 25 mai 2026) portant Code du travail au Burkina Faso.

Règles impératives :
1. Source unique : réponds UNIQUEMENT à partir des extraits d'articles fournis dans le
   contexte ci-dessous. N'utilise jamais ta mémoire générale, ni l'ancien Code de 2008,
   ni le droit d'un autre pays.
2. Citations obligatoires : cite explicitement le numéro de chaque article utilisé, et
   uniquement des articles présents dans le contexte fourni.
3. Exactitude des nombres : recopie fidèlement toutes les durées, délais, âges, seuils
   et nombres de renouvellements sans les modifier ni les généraliser.
4. Refus et renvois externes :
   - Si les extraits fournis ne permettent pas de répondre avec certitude, indique
     clairement que le texte fourni ne permet pas de répondre.
   - Si un article renvoie à une convention collective ou à un texte réglementaire
     (décret, arrêté), signale-le explicitement sans inventer de montant ni de barème.
5. Neutralité et forme : rédige une explication courte, claire et neutre (ni pro-employeur,
   ni pro-salarié) en français courant, suivie d'un rappel que cette réponse constitue une
   aide documentaire et ne remplace ni un avocat ni un inspecteur du travail.
```

### 4.2 Échantillon évalué
- **Volume :** au moins **30 réponses générées** tirées de manière stratifiée dans le jeu `Test`, incluant une majorité de questions **`aveugle`**, des questions **multi-articles** et au moins **5 questions à renvoi externe** (conventions collectives, textes réglementaires).
- **Modalité :** grille remplie manuellement avec double évaluation sur au moins 10 réponses pour contrôler la cohérence interne, et relecture partielle par la juriste `SOULAMA Grace Hope` sous réserve d'accord complémentaire.

### 4.3 Grille d'évaluation de fidélité et de respect du prompt système
La grille exploite directement les champs structurés du jeu de référence (`points_cles`, `nombres_cles`, `variantes_acceptables`, `conditions_exceptions`, `erreurs_frequentes`).

| Critère | Valeurs possibles | Définition opérationnelle |
| :--- | :--- | :--- |
| **Verdict de fidélité** | `Fidèle` / `Incomplète` / `Erronée` | **Fidèle (`complet`) :** tous les `points_cles` obligatoires (ou `variantes_acceptables`) sont couverts et conformes aux articles cités ; **Incomplète (`partiel`) :** règle centrale juste mais omet un élément de `points_cles` ou une condition/exception ; **Erronée (`faux` / `hors_sujet`) :** contredit la loi, tombe dans un piège d'`erreurs_frequentes`, généralise abusivement ou invente une règle. |
| **Nombres exacts** | `Oui` / `Non` / `N/A` | Tous les nombres présents dans la réponse correspondent exactement aux `nombres_cles` du texte officiel. **Toute erreur numérique classe automatiquement la réponse en `Erronée`.** |
| **Citations valides** *(auto)* | `Oui` / `Non` | Chaque article cité existe dans les 441 articles et appartient aux extraits transmis au modèle de langage. |
| **Renvoi externe respecté** | `Oui` / `Non` / `N/A` | Pour les questions avec `renvoi_externe = oui`, le système indique explicitement le renvoi (convention collective, décret) sans inventer de montant ni de barème. |
| **Respect du prompt système** | `Oui` / `Partiel` / `Non` | Absence de connaissances extérieures au contexte (droit étranger, Code de 2008), ton neutre (ni pro-employeur ni pro-salarié), français clair et présence de l'avertissement documentaire. |

**Objectif cible :** ≥ 85 % de réponses jugées `Fidèle`, **0 % d'erreur numérique** visé sur l'échantillon évalué (seuil toléré : ≤ 5 %), **0 % de citation inventée**, et **≥ 90 % de respect complet du prompt système**.

---

## 5. Partie 4 : Évaluation métier (essai utilisateurs)

En complément des métriques techniques, l'utilité réelle de l'outil est mesurée en conditions d'usage :
- **≥ 10 testeurs** externes (salariés, gérants de PME, référent juridique), **3 questions imposées** chacun ;
- **Chronométrage comparatif :** temps de réponse sourcée dans l'outil (< 10 secondes) comparé à la recherche manuelle dans les PDF officiels du Code du travail (127 à 128 pages) ;
- **Questionnaire court** (clarté, utilité, confiance) avec une cible de **≥ 80 % d'avis positifs** ;
- Information préalable, consentement des testeurs et **aucune donnée personnelle conservée**.

---

## 6. Tableau de restitution des résultats

La restitution présente les résultats séparés `aveugle` (indicateur principal) et `equipe` (indicateur secondaire), complétés par une ventilation par `registre` (`populaire`, `courant`, `soutenu`) et `type_question`.

| Système | Sous-ensemble | `Succès@5` | `Rappel@5` | Écart vs BM25 (IC 95 % bootstrap) | Refus hors champ (≥ 80 %) | Faux refus légitimes (≤ 10 %) | Clarification `doute` (6 q. Test) | Fidélité / Nombres / Prompt (≥ 30 rép.) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BM25 (référence)** | `aveugle` | - | - | Référence | - | - | - | N/A |
| **BM25 (référence)** | `equipe` | - | - | Référence | - | - | - | N/A |
| **Sémantique seul** | `aveugle` | - | - | - | - | - | - | - |
| **Sémantique seul** | `equipe` | - | - | - | - | - | - | - |
| **Hybride (BM25 + Sém.)** | `aveugle` | - | - | **Cible : ≥ +10 pts** | **≥ 80 %** | **≤ 10 %** | Suivi dédié | **≥ 85 % / ~0 % err. / ≥ 90 %** |
| **Hybride (BM25 + Sém.)** | `equipe` | - | - | - | - | - | Suivi dédié | - |

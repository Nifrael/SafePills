# 📖 Documentation Technique — SafePills

> Documentation détaillée de chaque fichier du projet et du fonctionnement de l'application.

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Flux utilisateur](#flux-utilisateur)
3. [Frontend — Fichiers détaillés](#frontend)
4. [Backend — Fichiers détaillés](#backend)
5. [Scripts ETL](#scripts-etl)
6. [Configuration & DevOps](#configuration--devops)
7. [Tests](#tests)

---

## Vue d'ensemble

**SafePills** est une application web d'aide à la décision pour l'automédication. Elle permet à un utilisateur de vérifier si un médicament en vente libre (OTC) est adapté à sa situation personnelle (âge, genre, pathologies, grossesse, etc.).

### Architecture haut niveau

```
┌─────────────────────┐         ┌──────────────────────────┐
│   Frontend (Astro)  │  HTTP   │     Backend (FastAPI)     │
│   Vercel (SSG)      │◄───────►│     Render (Docker)       │
│                     │         │                          │
│  React Islands      │         │  SQLite + Google GenAI   │
└─────────────────────┘         └──────────────────────────┘
```

### Flux de données

```
Utilisateur → Recherche médicament → Sélection → Questionnaire dynamique
    → Calcul du score (GREEN/YELLOW/ORANGE/RED) → Explication IA → Affichage résultat
```

---

## Flux utilisateur

### 1. Recherche (`/api/search`)

L'utilisateur tape le nom d'un médicament ou d'une substance. Le frontend appelle `/api/search?q=...` qui cherche en SQL (`LIKE`) dans les tables `brands` et `substances`.

### 2. Questions (`/api/automedication/flow/:cis`)

Après sélection d'un médicament (identifié par son code CIS), le frontend récupère la liste des questions pertinentes. Le backend :

- Identifie les substances du médicament
- Trouve les familles de substances correspondantes
- Charge les règles médicales (`rules`) associées
- Filtre selon la voie d'administration
- Convertit en questions pour le frontend

### 3. Évaluation (`/api/automedication/evaluate`)

L'utilisateur répond aux questions (oui/non, âge, genre). Le frontend envoie les réponses au backend qui :

1. **Calcule le score** via `RiskCalculator` (vert → rouge)
2. **Vérifie si le médicament est OTC**
3. **Vérifie la couverture** (le médicament est-il dans notre base ?)
4. **Génère une explication IA** via Google GenAI (si score non-vert)
5. **Retourne** le résultat complet au frontend

---

## Frontend

### Configuration

| Fichier            | Rôle                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| `astro.config.mjs` | Configuration Astro : intégration React, i18n (FR défaut, ES), routing sans préfixe pour FR            |
| `tsconfig.json`    | TypeScript strict, alias de paths (`@components/*`, `@styles/*`, `@i18n/*`, `@lib/*`)                  |
| `package.json`     | Dépendances : Astro 5, React 18, Sass, Nano Stores, Karla/Ysabeau fonts. Dev : Vitest, RTL, Playwright |
| `vitest.config.ts` | Config Vitest : environnement jsdom, globals activés, setup RTL                                        |

### Pages (`src/pages/`)

| Fichier                   | Route                | Description                                                       |
| ------------------------- | -------------------- | ----------------------------------------------------------------- |
| `index.astro`             | `/`                  | Page d'accueil FR avec Hero et Features                           |
| `automedication.astro`    | `/automedication`    | Page d'automédication FR (contient le composant React interactif) |
| `es/index.astro`          | `/es`                | Page d'accueil ES                                                 |
| `es/automedication.astro` | `/es/automedication` | Page d'automédication ES                                          |

Chaque page `.astro` utilise le `Layout` global et passe un `title`. Les pages ES sont des copies avec `lang="es"`.

### Layouts (`src/layouts/`)

| Fichier        | Description                                                                                                                                                                                             |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Layout.astro` | Layout principal : `<html lang>`, `<head>` avec SEO (meta description, Open Graph, canonical), favicon, `<Navbar>`, `<main>`, `<MedicalDisclaimer>`, `<Footer>`. Props typées (`title`, `description`). |

### Composants Globaux (`src/components/global/`)

| Fichier                   | Description                                                                                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Navbar.astro`            | Navigation responsive : logo SafePills + badge Bêta, switch de langue FR/ES, menu hamburger mobile, CTA « Testez ! ». SCSS scoped avec variables et mixins. |
| `Footer.astro`            | Pied de page : logo, disclaimer médical, copyright dynamique.                                                                                               |
| `MedicalDisclaimer.astro` | Bandeau d'avertissement : rappelle que l'outil ne remplace pas un avis médical professionnel.                                                               |

### Composants Home (`src/components/home/`)

| Fichier          | Description                                                                                           |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `Hero.astro`     | Section hero plein écran : image SafePills, badge « FIABILITÉ MÉDICALE », texte d'alerte, double CTA. |
| `Features.astro` | Section « Comment ça marche ? » : 3 étapes illustrées (Recherchez, Répondez, Recevez).                |

### Composants Automédication (`src/components/features/automedication/`)

| Fichier                       | Description                                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AutomedicationContainer.tsx` | **Orchestrateur frontend** : gère les étapes (recherche → questionnaire → résultat). Maintient l'état global du flux (médicament sélectionné, réponses, score, etc.).                      |
| `AutomedicationSearch.tsx`    | Recherche de médicaments : input avec debounce, appel API `/search`, affichage des résultats avec type (substance/médicament).                                                             |
| `UnifiedQuestionnaire.tsx`    | Questionnaire dynamique : affiche les questions une par une, gère les réponses (oui/non, saisie d'âge, choix de genre), barre de progression, navigation avant/arrière, short-circuit RED. |
| `AutomedicationScore.tsx`     | Affichage du résultat : score coloré (vert/jaune/orange/rouge), conseils généraux, explication IA, avertissement de couverture, bouton de réinitialisation.                                |
| `Automedication.scss`         | Styles spécifiques au flux d'automédication.                                                                                                                                               |

### Composants Icônes (`src/components/icons/`)

6 composants SVG Astro : `ActivityIcon`, `AlertIcon`, `DocumentIcon`, `PillIcon`, `SearchIcon`, `ShieldIcon`. Chacun accepte une prop `size` et utilise `currentColor` pour la couleur.

### i18n (`src/i18n/`)

| Fichier    | Description                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ui.ts`    | Dictionnaire de traductions FR/ES : ~80 clés couvrant navigation, hero, features, automédication (search, questionnaire, score), SEO. Exporté comme `const`. |
| `utils.ts` | Utilitaires : `getLangFromUrl()` (détecte la langue depuis l'URL), `useTranslations()` (retourne une fonction `t()` typée).                                  |

### Styles (`src/styles/`)

| Fichier                    | Description                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `main.scss`                | Point d'entrée SCSS : importe toutes les partials dans l'ordre (reset, variables, typography, components).               |
| `config/_variables.scss`   | Variables CSS globales : couleurs (primary, secondary, tertiary), fonts (Karla, Ysabeau), tailles de texte, breakpoints. |
| `config/_mixins.scss`      | Mixins SCSS : `breakpoint-up()`, `keyboard-focus()`, `button-keyboard-focus()`.                                          |
| `base/_reset.scss`         | Reset CSS : box-sizing, marges, police par défaut.                                                                       |
| `base/_typography.scss`    | Styles typographiques : tailles responsives h1-h4, paragraphes.                                                          |
| `components/_buttons.scss` | Styles de boutons : `.btn-primary`, `.btn-outline`, états hover/active/disabled, focus clavier accessible.               |
| `components/_badge.scss`   | Badge « Bêta » : fond vert semi-transparent, texte petit, border-radius.                                                 |

### Configuration Frontend (`src/config.ts`)

Exporte `API_BASE_URL` pointant vers le backend (variable `PUBLIC_API_URL` ou fallback `http://localhost:8000`).

---

## Backend

### Point d'entrée (`backend/api/main.py`)

Application FastAPI avec :

- **CORS** : origines restreintes + regex `safe-pills-*.vercel.app`, headers spécifiques
- **Middleware sécurité** : ajoute headers HTTP de sécurité sur chaque réponse
- **Rate limiting** : via SlowAPI avec stockage mémoire
- **Routes** : monte les routers `drugs`, `automedication`, `flow_endpoint`
- **Production** : désactive `/docs` et `/openapi.json`

### Endpoints API (`backend/api/`)

| Fichier             | Endpoint                            | Description                                                                                                             |
| ------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `drugs.py`          | `GET /api/search?q=...`             | Recherche de médicaments/substances. Rate limit : 30/min.                                                               |
| `flow_endpoint.py`  | `GET /api/automedication/flow/:id`  | Retourne les questions pertinentes pour un médicament. Filtre par voie d'administration + profil.                       |
| `automedication.py` | `POST /api/automedication/evaluate` | Évalue le risque. Valide avec Pydantic (`AnswersRequest`), délègue à `AutomedicationOrchestrator`. Rate limit : 10/min. |

### Couche Domaine (`backend/core/`)

| Fichier      | Description                                                                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `config.py`  | `Settings(BaseSettings)` : charge `.env` automatiquement, valide les types, parse `ALLOWED_ORIGINS` en CSV. Propriétés calculées : `IS_PRODUCTION`, `DB_PATH`. Singleton via `@lru_cache`. |
| `models.py`  | Modèles métier Pydantic : `Substance`, `Brand`, `BrandSubstance`, `Rule`, `RiskLevel` (Enum 1-4).                                                                                          |
| `schemas.py` | DTOs API : `SearchResult`, `FlowQuestion`, `EvaluationResponse`, `AnswersRequest`.                                                                                                         |
| `limiter.py` | Instance SlowAPI + handler d'exception pour les erreurs 429 (Too Many Requests).                                                                                                           |
| `i18n.py`    | `I18nService` : charge les fichiers JSON de traduction (`locales/`), fournit `get()` et `translate_question()`. Singleton par langue.                                                      |

### Services Automédication (`backend/services/automedication/`)

| Fichier              | Description                                                                                                                                                |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__.py`        | Expose `evaluate_risk()` : charge les règles depuis la DB, applique le `RiskCalculator`, retourne un `EvaluationResponse`.                                 |
| `orchestrator.py`    | **Orchestrateur SRP** : coordonne l'évaluation complète (score + détails médicament + vérification OTC + couverture + appel IA). Appelé par l'endpoint.    |
| `risk_calculator.py` | `RiskCalculator.compute_score()` : fonction pure qui calcule le score de risque (GREEN/YELLOW/ORANGE/RED) à partir des règles et des réponses utilisateur. |
| `db_repository.py`   | `AutomedicationRepository` : DAO SQLite avec context managers. Méthodes : `get_rules_for_brand()`, `get_rules_by_codes()`, `get_drug_route()`.             |

### Services Recherche (`backend/services/search/`)

| Fichier         | Description                                                                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `repository.py` | `DrugRepository` : DAO SQLite. `search_substances()` et `search_drugs()` utilisent `LIKE` + `LIMIT 20`. `get_drug_details()` retourne un `Brand` avec sa composition. |
| `service.py`    | `SearchService` : combine les résultats de recherche substances + médicaments, normalise la requête.                                                                  |
| `utils.py`      | `normalize_text()` : supprime accents et met en minuscules pour la recherche.                                                                                         |

### Service IA (`backend/services/ai_service.py`)

`generate_risk_explanation()` : appel asynchrone à Google GenAI (`gemini-3-flash-preview`). Construit un prompt avec :

- Instructions système (rôle de pharmacien, ton pédagogique)
- Contexte patient (âge, genre, substances)
- Questions/réponses déclenchées
- Score et détails de risque

Retourne une explication en français ou espagnol selon la langue.

### Base de données (`backend/data/`)

- `safepills.db` : SQLite générée à partir de `medical_knowledge.json` via les scripts ETL
- `medical_knowledge.json` : Source de vérité contenant substances, familles, marques, et règles médicales
- `locales/` : Fichiers JSON de traduction pour le backend (questions, types de recherche)

---

## Scripts ETL

| Fichier                         | Description                                                                                                                                                                                                    |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `build_db.py`                   | Crée le schéma SQLite (tables `substances`, `families`, `brands`, `brand_substances`, `substance_families`, `rules`) et importe les données depuis `medical_knowledge.json`. **Exécuté lors du build Docker.** |
| `extract_data.py`               | Extrait et nettoie les données brutes depuis les fichiers sources (BDPM, liste OTC).                                                                                                                           |
| `forge_data.py`                 | Croise les données officielles BDPM avec la liste OTC pour générer le référentiel JSON.                                                                                                                        |
| `import_json_to_sqlite.py`      | Import JSON vers SQLite avec gestion des doublons et normalisation.                                                                                                                                            |
| `update_rules.py`               | Met à jour les règles médicales dans la DB à partir de modifications dans `medical_knowledge.json`.                                                                                                            |
| `reformat_medical_knowledge.py` | Reformate `medical_knowledge.json` pour homogénéiser sa structure.                                                                                                                                             |

---

## Configuration & DevOps

| Fichier            | Description                                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `Dockerfile`       | Image Python 3.11-slim. Installe les dépendances, copie le backend, génère la DB SQLite, expose le port 8000, lance Uvicorn. |
| `.env.example`     | Template des variables d'environnement : `API_KEY` (Google GenAI), `ENV` (production/dev), `ALLOWED_ORIGINS`.                |
| `.gitignore`       | Ignore : `node_modules/`, `dist/`, `.env`, `__pycache__/`, `*.db`, `backend/data/raw/`, `docs/`.                             |
| `requirements.txt` | Dépendances Python : FastAPI, Uvicorn, Pydantic, pydantic-settings, google-genai, slowapi, pytest.                           |

---

## Tests

### Backend (Pytest) — 7 tests

| Fichier                        | Tests | Description                                                                  |
| ------------------------------ | ----- | ---------------------------------------------------------------------------- |
| `test_automedication_api.py`   | 3     | Intégration API : search, flow, evaluate (avec mocking)                      |
| `test_automedication_logic.py` | 3     | Logique métier : scénario RED (grossesse), scénario GREEN, filtrage par voie |
| `test_ai_service.py`           | 1     | Service IA : vérifie l'appel au client GenAI avec le bon prompt              |

### Frontend (Vitest) — 19 tests

| Fichier                        | Tests | Description                                                                          |
| ------------------------------ | ----- | ------------------------------------------------------------------------------------ |
| `AutomedicationScore.test.tsx` | 10    | Rendu des niveaux de risque, i18n FR/ES, conseils, couverture, explication IA, reset |
| `i18n.test.ts`                 | 9     | Détection langue URL, traductions FR/ES, parité automatique des clés                 |

### Commandes

```bash
# Tests backend
python -m pytest backend/tests/ -v

# Tests frontend
npx vitest run

# Build production
npm run build
```

## 1. VISION ET OBJECTIF

Développement d'une application web ("SafePills") destinée à savoir si l'automédication peut être dangereuse dans un contexte précis.

- **Public cible :** Grand public (vulgarisation) et professionnels de santé (vérification rapide).
- **Approche :** Hybride (Site statique performant + Application dynamique).
- **Source de vérité :** Uniquement les données officielles (Thésaurus ANSM, BDPM). Pas d'hallucination médicale tolérée.

## 2. STACK TECHNIQUE

### Frontend (L'Application - Racine du projet)

- **Framework Principal :** Astro (v5+).
- **Moteur de Rendu :** Static Site Generation (SSG) par défaut.
- **Interactivité ("Îlots") :** React.
- **Langage :** TypeScript (Strict mode requis).
- **Styling :** SCSS (Sass). Pas de frameworks CSS utilitaires (Tailwind). Utilisation méthodologie BEM ou modulaire recommandée.
- **State Management :** Nano Stores (natif Astro) pour le partage d'état entre îles.
- **Tests :** Vitest + React Testing Library.

### Backend (L'Intelligence - Dossier /backend)

- **API :** Python avec FastAPI.
- **Base de Données :** SQLite (Stockage structuré des médicaments, DCI, Classes et règles du Thésaurus).
- **Configuration :** `pydantic-settings` (`BaseSettings`) pour le chargement et la validation automatique des variables d'environnement depuis `.env`.
- **Sécurité API :** `slowapi` (Rate Limiting), CORS restreint (origines + headers spécifiques), headers de sécurité HTTP, validation Pydantic stricte.
- **Logging :** Module `logging` Python (pas de `print()`). Niveaux `debug`/`info`/`warning`/`error`.
- **IA / RAG Hybride :**
  - **Moteur :** SDK Google GenAI (`google-genai`).
  - **Modèle :** `gemini-3-flash-preview` (pour la vitesse et les explications pédagogiques).
  - **Flux :** Contexte structuré (questions/réponses) -> Injection dans le prompt -> Génération pédagogique vulgarisée.
  - **Contrainte :** Structured Output souhaité pour les futurs composants.
- **Tests :** Pytest (unitaires + intégration, mocking LLM).

### Déploiement & DevOps (Infrastructure)

- **Backend (API) :** Containerisé avec **Docker** et hébergé sur **Render** (Web Service).
- **Frontend (Application) :** Déployé sur **Vercel** (Optimisation Astro).
- **CI/CD :** Génération automatique de la base SQLite lors du build Docker à partir des sources JSON (`medical_knowledge.json`).

## 3. ARCHITECTURE DU CODE

### Structure des dossiers (Convention)

```
/pharma-tools
  /src                          # <--- ZONE FRONTEND
    /components
      /ui                       # Composants atomiques (Boutons, Inputs)
      /features                 # Composants métier React
        /automedication         # Container, Search, Score, UnifiedQuestionnaire
      /global                   # Composants Astro (Navbar, Footer, MedicalDisclaimer)
      /home                     # Composants page d'accueil (Hero, Features)
      /icons                    # Composants SVG (PillIcon, ShieldIcon, etc.)
    /layouts                    # Layouts Astro (MainLayout)
    /pages                      # Routes Astro (index, automedication, /es/*)
    /styles                     # SCSS globaux (variables, mixins, reset, composants)
    /i18n                       # Système i18n (ui.ts, utils.ts)
    /test                       # Tests frontend (Vitest + RTL)
    /config.ts                  # Configuration globale (API_BASE_URL)
  /backend                      # <--- ZONE BACKEND
    /api                        # Endpoints FastAPI (routing, validation, rate limiting)
      main.py                   # App FastAPI, CORS, middlewares, routes
      automedication.py         # Endpoint /evaluate (validation → orchestrateur)
      drugs.py                  # Endpoint /search
      flow_endpoint.py          # Endpoint /flow/:id (questions dynamiques)
    /core                       # Couche domaine
      config.py                 # Settings (pydantic-settings BaseSettings)
      models.py                 # Modèles métier (Brand, Substance, Rule, RiskLevel)
      schemas.py                # DTOs Pydantic (SearchResult, EvaluationResponse, etc.)
      limiter.py                # Configuration rate limiting
      i18n.py                   # Service i18n backend (FR/ES)
    /data                       # DB SQLite + medical_knowledge.json
    /services                   # Logique métier
      /automedication           # Module automédication
        orchestrator.py         # Orchestrateur (SRP : coordonne évaluation + IA)
        risk_calculator.py      # Calcul de score (fonctions pures)
        db_repository.py        # DAO SQLite (context managers)
        __init__.py             # Fonction evaluate_risk
      /search                   # Module recherche
        repository.py           # DAO SQLite (SQL LIKE + LIMIT)
        service.py              # Service de recherche
        utils.py                # Normalisation texte
      ai_service.py             # Intégration Google GenAI
    /tests                      # Tests Backend (Pytest)
    /scripts                    # Scripts ETL (import, build_db, extract, etc.)
```

### Principes d'Architecture

1.  **Architecture "Islands" :** Le JS est chargé uniquement pour les composants interactifs (`client:load`).
2.  **Séparation des responsabilités (SRP) :** Les endpoints API valident les entrées et délèguent au service orchestrateur. La logique métier est dans les services.
3.  **Repository Pattern :** Accès DB isolé dans des classes dédiées (`DrugRepository`, `AutomedicationRepository`) avec context managers pour la gestion des connexions.
4.  **Sécurité des Secrets :** Utilisation stricte de fichiers `.env` (jamais commités). `.env.example` documenté.

### Sécurité de l'API

- **CORS :** Origines restreintes via `ALLOWED_ORIGINS` + regex limité au projet (`pharma-tools-*.vercel.app`). Headers autorisés explicites (`Content-Type`, `Accept`, `Accept-Language`).
- **Rate Limiting :** Via `slowapi` — 10 req/min pour l'évaluation, 30 req/min pour la recherche, 60 req/min par défaut.
- **Headers HTTP :** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` sur chaque réponse.
- **Validation des entrées :** Pydantic `Field` avec contraintes (âge 0-150, genre `Literal["M","F"]`, maximum 50 réponses).
- **Documentation API :** `/docs` et `/openapi.json` désactivés en production (`ENV=production`).

### Stratégie de Gestion des Erreurs

- **Frontend :** Messages utilisateur clairs en cas d'échec API. Pas de `dangerouslySetInnerHTML`. Toutes les chaînes via i18n.
- **Backend :** Module `logging` Python avec niveaux. `except Exception` (jamais `bare except`). Aucune stacktrace exposée au client.

## 4. STANDARDS DE DÉVELOPPEMENT

### Qualité de Code

- **Noms de variables :** Anglais explicite (ex: `drugList`).
- **Imports :** Toujours en haut de fichier (jamais inline).
- **Defaults :** Pas d'arguments mutables par défaut (`[] → None`).
- **Sécurité :** Aucune donnée de santé personnelle stockée. Requêtes LLM anonymisées.
- **Principes :** SOLID, KISS, DRY appliqués systématiquement.

### Langues

- **Langue de dev :** Commentaires et logs en FRANÇAIS.
- **Documentation (Livrables) :** Bilingue FRANÇAIS / ESPAGNOL.
- **Interface (i18n) :** Toutes les chaînes UI gérées dans `src/i18n/ui.ts` (FR + ES). Aucune chaîne hardcodée dans les composants React.

### Git & Versionning (Conventional Commits)

- **Format :** `type(scope): description` (ex: `feat(search): ajout input`)
- **Types :** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

### SEO

- **Meta tags :** `<meta description>`, Open Graph (`og:title`, `og:description`, `og:locale`), URL canonique sur chaque page.
- **Headings :** Un seul `<h1>` par page. Hiérarchie de titres respectée.
- **Sémantique :** HTML5 (`<nav>`, `<main>`, `<footer>`, `<header>`).

### Accessibilité (Health First)

- **Standard :** WCAG 2.1 AA.
- **Focus :** Contraste, navigation clavier, sémantique HTML (`<button>` pas `<div>`), attributs `alt`.

### Documentation (Living Documentation)

- **Principe :** Pas de doc obsolète.
- **Fichiers clés :** `CHANGELOG.md` (FR+ES), `AGENTS.md` (FR+ES), `README.md`, Docstrings Python, `DOCUMENTATION.md`.

## 5. STRATÉGIE DE TESTS

**Approche globale : Pyramide de tests — 26 tests automatisés**

1.  **Tests Unitaires & Intégration Frontend (Vitest + React Testing Library)** — 19 tests
    - **Cible :** Composants React (`AutomedicationScore`), utilitaires i18n, parité traductions FR/ES.
    - **Workflow :** TDD (Red-Green-Refactor).

2.  **Tests Backend (Pytest)** — 7 tests
    - **Cible :** API FastAPI (search, flow, evaluate), logique métier (RiskCalculator), service IA (mocking GenAI).
    - **Workflow :** TDD. Mock des appels LLM externes.

3.  **Tests E2E (Playwright)** — À implémenter
    - **Cible :** Pages Astro, flux complet d'automédication.

### Cas critiques à tester

- **Logique métier :** Une automédication dangereuse (ex: AINS + Femme enceinte) DOIT déclencher une alerte.
- **i18n :** Toutes les clés FR doivent exister en ES (test automatisé).
- **UI :** L'interface doit rester utilisable sur mobile.

## 6. INSTRUCTIONS POUR L'AGENT

Tu agis en tant que **Senior Fullstack Developer** et **Docteur en Pharmacie**.

1.  **Workflow TDD+D :**
    - Étape 1 : Propose le Test (RED).
    - Étape 2 : Une fois validé/fail, propose le Code (GREEN).
    - Étape 3 : Propose le Refactor si nécessaire (REFACTOR).
    - Étape 4 : **Check Documentation** -> Demande si on met à jour le CHANGELOG.
2.  **Rigueur :** Si une interaction est incertaine, indique-le.
3.  **Pédagogie :** Explique tes choix simplement.
4.  **Bilinguisme :** Pour chaque fonctionnalité majeure ou instruction d'utilisation, propose une version en Français et sa traduction en Espagnol pour les livrables du TFM.

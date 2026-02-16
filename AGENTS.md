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

### Backend (L'Intelligence - Dossier /backend)

- **API :** Python avec FastAPI.
- **Base de Données :** SQLite (Stockage structuré des médicaments, DCI, Classes et règles du Thésaurus).
- **Sécurité API :** `slowapi` (Rate Limiting), CORS restreint, headers de sécurité HTTP, validation Pydantic stricte.
- **Logging :** Module `logging` Python (remplace `print()`). Niveaux `debug`/`info`/`warning`/`error`.
- **IA / RAG Hybride :**
  - **Moteur :** SDK Google GenAI (`google-genai`).
  - **Modèle :** `gemini-3-flash-preview` (pour la vitesse et les explications pédagogiques).
  - **Flux :** Contexte structuré (questions/réponses) -> Injection dans le prompt -> Génération pédagogique vulgarisée.
  - **Contrainte :** Structured Output souhaité pour les futurs composants.

### Déploiement & DevOps (Infrastructure)

- **Backend (API) :** Containerisé avec **Docker** et hébergé sur **Render** (Web Service).
- **Frontend (Application) :** Déployé sur **Vercel** (Optimisation Astro).
- **CI/CD :** Génération automatique de la base SQLite lors du build Docker à partir des sources JSON (`medical_knowledge.json`).

## 3. ARCHITECTURE DU CODE

### Structure des dossiers (Convention)

/pharma-tools
/src # <--- ZONE FRONTEND
/components
/ui # Composants atomiques (Boutons, Inputs)
/features # Composants métier React
/automedication # AutomedicationContainer, Search, Score, UnifiedQuestionnaire
/global # Composants globaux Astro (Navbar, Footer, MedicalDisclaimer)
/home # Composants page d'accueil (Hero, Features)
/icons # Composants SVG (PillIcon, ShieldIcon, SearchIcon, etc.)
/layouts # Layouts Astro (MainLayout)
/pages # Routes Astro (index, automedication)
/styles # Fichiers SCSS globaux (variables, mixins, reset)
/config.ts # Configuration globale (API_BASE_URL)
/backend # <--- ZONE BACKEND
/api # Endpoints FastAPI (Routing + Rate Limiting)
/core # Modèles de données (Pydantic) et Schémas
/data # DB SQLite (safepills.db), medical_knowledge.json
/services # Logique métier (AI, Recherche)
/automedication # Logique modulaire (Filters, Calculator, Repository)
/tests # Tests Backend (unitaires et intégration)
/scripts # Scripts de migration et d'import (ETL)

### Principes d'Architecture

1.  **Architecture "Islands" :** Le JS est chargé uniquement pour les composants interactifs (`client:load`).
2.  **Séparation des responsabilités :** Frontend (Affichage) vs Backend (Logique métier/IA).
3.  **Sécurité des Secrets :** Utilisation stricte de fichiers `.env` (jamais commités). `.env.example` documenté.

### Sécurité de l'API

- **CORS :** Restreint aux origines autorisées via variable d'environnement `ALLOWED_ORIGINS`.
- **Rate Limiting :** Via `slowapi` — 30 req/min pour la recherche, 60 req/min par défaut, protection contre l'abus des crédits IA.
- **Headers HTTP :** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` sur chaque réponse.
- **Validation des entrées :** Pydantic `Field` avec contraintes (âge 0-150, genre M/F, taille max des réponses).
- **Documentation API :** `/docs` et `/openapi.json` désactivés en production (`ENV=production`).

### Stratégie de Gestion des Erreurs

- **Frontend :** Utilisation de `Error Boundaries` React. Message utilisateur clair en cas d'échec API.
- **Backend :** Module `logging` Python avec niveaux (debug/info/warning/error). Aucune stacktrace exposée au client. Les messages debug sont silencieux en production.

## 4. STANDARDS DE DÉVELOPPEMENT

### Qualité de Code

- **Noms de variables :** Anglais explicite (ex: `drugList`).
- **Sécurité :** Aucune donnée de santé personnelle stockée. Requêtes LLM anonymisées.

### Langues

- **Langue de dev :** Commentaires et logs en FRANÇAIS.
- **Documentation (Livrables) :** Bilingue FRANÇAIS / ESPAGNOL (Dossiers `/docs/fr` et `/docs/es`).
- **Sortie Application :** Format standardisé par l'IA, capable de s'adapter à la langue de l'utilisateur.

### Git & Versionning (Conventional Commits)

- **Format :** `type(scope): description` (ex: `feat(search): ajout input`)
- **Types :** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

### Accessibilité (Health First)

- **Standard :** WCAG 2.1 AA.
- **Focus :** Contraste, navigation clavier, sémantique HTML (`<button>` pas `<div>`), attributs `alt`.

### Documentation (Living Documentation)

- **Principe :** Pas de doc obsolète.
- **Fichiers clés :** `CHANGELOG.md`, `README.md`, Docstrings Python.

## 5. STRATÉGIE DE TESTS (TDD & E2E)

**Approche globale : Pyramide de tests**

1.  **Tests Unitaires & Intégration (Vitest + React Testing Library)**
    - **Cible :** Composants React complexes, Nano Stores, Libs.
    - **Workflow :** TDD obligatoire (Red-Green-Refactor).

2.  **Tests de Bout en Bout / E2E (Playwright)**
    - **Cible :** Pages Astro, Hydratation, Routing, Scénarios complets.
    - **Objectif :** Vérifier que l'utilisateur peut faire une recherche complète.

3.  **Tests Backend (Pytest)**
    - **Cible :** API FastAPI, Logique d'extraction.
    - **Workflow :** TDD. Mock des appels LLM externes.

### Cas critiques à tester

- **Logique métier :** Une automédication dangereuse (ex: AINS + Femme enceinte) DOIT déclencher une alerte.
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

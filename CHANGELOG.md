# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [0.7.0] - 2026-02-21

### 🔍 Audit Complet & Refactoring

Audit exhaustif du projet couvrant sécurité, architecture, principes SOLID/KISS/DRY, maintenabilité et code inutilisé. Passage de **7 à 26 tests automatisés**.

### 🔐 Sécurité

- **CORS renforcé** : Restriction des `allow_headers` (liste explicite au lieu de `*`) et du regex d'origines Vercel (limité au projet `safe-pills-*`).
- **Suppression `dangerouslySetInnerHTML`** : Remplacement dans `AutomedicationScore.tsx` par du JSX sûr avec des clés i18n séparées.
- **Documentation API** : Confirmation que `/docs` et `/openapi.json` sont bien désactivés en production.

### 🏗️ Architecture (SRP & Clean Code)

- **Nouveau `orchestrator.py`** : Extraction de la logique métier de l'endpoint `/evaluate` dans un service orchestrateur dédié. L'endpoint passe de 81 à 41 lignes.
- **`pydantic-settings`** : Migration de `Settings` vers `BaseSettings` pour la validation automatique des variables d'environnement au démarrage.
- **Context managers DB** : Uniformisation de toutes les connexions SQLite dans `db_repository.py` avec `with self._get_connection()`.
- **Recherche optimisée** : Remplacement du filtrage Python O(n) par des requêtes SQL `LIKE` + `LIMIT 20` dans `repository.py`.

### 🗑️ Nettoyage (Code mort supprimé)

- **Fichiers supprimés** : `question_filters.py` (modèle inexistant), `test_insert.py` (script abandonné), `SearchDrug.scss` et `SelectedDrugsList.scss` (SCSS orphelins).
- **Code inline supprimé** : `build_ai_context()` (duplication jamais appelée), alias `compute_risk_score` (jamais importé), 20 lignes CSS commentées dans `_buttons.scss`.

### 📐 Qualité de Code

- **Anti-patterns corrigés** : `bare except` → `except Exception`, `print()` → `logger.error()`, argument mutable par défaut `[] → None`.
- **Imports** : Tous les imports inline déplacés en haut de fichier.
- **Docstrings** : Ajout de docstrings sur les méthodes du repository et de l'orchestrateur.

### 🌍 Internationalisation (i18n)

- **10 nouvelles clés** (FR + ES) : `questionnaire.about`, `.age_label`, `.continue`, `.yes`, `.no`, `score.no_coverage.before/bold`, `seo.description`, `seo.og_title`.
- **Chaînes hardcodées éliminées** : « À propos de », « ans », « Continuer → », « Oui », « Non » remplacées par `t('...')`.

### 🎨 Frontend & SEO

- **Meta SEO** : Ajout de `<meta description>`, Open Graph (`og:title`, `og:description`, `og:locale`), et URL canonique dans `Layout.astro`.
- **Footer** : Suppression des liens morts (`/mentions-legales`, `/confidentialite`, `/cookies`), `<h1>` → `<p>` (WCAG).
- **Props typées** : Interface `Props` ajoutée au composant `Layout.astro`.

### 🧪 Tests (19 nouveaux)

- **`AutomedicationScore.test.tsx`** (10 tests) : Rendu des niveaux de risque, i18n FR/ES, conseils généraux, couverture, explication IA, callback reset.
- **`i18n.test.ts`** (9 tests) : Détection de langue URL, traductions, test de parité automatique FR/ES.
- **Tests backend mis à jour** : Mock path corrigé pour le nouvel orchestrateur.

### 📝 Documentation

- **`AGENTS.md`** et **`AGENTS-ES.md`** : Mise à jour complète (structure, sécurité, tests, standards).
- **`DOCUMENTATION.md`** : Nouvelle documentation détaillée de chaque fichier du projet.

## [0.6.0] - 2026-02-18

### 🧠 Amélioration du Système RAG & IA

- **Base de Connaissances Médicales** : Implémentation d'un système RAG (Retrieval-Augmented Generation) avec `medical_knowledge.json` pour mapper les substances aux conseils validés.
- **Conseils Structurés** : L'IA reçoit désormais des contextes de conseils structurés pour une meilleure précision, réduisant les risques d'hallucination.
- **Affichage des Risques "Verts"** : Les médicaments sans risque identifié affichent maintenant des conseils généraux pertinents au lieu d'une section vide.
- **Logique de Risque** : Affinement de la logique pour s'assurer que toutes les questions de risque pertinentes sont posées.

### 🌐 Internationalisation (i18n) & UX

- **Correction des Traductions** : Résolution des problèmes de questions mélangeant les langues (Français/Espagnol) et amélioration de la génération des prompts.
- **Navigation** : Ajout d'un bouton retour dans le flux du questionnaire pour une meilleure expérience utilisateur.

### 🛠️ Correctifs & Optimisations

- **Résolution de Modules** : Correction des erreurs d'import `@i18n` qui bloquaient la compilation Astro.
- **Nettoyage Backend** : Suppression du code mort dans `automedication_service.py` et des fichiers de tests obsolètes.
- **Performance** : Optimisation du chargement des fichiers JSON et centralisation de la configuration du Rate Limiting.

## [0.5.0] - 2026-02-14

### 🎨 Refonte Frontend (Nouvelle Identité Visuelle)

- **Nouvelle Page d'Accueil** : Refonte complète de `index.astro` avec une architecture modulaire basée sur des composants dédiés (`Hero.astro`, `Features.astro`).
- **Section Hero** : Nouveau composant plein écran avec image SafePills, badge de confiance « FIABILITÉ MÉDICALE », description d'alerte sur l'automédication, et double CTA (Démarrer l'analyse / En savoir plus).
- **Section Features** : Composant « Comment ça marche ? » présentant les 3 étapes (Recherchez, Répondez, Recevez nos conseils) avec des cartes animées au survol.
- **Branding SafePills** : Identité visuelle cohérente avec gradient vert (#3cb56f → #60fca1) sur le titre principal.

### 🧩 Bibliothèque d'Icônes SVG

- **Remplacement des Emojis** : Les emojis (🔍, 📋, ✅, 🏥, 🚀) sont remplacés par des composants SVG Astro réutilisables et stylables.
- **6 Composants Icônes** : Création de `ActivityIcon`, `AlertIcon`, `DocumentIcon`, `PillIcon`, `SearchIcon`, `ShieldIcon` dans `src/components/icons/`.
- **Props Configurables** : Chaque icône accepte une prop `size` pour un dimensionnement flexible.
- **Couleurs via CSS** : Les icônes utilisent `currentColor` et les variables CSS (`--tertiary-color`) pour une cohérence visuelle.

### 🏗️ Nouveaux Composants Globaux

- **Footer** (`Footer.astro`) : Pied de page complet avec logo SafePills (icône PillIcon), liens de navigation (Mentions légales, Confidentialité, Cookies), et copyright dynamique.
- **Avertissement Médical** (`MedicalDisclaimer.astro`) : Bandeau dédié rappelant que l'outil ne remplace pas un avis médical professionnel.
- **Intégration Layout** : Le Footer est désormais intégré au layout global de l'application.

### 🎛️ Système de Design (SCSS)

- **Composant Boutons** (`_buttons.scss`) : Nouveau fichier SCSS réutilisable avec les variantes `.btn-primary`, `.btn-outline`, gestion des états `:hover`, `:active`, `:disabled`, et focus clavier accessible.
- **Styles Globaux** : Ajout du `scroll-behavior: smooth`, styles du logo `#logo` centralisés, et couleur des icônes `.icon` globalisée.
- **Navbar Enrichie** : Intégration de l'icône PillIcon dans le logo, bouton CTA « Testez ! » dans la navigation desktop et mobile.

### 🐛 Corrections & Ajustements

- **Page Automédication** : Correction du padding et de la couleur du titre (`--color-primary` → `--tertiary-color`).
- **Nettoyage** : Suppression de ~170 lignes de styles inline dans `index.astro` au profit de composants modulaires.

## [0.4.0] - 2026-02-07

### 🧠 Intelligence Artificielle & Pédagogie

- **Intégration Gemini 3** : Migration vers le nouveau SDK `google-genai` et utilisation du modèle `gemini-3-flash-preview`.
- **Explications Contextuelles** : L'IA génère désormais une explication vulgarisée et rassurante basée sur le profil du patient et ses réponses au quiz.
- **Prompt Engineering** : Système d'instructions strict pour éviter les hallucinations et s'adapter au profil (âge, genre, grossesse).

### 🏗️ Architecture Backend (Refactoring Modulaire)

- **Découpage du Monolithe** : Transformation du service d'automédication en un module structuré (`backend/services/automedication/`) :
  - `risk_calculator.py` : Calculateur de score agnostique.
  - `db_repository.py` : Couche d'accès aux données (DAO) isolée.
  - `orchestrator.py` : Service d'orchestration (ajouté en v0.7.0).
- **Clean Code** : Séparation stricte de la logique métier (fonctions pures) et des entrées/sorties (IO).

### 🚢 DevOps & Déploiement Cloud

- **Dockerisation** : Création d'une image Docker optimisée pour le backend avec génération automatique de la base SQLite lors du Build.
- **Stratégie Hybride** :
  - Backend déployé sur **Render** (via Docker).
  - Frontend déployé sur **Vercel** (optimisation Astro).
- **Config Dynamique** : Mise en place de `PUBLIC_API_URL` pour une communication fluide entre le front et le back.

### 🧪 Qualité & Fiabilité

- **Renforcement des Tests** : Passage à **21 tests automatisés**.
- **TDD Legacy** : Utilisation de tests de caractérisation pour sécuriser le refactoring du code existant.
- **Validation API** : Tests d'intégration sur les endpoints FastAPI (Mocking LLM & DB).

## [0.3.0] - 2026-02-01

### 🔄 PIVOT MAJEUR : Sécurisation de l'Automédication

**Changement de stratégie** : Le projet abandonne l'objectif initial d'analyse exhaustive des interactions médicamenteuses (trop complexe et onéreux d'obtenir une base de données certifiée et à jour) pour se concentrer sur **l'aide à la décision pour l'automédication**.
L'objectif est désormais de sécuriser la prise de médicaments en accès direct (OTC) via un questionnaire de santé dynamique.

### 🚀 Nouvelles Fonctionnalités

- **Score de Risque Automédication** : Système intelligent modélisant les risques (Grossesse, Problèmes hépatiques, etc.) sous forme de tags et de questions.
- **Quiz Dynamique** : Le frontend génère les questions pertinentes en fonction du médicament sélectionné.
- **Calcul de Score** : Algorithme pur déterminant un niveau de risque (VERT, ORANGE, ROUGE) basé sur les réponses patient.
- **Recherche Simplifiée** : Moteur de recherche focalisé sur les médicaments OTC et substances actives.

### 🏗️ Architecture & Technique (Refonte KISS)

- **Base de Données Minimaliste** :
  - Abandon du schéma complexe `interactions`.
  - Nouvelle structure simplifiée : `drugs`, `substances`, `questions`.
  - Source de vérité : Fichier Excel "Liste-OTC" certifié + BDPM.
- **ETL (Extract Transform Load)** :
  - Nouveau script `forge_data.py` qui croise les données officielles (BDPM) avec la liste des OTC autorisés.
  - Génération d'un référentiel JSON unique et maîtrisable.
- **Qualité de Code (TDD)** :
  - Implémentation du **Test Driven Development** pour la logique critique.
  - Typage fort avec `Enum` (RiskLevel) pour éviter les "magic strings".
  - Séparation stricte : Logique métier (Pure) vs Accès données.

### 🗑️ Suppressions (Cleanup)

- Suppression du moteur d'analyse d'interactions complexe (`interaction_service.py`).
- Suppression des scripts de réparation du PDF ANSM (trop instables).
- Nettoyage des anciennes tables de base de données inutilisées.

## [Unreleased]

### Feat

- Initialisation de l'architecture du projet (Frontend Astro/React, Backend FastAPI).
- Ajout du point d'entrée de l'API FastAPI et de l'endpoint `/health`.
- Mise en place de l'environnement de test Frontend (Vitest).
- Création du composant `SearchDrug` avec tests unitaires (TDD).

### Backend & Data

- Création des modèles de données Pydantic (`Drug`, `Substance`) simplifiés pour les interactions.
- Implémentation du service `drug_loader` pour ingérer les fichiers officiels de la BDPM (ANSM).
- Développement d'un moteur de recherche hybride (Marque + Molécule) avec normalisation des accents.
- Mise en place de tests d'intégration automatisés (Pytest) pour la logique métier et l'API.
- Endpoint `/api/search` fonctionnel pour la recherche de médicaments.

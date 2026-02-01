# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

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

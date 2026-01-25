# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

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

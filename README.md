# <img src="public/images/banner.png" alt="SafePills Banner" width="100%">

<div align="center">

# 💊 SafePills

**Votre compagnon intelligent pour une automédication sécurisée.**  
_Your AI-powered companion for safe self-medication._

[![Version](https://img.shields.io/badge/version-1.0.0-3cb56f.svg)](CHANGELOG.md)
[![Website](https://img.shields.io/badge/Website-Live-brightgreen.svg)](https://safe-pills-ten.vercel.app/)

**[Accéder à l'application 🚀](https://safe-pills-ten.vercel.app/)**

[![Astro](https://img.shields.io/badge/Frontend-Astro%20%2F%20React-darkorchid.svg)](https://astro.build/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/AI-Gemini%20Flash%20RAG-blue.svg)](https://deepmind.google/technologies/gemini/)
[![i18n](https://img.shields.io/badge/i18n-FR%20%7C%20ES-orange.svg)](#internationalisation)

</div>

---

## 🎯 À propos de SafePills

L'automédication est une pratique courante mais non dénuée de risques. **SafePills** est une application web moderne conçue pour aider les utilisateurs à vérifier la compatibilité des médicaments en accès direct (OTC) avec leur profil de santé.

Grâce à une combinaison de **logique algorithmique stricte** et d'**ingénierie RAG (Retrieval-Augmented Generation)** alimentée par l'IA, l'outil fournit des conseils personnalisés, rapides et vulgarisés pour minimiser les risques d'interactions et de contre-indications.

---

## ✨ Fonctionnalités Clés

|     | Fonctionnalité              | Description                                                                                               |
| --- | --------------------------- | --------------------------------------------------------------------------------------------------------- |
| 🔍  | **Recherche Intelligente**  | Moteur de recherche hybride (Marque & Molécule) basé sur les données officielles de la BDPM.              |
| 📋  | **Questionnaire Dynamique** | Génération de questions de santé spécifiques en fonction des substances actives sélectionnées.            |
| ⚖️  | **Score de Risque**         | Évaluation instantanée (Vert, Orange, Rouge) selon les antécédents et le profil patient.                  |
| 🧠  | **Explications par IA**     | Synthèse vulgarisée générée par Gemini Flash, s'appuyant sur une base de connaissances médicale vérifiée. |
| 🌍  | **Bilingue Native**         | Interface et logique médicale intégralement disponibles en **Français** et **Espagnol**.                  |

---

## 🛠️ Stack Technique

### **Frontend**

- **Framework :** [Astro](https://astro.build/) (v5+) pour une performance maximale.
- **UI :** [React](https://reactjs.org/) pour les composants interactifs complexes.
- **Styles :** SCSS modulaire avec un système de design personnalisé.
- **State Management :** Nano Stores (ultra-léger).

### **Backend**

- **Framework :** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+).
- **Base de données :** SQLite (léger et portable).
- **Validation :** Pydantic v2.
- **IA :** Google Generative AI (SDK Gemini) avec orchestration RAG.

---

## 🚀 Démarrage Rapide

### 1. Prérequis

- Node.js (v20+)
- Python (3.12+)

### 2. Installation du Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configurez votre GEMINI_API_KEY
uvicorn api.main:app --reload
```

### 3. Installation du Frontend

```bash
npm install
npm run dev
```

L'application sera accessible sur `http://localhost:4321`.

---

## 📁 Structure du Projet

```text
├── backend/                # API FastAPI & Logique métier
│   ├── api/                # Endpoints & Middlewares
│   ├── services/           # Orchestrateur, IA & Calcul de risque
│   ├── repository/         # Accès aux données SQLite
│   └── data/               # Scripts ETL & JSON sources
├── src/                    # Code source Frontend (Astro)
│   ├── components/         # Composants React & Astro
│   ├── layouts/            # Templates de pages
│   ├── pages/              # Routes (index, automedication...)
│   └── styles/             # Fichiers SCSS globaux & variables
├── public/                 # Assets statiques (images, icons)
└── CHANGELOG.md            # Historique des versions
```

---

## 🛡️ Avertissement Légal

**SafePills est un outil d'aide à la décision et ne remplace en aucun cas l'avis d'un professionnel de santé (médecin ou pharmacien).** En cas de doute, consultez toujours un professionnel avant de prendre un médicament.

---

<div align="center">
  <sub>Propulsé par <b>DeepMind Gemini</b>. Développé avec ❤️ pour la santé de tous.</sub>
</div>

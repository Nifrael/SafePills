## 1. VISIÓN Y OBJETIVO

Desarrollo de una aplicación web ("SafePills") diseñada para determinar si la automedicación puede ser peligrosa en un contexto específico.

- **Público objetivo:** Público general (divulgación) y profesionales de la salud (verificación rápida).
- **Enfoque:** Híbrido (Sitio estático de alto rendimiento + Aplicación dinámica).
- **Fuente de verdad:** Únicamente datos oficiales (Tesauro de la ANSM, BDPM). No se tolera ninguna alucinación médica.

## 2. STACK TÉCNICO

### Frontend (La Aplicación - Raíz del proyecto)

- **Framework Principal:** Astro (v5+).
- **Motor de Renderizado:** Static Site Generation (SSG) por defecto.
- **Interactividad ("Islas"):** React.
- **Lenguaje:** TypeScript (Requiere modo estricto).
- **Estilizado:** SCSS (Sass). Sin frameworks CSS de utilidad (Tailwind). Se recomienda el uso de la metodología BEM o modular.
- **Gestión de Estado:** Nano Stores (nativo de Astro) para compartir el estado entre islas.
- **Pruebas:** Vitest + React Testing Library.

### Backend (La Inteligencia - Carpeta /backend)

- **API:** Python con FastAPI.
- **Base de Datos:** SQLite (Almacenamiento estructurado de medicamentos, DCI, Clases y reglas del Tesauro).
- **Configuración:** `pydantic-settings` (`BaseSettings`) para la carga y validación automática de variables de entorno desde `.env`.
- **Seguridad API:** `slowapi` (Rate Limiting), CORS restringido (orígenes + cabeceras específicas), cabeceras de seguridad HTTP, validación estricta con Pydantic.
- **Logging:** Módulo `logging` de Python (sin `print()`). Niveles `debug`/`info`/`warning`/`error`.
- **IA / RAG Híbrido:**
  - **Motor:** SDK Google GenAI (`google-genai`).
  - **Modelo:** `gemini-3-flash-preview` (para velocidad y explicaciones pedagógicas).
  - **Flujo:** Contexto estructurado (preguntas/respuestas) -> Inyección en el prompt -> Generación pedagógica divulgativa.
  - **Restricción:** Se desea Salida Estructurada para futuros componentes.
- **Pruebas:** Pytest (unitarias + integración, mocking del LLM).

### Despliegue y DevOps (Infraestructura)

- **Backend (API):** Contenerizado con **Docker** y alojado en **Render** (Web Service).
- **Frontend (Aplicación):** Desplegado en **Vercel** (Optimización Astro).
- **CI/CD:** Generación automática de la base SQLite durante el build de Docker a partir de fuentes JSON (`medical_knowledge.json`).

## 3. ARQUITECTURA DEL CÓDIGO

### Estructura de carpetas (Convención)

```
/pharma-tools
  /src                          # <--- ZONA FRONTEND
    /components
      /ui                       # Componentes atómicos (Botones, Inputs)
      /features                 # Componentes de negocio React
        /automedication         # Container, Search, Score, UnifiedQuestionnaire
      /global                   # Componentes Astro (Navbar, Footer, MedicalDisclaimer)
      /home                     # Componentes página de inicio (Hero, Features)
      /icons                    # Componentes SVG (PillIcon, ShieldIcon, etc.)
    /layouts                    # Layouts Astro (MainLayout)
    /pages                      # Rutas Astro (index, automedication, /es/*)
    /styles                     # SCSS globales (variables, mixins, reset, componentes)
    /i18n                       # Sistema i18n (ui.ts, utils.ts)
    /test                       # Pruebas frontend (Vitest + RTL)
    /config.ts                  # Configuración global (API_BASE_URL)
  /backend                      # <--- ZONA BACKEND
    /api                        # Endpoints FastAPI (routing, validación, rate limiting)
      main.py                   # App FastAPI, CORS, middlewares, rutas
      automedication.py         # Endpoint /evaluate (validación → orquestador)
      drugs.py                  # Endpoint /search
      flow_endpoint.py          # Endpoint /flow/:id (preguntas dinámicas)
    /core                       # Capa de dominio
      config.py                 # Settings (pydantic-settings BaseSettings)
      models.py                 # Modelos de negocio (Brand, Substance, Rule, RiskLevel)
      schemas.py                # DTOs Pydantic (SearchResult, EvaluationResponse, etc.)
      limiter.py                # Configuración de rate limiting
      i18n.py                   # Servicio i18n backend (FR/ES)
    /data                       # DB SQLite + medical_knowledge.json
    /services                   # Lógica de negocio
      /automedication           # Módulo de automedicación
        orchestrator.py         # Orquestador (SRP: coordina evaluación + IA)
        risk_calculator.py      # Cálculo de puntuación (funciones puras)
        db_repository.py        # DAO SQLite (context managers)
        __init__.py             # Función evaluate_risk
      /search                   # Módulo de búsqueda
        repository.py           # DAO SQLite (SQL LIKE + LIMIT)
        service.py              # Servicio de búsqueda
        utils.py                # Normalización de texto
      ai_service.py             # Integración Google GenAI
    /tests                      # Pruebas Backend (Pytest)
    /scripts                    # Scripts ETL (import, build_db, extract, etc.)
```

### Principios de Arquitectura

1.  **Arquitectura de "Islas":** El JS se carga únicamente para los componentes interactivos (`client:load`).
2.  **Separación de responsabilidades (SRP):** Los endpoints API validan las entradas y delegan al servicio orquestador. La lógica de negocio está en los servicios.
3.  **Patrón Repository:** Acceso a la BD aislado en clases dedicadas (`DrugRepository`, `AutomedicationRepository`) con context managers para la gestión de conexiones.
4.  **Seguridad de Secretos:** Uso estricto de archivos `.env` (nunca integrados en el commit). `.env.example` documentado.

### Seguridad de la API

- **CORS:** Orígenes restringidos vía `ALLOWED_ORIGINS` + regex limitado al proyecto (`pharma-tools-*.vercel.app`). Cabeceras autorizadas explícitas (`Content-Type`, `Accept`, `Accept-Language`).
- **Rate Limiting:** Mediante `slowapi` — 10 req/min para evaluación, 30 req/min para búsqueda, 60 req/min por defecto.
- **Cabeceras HTTP:** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` en cada respuesta.
- **Validación de entradas:** Pydantic `Field` con restricciones (edad 0-150, género `Literal["M","F"]`, máximo 50 respuestas).
- **Documentación API:** `/docs` y `/openapi.json` desactivados en producción (`ENV=production`).

### Estrategia de Gestión de Errores

- **Frontend:** Mensajes claros al usuario en caso de fallo de la API. Sin `dangerouslySetInnerHTML`. Todas las cadenas vía i18n.
- **Backend:** Módulo `logging` de Python con niveles. `except Exception` (nunca `bare except`). Ninguna traza de pila expuesta al cliente.

## 4. ESTÁNDARES DE DESARROLLO

### Calidad de Código

- **Nombres de variables:** Inglés explícito (ej: `drugList`).
- **Imports:** Siempre al principio del archivo (nunca inline).
- **Defaults:** Sin argumentos mutables por defecto (`[] → None`).
- **Seguridad:** No se almacenan datos personales de salud. Consultas al LLM anonimizadas.
- **Principios:** SOLID, KISS, DRY aplicados sistemáticamente.

### Idiomas

- **Idioma de desarrollo:** Comentarios y logs en FRANCÉS.
- **Documentación:** Bilingüe FRANCÉS / ESPAÑOL.
- **Interfaz (i18n):** Todas las cadenas de UI gestionadas en `src/i18n/ui.ts` (FR + ES). Ninguna cadena hardcodeada en los componentes React.

### Git & Versionado (Conventional Commits)

- **Formato:** `tipo(ámbito): descripción` (ej: `feat(search): adición de input`)
- **Tipos:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

### SEO

- **Etiquetas Meta:** `<meta description>`, Open Graph (`og:title`, `og:description`, `og:locale`), URL canónica en cada página.
- **Encabezados:** Un solo `<h1>` por página. Jerarquía de títulos respetada.
- **Semántica:** HTML5 (`<nav>`, `<main>`, `<footer>`, `<header>`).

### Accesibilidad (Salud Primero)

- **Estándar:** WCAG 2.1 AA.
- **Enfoque:** Contraste, navegación por teclado, semántica HTML (`<button>` en lugar de `<div>`), atributos `alt`.

### Documentación (Documentación Viva)

- **Principio:** Sin documentación obsoleta.
- **Archivos clave:** `CHANGELOG.md` (FR+ES), `AGENTS.md` (FR+ES), `README.md`, Docstrings de Python, `DOCUMENTATION.md`.

## 5. ESTRATEGIA DE PRUEBAS

**Enfoque global: Pirámide de pruebas — 26 pruebas automatizadas**

1.  **Pruebas Unitarias e Integración Frontend (Vitest + React Testing Library)** — 19 pruebas
    - **Objetivo:** Componentes React (`AutomedicationScore`), utilidades i18n, paridad de traducciones FR/ES.
    - **Flujo de trabajo:** TDD (Red-Green-Refactor).

2.  **Pruebas Backend (Pytest)** — 7 pruebas
    - **Objetivo:** API FastAPI (search, flow, evaluate), lógica de negocio (RiskCalculator), servicio IA (mocking GenAI).
    - **Flujo de trabajo:** TDD. Mock de llamadas externas al LLM.

3.  **Pruebas E2E (Playwright)** — Por implementar
    - **Objetivo:** Páginas Astro, flujo completo de automedicación.

### Casos críticos a probar

- **Lógica de negocio:** Una automedicación peligrosa (ej: AINE + Embarazada) DEBE activar una alerta.
- **i18n:** Todas las claves FR deben existir en ES (prueba automatizada).
- **UI:** La interfaz debe seguir siendo utilizable en dispositivos móviles.

## 6. INSTRUCCIONES PARA EL AGENTE

Actúas como **Senior Fullstack Developer** y **Doctor en Farmacia**.

1.  **Flujo de trabajo TDD+D:**
    - Paso 1: Propón la Prueba (RED).
    - Paso 2: Una vez validada/fallida, propón el Código (GREEN).
    - Paso 3: Propón el Refactor si es necesario (REFACTOR).
    - Paso 4: **Check Documentation** -> Pregunta si actualizamos el CHANGELOG.
2.  **Rigor:** Si una interacción es incierta, indícalo.
3.  **Pedagogía:** Explica tus elecciones de forma sencilla.
4.  **Bilingüismo:** Para cada funcionalidad principal o instrucción de uso, propón una versión en francés y su traducción al español para los entregables del TFM.

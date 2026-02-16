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

### Backend (La Inteligencia - Carpeta /backend)

- **API:** Python con FastAPI.
- **Base de Datos:** SQLite (Almacenamiento estructurado de medicamentos, DCI, Clases y reglas del Tesauro).
- **Seguridad API:** `slowapi` (Rate Limiting), CORS restringido, cabeceras de seguridad HTTP, validación estricta con Pydantic.
- **Logging:** Módulo `logging` de Python (reemplaza `print()`). Niveles `debug`/`info`/`warning`/`error`.
- **IA / RAG Híbrido:**
  - **Motor:** SDK Google GenAI (`google-genai`).
  - **Modelo:** `gemini-3-flash-preview` (para velocidad y explicaciones pedagógicas).
  - **Flujo:** Contexto estructurado (preguntas/respuestas) -> Inyección en el prompt -> Generación pedagógica divulgativa.
  - **Restricción:** Se desea Salida Estructurada para futuros componentes.

### Despliegue y DevOps (Infraestructura)

- **Backend (API):** Contenerizado con **Docker** y alojado en **Render** (Web Service).
- **Frontend (Aplicación):** Desplegado en **Vercel** (Optimización Astro).
- **CI/CD:** Generación automática de la base SQLite durante el build de Docker a partir de fuentes JSON (`medical_knowledge.json`).

## 3. ARQUITECTURA DEL CÓDIGO

### Estructura de carpetas (Convención)

/pharma-tools
/src # <--- ZONA FRONTEND
/components
/ui # Componentes atómicos (Botones, Inputs)
/features # Componentes de negocio React
/automedication # AutomedicationContainer, Search, Score, UnifiedQuestionnaire
/global # Componentes globales Astro (Navbar, Footer, MedicalDisclaimer)
/home # Componentes página de inicio (Hero, Features)
/icons # Componentes SVG (PillIcon, ShieldIcon, SearchIcon, etc.)
/layouts # Layouts Astro (MainLayout)
/pages # Rutas Astro (index, automedication)
/styles # Archivos SCSS globales (variables, mixins, reset)
/config.ts # Configuración global (API_BASE_URL)
/backend # <--- ZONA BACKEND
/api # Endpoints FastAPI (Routing + Rate Limiting)
/core # Modelos de datos (Pydantic) y Esquemas
/data # DB SQLite (safepills.db), medical_knowledge.json
/services # Lógica de negocio (AI, Búsqueda)
/automedication # Lógica modular (Filtros, Calculadora, Repositorio)
/tests # Pruebas Backend (unitarias e integración)
/scripts # Scripts de migración e importación (ETL)

### Principios de Arquitectura

1.  **Arquitectura de "Islas":** El JS se carga únicamente para los componentes interactivos (`client:load`).
2.  **Separación de responsabilidades:** Frontend (Visualización) vs Backend (Lógica de negocio/IA).
3.  **Seguridad de Secretos:** Uso estricto de archivos `.env` (nunca integrados en el commit). `.env.example` documentado.

### Seguridad de la API

- **CORS:** Restringido a orígenes autorizados mediante la variable de entorno `ALLOWED_ORIGINS`.
- **Rate Limiting:** Mediante `slowapi` — 30 req/min para búsqueda, 60 req/min por defecto, protección contra el abuso de créditos IA.
- **Cabeceras HTTP:** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` en cada respuesta.
- **Validación de entradas:** Pydantic `Field` con restricciones (edad 0-150, género M/F, tamaño máximo de respuestas).
- **Documentación API:** `/docs` y `/openapi.json` desactivados en producción (`ENV=production`).

### Estrategia de Gestión de Errores

- **Frontend:** Uso de `Error Boundaries` de React. Mensaje de usuario claro en caso de fallo de la API.
- **Backend:** Módulo `logging` de Python con niveles (debug/info/warning/error). Ninguna traza de pila expuesta al cliente. Los mensajes debug son silenciosos en producción.

## 4. ESTÁNDARES DE DESARROLLO

### Calidad de Código

- **Nombres de variables:** Inglés explícito (ej: `drugList`).
- **Seguridad:** No se almacenan datos personales de salud. Consultas al LLM anonimizadas.

### Idiomas

- **Idioma de desarrollo:** Comentarios y logs en FRANCÉS.
- **Documentación:** Bilingüe FRANCÉS / ESPAÑOL (Carpetas `/docs/fr` y `/docs/es`).
- **Salida de la Aplicación:** Formato estandarizado por la IA, capaz de adaptarse al idioma del usuario.

### Git & Versionado (Conventional Commits)

- **Formato:** `tipo(ámbito): descripción` (ej: `feat(search): adición de input`)
- **Tipos:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

### Accesibilidad (Salud Primero)

- **Estándar:** WCAG 2.1 AA.
- **Enfoque:** Contraste, navegación por teclado, semántica HTML (`<button>` en lugar de `<div>`), atributos `alt`.

### Documentación (Documentación Viva)

- **Principio:** Sin documentación obsoleta.
- **Archivos clave:** `CHANGELOG.md`, `README.md`, Docstrings de Python.

## 5. ESTRATEGIA DE PRUEBAS (TDD & E2E)

**Enfoque global: Pirámide de pruebas**

1.  **Pruebas Unitarias e Integración (Vitest + React Testing Library)**
    - **Objetivo:** Componentes React complejos, Nano Stores, Libs.
    - **Flujo de trabajo:** TDD obligatorio (Red-Green-Refactor).

2.  **Pruebas de Extremo a Extremo / E2E (Playwright)**
    - **Objetivo:** Páginas Astro, Hidratación, Enrutamiento, Escenarios completos.
    - **Objetivo:** Verificar que el usuario puede realizar una búsqueda completa.

3.  **Pruebas Backend (Pytest)**
    - **Objetivo:** API FastAPI, lógica de extracción.
    - **Flujo de trabajo:** TDD. Mock de llamadas externas al LLM.

### Casos críticos a probar

- **Lógica de negocio:** Una automedicación peligrosa (ej: AINE + Embarazada) DEBE activar una alerta.
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

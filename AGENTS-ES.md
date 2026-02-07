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
/features # Componentes de negocio (React: SearchDrug, InteractionList)
/layouts # Layouts Astro (MainLayout)
/pages # Rutas Astro (index, about, checker)
/styles # Archivos SCSS globales (variables, mixins, reset)
/lib # Lógica compartida Frontend, helpers TS
/backend # <--- ZONA BACKEND
/api # Endpoints FastAPI (Routing)
/core # Modelos de datos (Pydantic) y Esquemas
/data # DB SQLite (safepills.db) y fuentes JSON
/services # Lógica de negocio (AI, Búsqueda)
/automedication # Lógica modular (Filtros, Calculadora, Repositorio)
/tests # Pruebas Backend (unitarias e integración)
/scripts # Scripts de migración e importación (ETL)

### Principios de Arquitectura

1.  **Arquitectura de "Islas":** El JS se carga únicamente para los componentes interactivos (`client:load`).
2.  **Separación de responsabilidades:** Frontend (Visualización) vs Backend (Lógica de negocio/IA).
3.  **Seguridad de Secretos:** Uso estricto de archivos `.env` (nunca integrados en el commit).

### Estrategia de Gestión de Errores

- **Frontend:** Uso de `Error Boundaries` de React. Mensaje de usuario claro en caso de fallo de la API.
- **Backend:** Gestión de excepciones tipificadas. Ninguna traza de pila (stacktrace) expuesta al cliente.

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

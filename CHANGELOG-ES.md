# Registro de Cambios (Changelog)

Todos los cambios notables de este proyecto se documentarán en este archivo.

## [0.5.0] - 2026-02-14

### 🎨 Rediseño Frontend (Nueva Identidad Visual)

- **Nueva Página de Inicio**: Rediseño completo de `index.astro` con una arquitectura modular basada en componentes dedicados (`Hero.astro`, `Features.astro`).
- **Sección Hero**: Nuevo componente a pantalla completa con imagen SafePills, insignia de confianza « FIABILIDAD MÉDICA », descripción de alerta sobre la automedicación, y doble CTA (Iniciar el análisis / Más información).
- **Sección Features**: Componente « ¿Cómo funciona? » que presenta los 3 pasos (Busque, Responda, Reciba nuestros consejos) con tarjetas animadas al pasar el cursor.
- **Branding SafePills**: Identidad visual coherente con degradado verde (#3cb56f → #60fca1) en el título principal.

### 🧩 Biblioteca de Iconos SVG

- **Sustitución de Emojis**: Los emojis (🔍, 📋, ✅, 🏥, 🚀) se reemplazan por componentes SVG Astro reutilizables y estilizables.
- **6 Componentes de Iconos**: Creación de `ActivityIcon`, `AlertIcon`, `DocumentIcon`, `PillIcon`, `SearchIcon`, `ShieldIcon` en `src/components/icons/`.
- **Props Configurables**: Cada icono acepta una prop `size` para un dimensionamiento flexible.
- **Colores vía CSS**: Los iconos utilizan `currentColor` y las variables CSS (`--tertiary-color`) para una coherencia visual.

### 🏗️ Nuevos Componentes Globales

- **Footer** (`Footer.astro`): Pie de página completo con logo SafePills (icono PillIcon), enlaces de navegación (Aviso legal, Privacidad, Cookies) y copyright dinámico.
- **Aviso Médico** (`MedicalDisclaimer.astro`): Banner dedicado que recuerda que la herramienta no sustituye una opinión médica profesional.
- **Integración en el Layout**: El Footer está ahora integrado en el layout global de la aplicación.

### 🎛️ Sistema de Diseño (SCSS)

- **Componente de Botones** (`_buttons.scss`): Nuevo archivo SCSS reutilizable con las variantes `.btn-primary`, `.btn-outline`, gestión de estados `:hover`, `:active`, `:disabled`, y foco de teclado accesible.
- **Estilos Globales**: Adición de `scroll-behavior: smooth`, estilos del logo `#logo` centralizados, y color de iconos `.icon` globalizado.
- **Navbar Mejorada**: Integración del icono PillIcon en el logo, botón CTA « ¡Pruébalo! » en la navegación de escritorio y móvil.

### 🐛 Correcciones y Ajustes

- **Página de Automedicación**: Corrección del padding y del color del título (`--color-primary` → `--tertiary-color`).
- **Limpieza**: Eliminación de ~170 líneas de estilos inline en `index.astro` a favor de componentes modulares.

## [0.4.0] - 2026-02-07

### 🧠 Inteligencia Artificial y Pedagogía

- **Integración de Gemini 3**: Migración al nuevo SDK `google-genai` y uso del modelo `gemini-3-flash-preview`.
- **Explicaciones Contextuales**: La IA genera ahora una explicación divulgativa y tranquilizadora basada en el perfil del paciente y sus respuestas al cuestionario.
- **Ingeniería de Prompts**: Sistema de instrucciones estricto para evitar alucinaciones y adaptarse al perfil (edad, género, embarazo).

### 🏗️ Arquitectura Backend (Refactorización Modular)

- **Descomposición del Monolito**: Transformación del servicio de automedicación en un módulo estructurado (`backend/services/automedication/`):
  - `question_filters.py`: Lógica pura de filtrado (edad, género, vía).
  - `risk_calculator.py`: Calculadora de puntuación agnóstica.
  - `db_repository.py`: Capa de acceso a datos (DAO) aislada.
- **Código Limpio (Clean Code)**: Separación estricta de la lógica de negocio (funciones puras) y las entradas/salidas (IO).

### 🚢 DevOps y Despliegue en la Nube

- **Dockerización**: Creación de una imagen Docker optimizada para el backend con generación automática de la base SQLite durante la construcción (Build).
- **Estrategia Híbrida**:
  - Backend desplegado en **Render** (vía Docker).
  - Frontend desplegado en **Vercel** (optimización para Astro).
- **Configuración Dinámica**: Implementación de `PUBLIC_API_URL` para una comunicación fluida entre el front y el back.

### 🧪 Calidad y Fiabilidad

- **Refuerzo de Pruebas**: Incremento a **21 pruebas automatizadas**.
- **TDD de Legado**: Uso de pruebas de caracterización para asegurar la refactorización del código existente.
- **Validación de la API**: Pruebas de integración en los endpoints de FastAPI (Mocking de LLM y DB).

## [0.3.0] - 2026-02-01

### 🔄 PIVOTE MAYOR: Aseguramiento de la Automedicación

**Cambio de estrategia**: El proyecto abandona el objetivo inicial de análisis exhaustivo de interacciones medicamentosas (demasiado complejo y costoso obtener una base de datos certificada y actualizada) para centrarse en el **apoyo a la toma de decisiones para la automedicación**.
El objetivo es ahora asegurar la toma de medicamentos de acceso directo (OTC) a través de un cuestionario de salud dinámico.

### 🚀 Nuevas Funcionalidades

- **Puntuación de Riesgo de Automedicación**: Sistema inteligente que modela los riesgos (Embarazo, Problemas hepáticos, etc.) en forma de etiquetas y preguntas.
- **Cuestionario Dinámico**: El frontend genera las preguntas pertinentes en función del medicamento seleccionado.
- **Cálculo de Puntuación**: Algoritmo puro que determina un nivel de riesgo (VERDE, NARANJA, ROJO) basado en las respuestas del paciente.
- **Búsqueda Simplificada**: Motor de búsqueda centrado en medicamentos OTC y sustancias activas.

### 🏗️ Arquitectura y Técnica (Rediseño KISS)

- **Base de Datos Minimalista**:
  - Abandono del esquema complejo de `interactions`.
  - Nueva estructura simplificada: `drugs`, `substances`, `questions`.
  - Fuente de verdad: Archivo Excel "Liste-OTC" certificado + BDPM.
- **ETL (Extract Transform Load)**:
  - Nuevo script `forge_data.py` que cruza los datos oficiales (BDPM) con la lista de OTC autorizados.
  - Generación de un repositorio JSON único y controlable.
- **Calidad de Código (TDD)**:
  - Implementación de **Test Driven Development** para la lógica crítica.
  - Tipado fuerte con `Enum` (RiskLevel) para evitar "strings mágicos".
  - Separación estricta: Lógica de negocio (Pura) vs. Acceso a datos.

### 🗑️ Eliminaciones (Limpieza)

- Eliminación del motor de análisis de interacciones complejo (`interaction_service.py`).
- Eliminación de scripts de reparación de PDF de la ANSM (demasiado inestables).
- Limpieza de tablas antiguas de la base de datos no utilizadas.

## [Desarrollo]

### Funcionalidades

- Inicialización de la arquitectura del proyecto (Frontend Astro/React, Backend FastAPI).
- Adición del punto de entrada de la API FastAPI y del endpoint `/health`.
- Implementación del entorno de pruebas Frontend (Vitest).
- Creación del componente `SearchDrug` con pruebas unitarias (TDD).

### Backend y Datos

- Creación de modelos de datos Pydantic (`Drug`, `Substance`) simplificados para las interacciones.
- Implementación del servicio `drug_loader` para ingerir archivos oficiales de la BDPM (ANSM).
- Desarrollo de un motor de búsqueda híbrido (Marca + Molécula) con normalización de acentos.
- Implementación de pruebas de integración automatizadas (Pytest) para la lógica de negocio y la API.
- Endpoint `/api/search` funcional para la búsqueda de medicamentos.

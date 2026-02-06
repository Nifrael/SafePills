/**
 * Configuration globale de l'application
 */

// URL de base de l'API Backend
// En local: http://127.0.0.1:8000
// En production: Utilise la variable d'environnement PUBLIC_API_URL
export const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://127.0.0.1:8000';

/**
 * Tests unitaires pour les utilitaires i18n.
 * Vérifie le bon fonctionnement de la détection de langue et des traductions.
 */
import { describe, it, expect } from 'vitest';
import { getLangFromUrl, useTranslations } from '../i18n/utils';
import { ui, defaultLang } from '../i18n/ui';

describe('getLangFromUrl', () => {
  it('retourne "fr" pour la racine /', () => {
    const url = new URL('http://localhost/');
    expect(getLangFromUrl(url)).toBe('fr');
  });

  it('retourne "es" pour /es/', () => {
    const url = new URL('http://localhost/es/');
    expect(getLangFromUrl(url)).toBe('es');
  });

  it('retourne "es" pour /es/automedication', () => {
    const url = new URL('http://localhost/es/automedication');
    expect(getLangFromUrl(url)).toBe('es');
  });

  it('retourne "fr" (défaut) pour une langue inconnue /de/', () => {
    const url = new URL('http://localhost/de/');
    expect(getLangFromUrl(url)).toBe('fr');
  });

  it('retourne "fr" pour /automedication (pas de préfixe de langue)', () => {
    const url = new URL('http://localhost/automedication');
    expect(getLangFromUrl(url)).toBe('fr');
  });
});

describe('useTranslations', () => {
  it('retourne la traduction FR correcte', () => {
    const t = useTranslations('fr');
    expect(t('nav.home')).toBe('Accueil');
  });

  it('retourne la traduction ES correcte', () => {
    const t = useTranslations('es');
    expect(t('nav.home')).toBe('Inicio');
  });

  it('les clés i18n FR et ES ont le même nombre de clés', () => {
    const frKeys = Object.keys(ui.fr);
    const esKeys = Object.keys(ui.es);
    expect(frKeys.length).toBe(esKeys.length);
  });

  it('toutes les clés FR existent aussi en ES', () => {
    const frKeys = Object.keys(ui.fr);
    const esKeys = Object.keys(ui.es);
    
    const missingInEs = frKeys.filter(key => !esKeys.includes(key));
    expect(missingInEs).toEqual([]);
  });
});

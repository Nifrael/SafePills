/// <reference types="vitest" />
import { getViteConfig } from 'astro/config';

export default getViteConfig({
  test: {
    // Vitest configuration options
    environment: 'jsdom',
    globals: true, // Allows using describe, it, expect without importing
    setupFiles: ['./src/test/setup.ts'],
  },
});

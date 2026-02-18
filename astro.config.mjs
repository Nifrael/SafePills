import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
  integrations: [react()],
  i18n: {
    defaultLocale: "fr",
    locales: ["fr", "es"],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});

// ADK Viewer: reads harness runs (git history, results on disk, a running sandbox). See ARCHITECTURE.md.
export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',
  ssr: false,
  devtools: { enabled: false },
  modules: ['vuetify-nuxt-module', '@nuxt/eslint'],
  vuetify: {
    vuetifyOptions: './vuetify.config.ts',
  },
  devServer: { host: '127.0.0.1', port: 3000 },
  typescript: { strict: true },
  // NUXT_PUBLIC_DEPLOYED=true at `nuxt generate` builds the deployed viewer (§13): history from the snapshot, no live view.
  runtimeConfig: { public: { deployed: false } },
  app: {
    head: { title: 'ADK Viewer', htmlAttrs: { lang: 'pl' } },
  },
})

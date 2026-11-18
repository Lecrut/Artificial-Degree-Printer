// Read-only viewer of harness runs. It reads run folders from disk (VIEWER_RUN_ROOTS) and never imports adk.
export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',
  ssr: false,
  devtools: { enabled: false },
  css: ['~/assets/main.css'],
  app: {
    head: {
      title: 'ADK Viewer',
      htmlAttrs: { lang: 'pl' },
    },
  },
})

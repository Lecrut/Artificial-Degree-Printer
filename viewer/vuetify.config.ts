import { defineVuetifyConfiguration } from 'vuetify-nuxt-module/custom-configuration'

// One dark theme: deep navy surfaces and a vivid emerald accent that cuts through them; semantic colors tuned for navy.
export default defineVuetifyConfiguration({
  theme: {
    defaultTheme: 'adk',
    themes: {
      adk: {
        dark: true,
        colors: {
          'background': '#050b1c',
          'surface': '#0a1430',
          'surface-bright': '#11204a',
          'surface-light': '#11204a',
          'surface-variant': '#1b2d5c',
          'on-surface-variant': '#c8d4f0',
          'primary': '#14c784',
          'secondary': '#3f8cff',
          'success': '#22c55e',
          'error': '#ff6b6b',
          'warning': '#f5b544',
          'info': '#4fa3ff',
        },
        variables: {
          'border-color': '#7f95c9',
          'border-opacity': 0.14,
          'high-emphasis-opacity': 0.94,
          'medium-emphasis-opacity': 0.66,
        },
      },
    },
  },
  icons: {
    defaultSet: 'mdi-svg',
  },
  // Vuetify's own texts (tables, pagination, loading, date picker) in Polish, like the rest of the interface.
  locale: { locale: 'pl', fallback: 'en' },
  localeMessages: ['pl', 'en'],
  defaults: {
    VAppBar: { flat: true, color: 'surface' },
    VCard: { variant: 'flat', rounded: 'xl', border: true },
    VSheet: { rounded: 'xl' },
    VChip: { size: 'small', variant: 'tonal', rounded: 'pill' },
    VBtn: { rounded: 'pill' },
    VBtnToggle: { rounded: 'pill' },
    VBtnGroup: { rounded: 'pill' },
    VAlert: { rounded: 'xl' },
    VAvatar: { rounded: 'xl' },
    VTimeline: { density: 'compact' },
    VTextField: { variant: 'solo-filled', flat: true, density: 'compact', rounded: 'pill' },
    VSelect: { variant: 'solo-filled', flat: true, density: 'compact', rounded: 'pill' },
    VDateInput: { variant: 'solo-filled', flat: true, density: 'compact', rounded: 'pill' },
    VExpansionPanels: { rounded: 'xl' },
    VExpansionPanel: { rounded: 'xl' },
    VDataTable: { density: 'comfortable', hover: true },
    VTabs: { rounded: 'pill' },
    VProgressLinear: { rounded: true },

  },
})

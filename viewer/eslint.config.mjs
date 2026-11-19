import withNuxt from './.nuxt/eslint.config.mjs'

// No custom CSS anywhere (ARCHITECTURE.md §3.1): look comes from Vuetify components, props and utility classes.
export default withNuxt({
  rules: {
    'vue/no-restricted-block': ['error', 'style'],
    'vue/no-restricted-static-attribute': ['error', 'style'],
    'vue/no-restricted-v-bind': ['error', 'style'],
    'max-lines': ['error', { max: 160, skipBlankLines: true, skipComments: true }],
    'max-lines-per-function': ['warn', { max: 40, skipBlankLines: true, skipComments: true }],
  },
}, {
  files: ['**/*.test.ts'],
  rules: { 'max-lines-per-function': 'off' },
})

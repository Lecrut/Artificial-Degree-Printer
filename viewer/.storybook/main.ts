import type { StorybookConfig } from '@storybook-vue/nuxt'

// Storybook boots the real Nuxt app (Vuetify module, auto-imports), so components render exactly as in the viewer.
const config: StorybookConfig = {
  stories: ['../stories/**/*.stories.ts'],
  addons: ['@storybook/addon-docs'],
  framework: { name: '@storybook-vue/nuxt', options: {} },
}

export default config

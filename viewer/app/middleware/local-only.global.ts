import { LOCAL_ONLY } from '~/utils/nav'

// The deployed viewer has no live view and no launching: their addresses lead to the history.
export default defineNuxtRouteMiddleware((to) => {
  if (useDeployed() && LOCAL_ONLY.some(path => to.path.startsWith(path))) return navigateTo('/')
})

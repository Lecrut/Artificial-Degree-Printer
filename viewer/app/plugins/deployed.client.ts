// The deployed viewer (ARCHITECTURE.md §13) has no server: `/api/*` is answered from the snapshot's static packs.
// Locally this does nothing.
export default defineNuxtPlugin(async () => {
  if (!useDeployed()) return
  const [{ packReader }, { installFetchShim }] = await Promise.all([
    import('~/utils/snapshot/packs'),
    import('~/utils/snapshot/fetchShim'),
  ])
  installFetchShim(packReader())
})

export default defineEventHandler((event) => {
  const { root, id, n } = getRouterParams(event)
  return callDetail(runDir(root, id), Number(n))
})

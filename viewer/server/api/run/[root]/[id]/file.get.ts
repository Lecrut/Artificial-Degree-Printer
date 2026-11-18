import { existsSync, readFileSync } from 'node:fs'
import { extname } from 'node:path'

const TYPES: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf',
  '.json': 'application/json; charset=utf-8',
}

export default defineEventHandler((event) => {
  const { root, id } = getRouterParams(event)
  const path = insideRun(runDir(root, id), String(getQuery(event).path ?? ''))
  if (!existsSync(path)) throw createError({ statusCode: 404, statusMessage: 'Brak pliku' })
  setHeader(event, 'content-type', TYPES[extname(path).toLowerCase()] ?? 'text/plain; charset=utf-8')
  return readFileSync(path)
})

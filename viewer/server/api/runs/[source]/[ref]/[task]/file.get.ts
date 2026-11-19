import { extname } from 'node:path'
import { sourceFromParams, taskFromParams } from '../../../../../utils/params'

const TYPES: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf',
}

export default defineEventHandler(async (event) => {
  const rel = String(getQuery(event).path ?? '')
  if (!rel || rel.includes('..')) throw createError({ statusCode: 400, statusMessage: 'Bad path' })
  const bytes = await sourceFromParams(event).readBytes(taskFromParams(event), rel)
  if (!bytes) throw createError({ statusCode: 404, statusMessage: 'No such file' })
  setHeader(event, 'content-type', TYPES[extname(rel).toLowerCase()] ?? 'text/plain; charset=utf-8')
  return bytes
})

import { callDetail } from '../../../../../../utils/calls'
import { sourceFromParams, taskFromParams } from '../../../../../../utils/params'

export default defineEventHandler(async (event) => {
  const step = Number(getRouterParam(event, 'step'))
  const detail = Number.isInteger(step) ? await callDetail(sourceFromParams(event), taskFromParams(event), step) : null
  if (!detail) throw createError({ statusCode: 404, statusMessage: 'No such call' })
  return detail
})

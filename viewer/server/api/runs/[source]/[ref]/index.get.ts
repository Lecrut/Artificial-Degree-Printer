import { sourceFromParams } from '../../../../utils/params'
import { loadTaskSummary } from '../../../../utils/runBundle'

export default defineEventHandler(async (event) => {
  const source = sourceFromParams(event)
  return Promise.all((await source.listTasks()).map(task => loadTaskSummary(source, task)))
})

import { sourceFromParams, taskFromParams } from '../../../../../utils/params'
import { loadRunBundle } from '../../../../../utils/runBundle'

export default defineEventHandler(event => loadRunBundle(sourceFromParams(event), taskFromParams(event)))

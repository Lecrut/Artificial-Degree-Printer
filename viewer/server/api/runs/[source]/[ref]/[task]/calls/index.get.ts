import { listCalls } from '../../../../../../utils/calls'
import { sourceFromParams, taskFromParams } from '../../../../../../utils/params'

export default defineEventHandler(event => listCalls(sourceFromParams(event), taskFromParams(event)))

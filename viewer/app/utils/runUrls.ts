import type { RunRef } from '#shared/types/run'

// Every address of one run, in the app (its page) and in the API.
const path = ({ source, ref, task }: RunRef) => `${source}/${ref}/${task}`

export const runPage = (at: RunRef) => `/run/${path(at)}`
export const runApi = (at: RunRef) => `/api/runs/${path(at)}`
export const callsApi = (at: RunRef) => `${runApi(at)}/calls`
export const callApi = (at: RunRef, step: number) => `${callsApi(at)}/${step}`
export const fileApi = (at: RunRef, file: string) => `${runApi(at)}/file?path=${encodeURIComponent(file)}`

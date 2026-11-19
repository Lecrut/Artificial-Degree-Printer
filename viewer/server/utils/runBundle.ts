import type { Hypergraph } from '#shared/types/hypergraph'
import type { RunBundle, RunEvent, RunFiles, TaskSummary } from '#shared/types/run'
import { parseJsonl } from '#shared/utils/events'
import { summarizeRun } from '#shared/utils/summary'
import { legacyTask, mergeLegacy } from './legacySummary'
import { runPath, type RunFileKey } from './runLayout'
import type { RunSource } from './sources/types'
import { parseJson } from '#shared/utils/json'

async function readJson<T>(source: RunSource, task: string, key: RunFileKey): Promise<T | null> {
  return parseJson<T>(await source.readText(task, runPath(source.kind, key)))
}

export async function readEvents(source: RunSource, task: string): Promise<RunEvent[]> {
  const text = await source.readText(task, runPath(source.kind, 'events'))
  return text ? parseJsonl(text) : []
}

async function readTitle(source: RunSource, task: string): Promise<string | null> {
  const blueprint = (await readJson<Record<string, unknown>>(source, task, 'blueprintRoot'))
    ?? (await readJson<Record<string, unknown>>(source, task, 'blueprint'))
  const title = blueprint?.thesis_title ?? blueprint?.thesis_statement
  return typeof title === 'string' ? title : null
}

export async function loadTaskSummary(source: RunSource, task: string): Promise<TaskSummary> {
  const summary = summarizeRun(task, await readEvents(source, task), await readTitle(source, task))
  return mergeLegacy(summary, await legacyTask(source, task))
}

async function readFiles(source: RunSource, task: string): Promise<RunFiles> {
  const existing = async (key: RunFileKey) => {
    const rel = runPath(source.kind, key)
    return (await source.readBytes(task, rel)) ? rel : null
  }
  const figuresDir = runPath(source.kind, 'figures')
  const figures = (await source.listDir(task, figuresDir)).filter(name => /\.(png|svg|jpe?g)$/i.test(name))
  return {
    thesis: await existing('thesis'),
    thesisCompiled: await existing('thesisCompiled'),
    results: await existing('results'),
    pdf: await existing('pdf'),
    figures: figures.map(name => `${figuresDir}/${name}`),
  }
}

export async function loadRunBundle(source: RunSource, task: string): Promise<RunBundle> {
  const events = await readEvents(source, task)
  return {
    ref: { source: source.kind, ref: source.ref, task },
    summary: mergeLegacy(summarizeRun(task, events, await readTitle(source, task)), await legacyTask(source, task)),
    events,
    hypergraph: await readJson<Hypergraph>(source, task, 'hypergraph'),
    blueprint: (await readJson(source, task, 'blueprintRoot')) ?? (await readJson(source, task, 'blueprint')),
    files: await readFiles(source, task),
  }
}

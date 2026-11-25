import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import type { AgentPrompt } from '#shared/types/flow'
import { REPO_ROOT } from './repo'

const AGENTS_DIR = join(REPO_ROOT, 'adk', 'agents')

/** The base prompt of an agent from `adk/agents/<group>/<name>.md`, or null. The name is matched against the listing, never joined into a path. */
export async function readAgentPrompt(name: string): Promise<AgentPrompt | null> {
  const groups = await readdir(AGENTS_DIR, { withFileTypes: true }).catch(() => [])
  for (const group of groups.filter(entry => entry.isDirectory())) {
    const files = await readdir(join(AGENTS_DIR, group.name)).catch(() => [])
    const file = files.find(candidate => candidate === `${name}.md`)
    if (file) return { name, group: group.name, markdown: await readFile(join(AGENTS_DIR, group.name, file), 'utf-8') }
  }
  return null
}

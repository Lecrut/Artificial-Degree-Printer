import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import type { Changelog, CommitInfo } from '#shared/types/changelog'
import { parseAudit } from '#shared/utils/audit'
import { BENCHMARKS_DIR, git, REPO_ROOT } from './repo'

const STAT = /(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?/

/** Every commit, newest first, with the size of its change and whether it carries benchmark results. */
async function commits(): Promise<CommitInfo[]> {
  const out = (await git(['log', '--shortstat', '--format=@%H%x09%aI%x09%s'])) ?? ''
  const benchmarkShas = new Set(((await git(['log', '--format=%H', '--', BENCHMARKS_DIR])) ?? '').split('\n').filter(Boolean))
  const result: CommitInfo[] = []
  for (const line of out.split('\n')) {
    if (line.startsWith('@')) {
      const [sha = '', date = '', ...message] = line.slice(1).split('\t')
      result.push({ sha, short: sha.slice(0, 7), date, message: message.join('\t'), files: 0, insertions: 0, deletions: 0, benchmarks: benchmarkShas.has(sha) })
      continue
    }
    const stat = STAT.exec(line)
    const last = result.at(-1)
    if (stat && last) Object.assign(last, { files: Number(stat[1]), insertions: Number(stat[2] ?? 0), deletions: Number(stat[3] ?? 0) })
  }
  return result
}

/** The audit's sections and the repository's commits: what changed when, and why. */
export async function loadChangelog(): Promise<Changelog> {
  const audit = await readFile(join(REPO_ROOT, 'audit_repairs.md'), 'utf-8').catch(() => '')
  return { entries: parseAudit(audit), commits: await commits() }
}

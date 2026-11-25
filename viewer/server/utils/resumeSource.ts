import { execFile } from 'node:child_process'
import { mkdtemp, stat, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { promisify } from 'node:util'
import type { LaunchTask, ResumeFrom } from '#shared/types/live'
import { taskKey } from '#shared/utils/launch'
import { BENCHMARKS_DIR, REPO_ROOT, SANDBOX_DIR, gitBuffer } from './repo'
import { runSource } from './sources'

const run = promisify(execFile)
// A live sandbox written to a moment ago belongs to a run still going: resuming would wipe it under that run.
const LIVE_QUIET_MS = 120_000
export const SNAPSHOT_FILE = /^\d{3}_[\w.-]+\.zip$/

async function liveIsQuiet(slug: string): Promise<boolean> {
  const events = await stat(join(REPO_ROOT, SANDBOX_DIR, slug, 'workspace', 'logs', 'events.jsonl')).catch(() => null)
  return !events || Date.now() - events.mtimeMs > LIVE_QUIET_MS
}

async function extractCommit(sha: string, slug: string): Promise<string> {
  const target = await mkdtemp(join(tmpdir(), 'adk-resume-'))
  const archive = join(target, 'run.tar')
  const folder = `${BENCHMARKS_DIR}/${slug}`
  await run('git', ['archive', '--format=tar', '-o', archive, sha, '--', folder], { cwd: REPO_ROOT })
  await run('tar', ['-xf', archive, '-C', target])
  return join(target, folder)
}

/** One snapshot zip of a commit, written to a temporary file (the harness reads files, not git). */
async function extractSnapshot(sha: string, slug: string, file: string): Promise<string> {
  const bytes = await gitBuffer(['show', `${sha}:${BENCHMARKS_DIR}/${slug}/logs/snapshots/${file}`])
  if (!bytes) throw createError({ statusCode: 404, statusMessage: 'No such snapshot in that commit' })
  const target = join(await mkdtemp(join(tmpdir(), 'adk-resume-')), file)
  await writeFile(target, bytes)
  return target
}

async function onDiskSnapshot(from: ResumeFrom, slug: string, file: string): Promise<string> {
  const base = from.source === 'live' ? join(SANDBOX_DIR, slug, 'workspace') : join(BENCHMARKS_DIR, slug)
  const path = join(REPO_ROOT, base, 'logs', 'snapshots', file)
  if (!(await stat(path).catch(() => null))) throw createError({ statusCode: 404, statusMessage: 'No such snapshot' })
  return path
}

/** What `main.py --resume-from` reads for a run of the viewer: the saved state of a run (on disk, or extracted from
 *  a commit), or one snapshot of it. */
export async function resumeDir(from: ResumeFrom, key: LaunchTask): Promise<string> {
  const slug = (await runSource(from.source, from.ref).listTasks()).find(name => taskKey(name) === key)
  if (!slug) throw createError({ statusCode: 404, statusMessage: 'No such task in that run' })
  if (from.source === 'live' && !(await liveIsQuiet(slug))) {
    throw createError({ statusCode: 409, statusMessage: 'That run is still writing; stop it first' })
  }
  if (from.snapshot) {
    return from.source === 'git' ? extractSnapshot(from.ref, slug, from.snapshot) : onDiskSnapshot(from, slug, from.snapshot)
  }
  if (from.source === 'git') return extractCommit(from.ref, slug)
  return join(REPO_ROOT, from.source === 'live' ? SANDBOX_DIR : BENCHMARKS_DIR, slug)
}

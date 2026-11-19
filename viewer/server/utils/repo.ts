import { execFile } from 'node:child_process'
import { resolve } from 'node:path'
import { promisify } from 'node:util'

const run = promisify(execFile)

/** The repository the viewer reads: the parent of `viewer/` unless ADK_REPO says otherwise. */
export const REPO_ROOT = resolve(process.env.ADK_REPO ?? resolve(process.cwd(), '..'))
export const BENCHMARKS_DIR = 'adk/workspace/benchmarks'
export const SANDBOX_DIR = `${BENCHMARKS_DIR}/_evolved_adk_state`

/** stdout of a git command in the repository, or null when git fails (missing path in a commit). */
export async function git(args: string[]): Promise<string | null> {
  return (await gitBuffer(args))?.toString('utf-8') ?? null
}

/** The same, as bytes (images and PDFs from a commit). */
export async function gitBuffer(args: string[]): Promise<Buffer | null> {
  try {
    const { stdout } = await run('git', args, { cwd: REPO_ROOT, maxBuffer: 256 * 1024 * 1024, encoding: 'buffer' })
    return stdout
  }
  catch {
    return null
  }
}

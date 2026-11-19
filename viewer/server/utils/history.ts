import type { CommitSummary } from '#shared/types/run'
import { BENCHMARKS_DIR, git } from './repo'
import { loadTaskSummary } from './runBundle'
import { gitSource } from './sources/gitSource'

const summaries = new Map<string, Promise<CommitSummary>>()

interface CommitLine {
  sha: string
  date: string
  message: string
}

async function benchmarkCommits(): Promise<CommitLine[]> {
  const out = await git(['log', '--format=%H%x09%aI%x09%s', '--', BENCHMARKS_DIR])
  return (out ?? '').split('\n').filter(Boolean).map((line) => {
    const [sha = '', date = '', ...message] = line.split('\t')
    return { sha, date, message: message.join('\t') }
  })
}

async function summarizeCommit(commit: CommitLine): Promise<CommitSummary> {
  const source = gitSource(commit.sha)
  const tasks = await Promise.all((await source.listTasks()).map(task => loadTaskSummary(source, task)))
  return { sha: commit.sha, short: commit.sha.slice(0, 7), date: commit.date, message: commit.message, tasks }
}

/** Every commit that changed the benchmark results, newest first, with the summary of each task it holds. */
export async function listHistory(): Promise<CommitSummary[]> {
  const commits = await benchmarkCommits()
  return Promise.all(commits.map((commit) => {
    if (!summaries.has(commit.sha)) summaries.set(commit.sha, summarizeCommit(commit))
    return summaries.get(commit.sha)!
  }))
}

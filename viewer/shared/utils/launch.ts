import type { LaunchRequest, LaunchTask } from '../types/live'

export const LAUNCH_TASKS: readonly LaunchTask[] = ['1', '2', '3', '4']

/** The chosen tasks in suite order, without repeats and unknown keys. */
export function normalizeTasks(tasks: readonly string[]): LaunchTask[] {
  return LAUNCH_TASKS.filter(task => tasks.includes(task))
}

/** The suite key of a task folder (`01_rl_tictactoe` -> `1`), or null for anything else. */
export function taskKey(task: string): LaunchTask | null {
  const key = String(Number(/^(\d{2})_/.exec(task)?.[1]))
  return LAUNCH_TASKS.find(candidate => candidate === key) ?? null
}

/** Arguments of `main.py` for a request: `--benchmark-task` takes the tasks as a comma-separated list.
 *  `resumeDir`: the folder holding the saved state of the run to continue (one task only). */
export function launchArgs(request: LaunchRequest, resumeDir?: string): string[] {
  const template = request.template ? ['--template', request.template] : []
  const resume = resumeDir ? ['--resume-from', resumeDir] : []
  return ['main.py', '--provider', request.provider, '--benchmark-task', normalizeTasks(request.tasks).join(','), ...template, ...resume]
}

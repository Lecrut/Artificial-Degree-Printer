import type { LaunchRequest, LaunchTask } from '../types/live'

export const LAUNCH_TASKS: readonly LaunchTask[] = ['1', '2', '3', '4']

/** The chosen tasks in suite order, without repeats and unknown keys. */
export function normalizeTasks(tasks: readonly string[]): LaunchTask[] {
  return LAUNCH_TASKS.filter(task => tasks.includes(task))
}

/** Arguments of `main.py` for a request: `--benchmark-task` takes the tasks as a comma-separated list. */
export function launchArgs(request: LaunchRequest): string[] {
  const template = request.template ? ['--template', request.template] : []
  return ['main.py', '--provider', request.provider, '--benchmark-task', normalizeTasks(request.tasks).join(','), ...template]
}

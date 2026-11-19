// Real data from benchmark 18.11 (01_rl_tictactoe), so stories show what the viewer shows.
import type { Hypergraph } from '../../shared/types/hypergraph'
import type { QueueTask } from '../../shared/types/live'
import type { RunEvent, TaskSummary } from '../../shared/types/run'
import type { RunTimeline } from '../../shared/types/timeline'
import hypergraphJson from './hypergraph.json'
import timelineJson from './timeline.json'

export const hypergraph = hypergraphJson as unknown as Hypergraph
export const timeline = timelineJson as RunTimeline
export const states = Object.fromEntries(Object.entries(hypergraph.vertices).map(([id, v]) => [id, v.state]))

export const summary: TaskSummary = {
  task: '01_rl_tictactoe',
  status: 'COMPLETED_WITH_GAPS',
  title: 'Zastosowanie algorytmu Q-Learning do gry w Kółko i Krzyżyk',
  started: '2026-11-18T18:11:11+00:00',
  ended: '2026-11-18T19:39:44+00:00',
  durationSeconds: 5313,
  tasksTotal: 34,
  tasksDone: 21,
  llmCalls: 316,
  failedVerdicts: 69,
  rejectedWrites: 66,
  planVersions: 3,
  replans: 4,
}

export const queue: QueueTask[] = [
  { task_id: 'T1', description: 'Wstęp i motywacja', target_node: 'thesis.md#ch1', assigned_agent: 'seed_writer', status: 'DONE' },
  { task_id: 'T3', description: 'Konfiguracja eksperymentu', target_node: 'config.py', assigned_agent: 'seed_coder', status: 'DONE', repair_attempts: 1 },
  { task_id: 'T5', description: 'Agent Q-Learning', target_node: 'qagent.py', assigned_agent: 'seed_coder', status: 'FAILED', repair_attempts: 3 },
  { task_id: 'T7', description: 'Testy agenta', target_node: 'tests/test_qagent.py', assigned_agent: 'seed_tester', status: 'FAILED', repair_attempts: 2 },
  { task_id: 'T6', description: 'Testy środowiska', target_node: 'test_env.py', assigned_agent: 'qa_agent', status: 'IN_PROGRESS' },
  { task_id: 'T8', description: 'Eksperyment', target_node: 'experiment.py', assigned_agent: 'seed_coder', status: 'WAITING' },
  { task_id: 'T12', description: 'Wyniki', target_node: 'thesis.md#ch4', assigned_agent: 'seed_writer', status: 'TODO' },
]

// T7 is being repaired (its second fix runs): the queue already says FAILED, the board must show it in progress.
export const repairingEvents: RunEvent[] = [
  { ts: '2026-11-19T11:42:53+00:00', event: 'TASK_START', task_id: 'T7' },
  { ts: '2026-11-19T11:44:10+00:00', event: 'VERDICT', task_id: 'T7', status: 'FAIL' },
  { ts: '2026-11-19T11:46:02+00:00', event: 'LLM_CALL_START', step: 31, agent: 'seed_tester', task_id: 'T7_FIX2' },
]

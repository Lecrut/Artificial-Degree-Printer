import type { FlowKind, FlowNode } from '#shared/types/flow'

const node = (id: string, kind: FlowKind, col: number, row: number): FlowNode => ({ id, kind, col, row })

/**
 * The blocks of the diagram. A hand-made description of the harness (`orchestrator.run`, `plan_stages`, `building`,
 * `verification`, `repair`, `fragment_replan`): a change of the flow there is a change here (flow.test.ts keeps the agents in step).
 * Columns: 0 is the main line, -1 and -2 the re-plan side, 1 to 4 the repair side.
 */
export const FLOW_NODES: FlowNode[] = [
  node('start', 'start', 0, 0),
  node('recon', 'step', 0, 1),
  // Planning, stage by stage (plan_stages): outline, one interface per module, tasks derived by code, the main critic.
  node('plan_outline', 'agent', 0, 2),
  node('outline_critic_guard', 'agent', 0, 3),
  node('d_outline', 'decision', 0, 4),
  node('j_outline', 'jump', 1, 4),
  node('plan_module', 'agent', 0, 5),
  node('module_critic_guard', 'agent', 0, 6),
  node('d_module', 'decision', 0, 7),
  node('j_module', 'jump', 1, 7),
  node('s_tasks', 'step', 0, 8),
  node('plan_critic_guard', 'agent', 0, 9),
  node('d_plan', 'decision', 0, 10),
  node('j_plan', 'jump', 1, 10),
  node('s_gates', 'step', 0, 11),
  // Building: the next ready task goes to the agent of its file, then to the checks.
  node('s_queue', 'step', 0, 12),
  node('d_type', 'decision', 0, 13),
  node('seed_coder', 'agent', -1, 14),
  node('seed_tester', 'agent', 0, 14),
  node('seed_writer', 'agent', 1, 14),
  node('background_researcher', 'agent', 2, 13),
  node('discoverer_researcher', 'agent', 2, 14),
  node('sota_researcher', 'agent', 2, 15),
  node('s_verify', 'step', 0, 17),
  node('d_pass', 'decision', 0, 18),
  node('d_more', 'decision', 0, 19),
  node('j_queue1', 'jump', -1, 19),
  node('d_failed', 'decision', 0, 20),
  // The end of the queue with failed vertices: the designer revises the design first (redesign), then the re-plan of the failed.
  node('d_redesign', 'decision', -1, 20),
  node('implementation_auditor', 'agent', -3, 20),
  node('s_revise', 'step', -3, 21),
  node('d_guidelines', 'decision', -3, 22),
  node('j_replan', 'jump', -4, 22),
  node('s_redesign_modules', 'step', -3, 23),
  node('s_redesign_apply', 'step', -3, 24),
  node('j_queue4', 'jump', -3, 25),
  node('task_planner', 'agent', -1, 21),
  node('d_progress', 'decision', -1, 22),
  node('j_queue2', 'jump', -2, 22),
  node('e_gaps1', 'end', -1, 23),
  // The repair of a failed task (repair): fast attempts, the interface judge, evolution, the repair planner.
  node('s_fast', 'step', 2, 18),
  node('d_fastok', 'decision', 2, 19),
  node('d_spec', 'decision', 2, 20),
  node('plan_change_guard', 'agent', 3, 20),
  node('j_fast', 'jump', 4, 20),
  node('d_pattern', 'decision', 2, 21),
  node('evolution_architect', 'agent', 3, 21),
  node('prompt_consolidator', 'agent', 3, 22),
  node('d_vertex', 'decision', 2, 22),
  node('remediation_planner', 'agent', 3, 23),
  node('s_failed', 'step', 2, 23),
  node('j_next', 'jump', 2, 24),
  // Gate 3, the defense of the whole work.
  node('code_auditor', 'agent', 0, 21),
  node('symbolic_auditor', 'agent', 0, 22),
  node('redteam_critic_guard', 'agent', 0, 23),
  node('d_defense', 'decision', 0, 24),
  node('s_rebuild', 'step', -1, 24),
  node('j_queue3', 'jump', -2, 24),
  node('e_gaps2', 'end', -1, 25),
  node('s_pdf', 'step', 0, 25),
  node('s_hitl', 'step', 0, 26),
  node('end', 'end', 0, 27),
]

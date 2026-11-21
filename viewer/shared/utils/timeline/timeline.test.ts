import { describe, expect, it } from 'bun:test'
import type { RunEvent } from '../../types/run'
import { buildTimeline } from './index'

const at = (ts: string, event: string, fields: Record<string, unknown> = {}): RunEvent => ({ ts, event, ...fields })

describe('buildTimeline', () => {
  it('groups a task with its repairs and keeps a queue task of the same name apart', () => {
    const { entries } = buildTimeline([
      at('1', 'TASK_START', { task_id: 'T5', node: 'env.py', agent: 'seed_coder', tier: 'SML' }),
      at('2', 'VERDICT', { task_id: 'T5', status: 'FAIL', first_issue: 'boom' }),
      at('3', 'BUILDER_ANSWER_REJECTED', { task_id: 'T5_FIX1', error: 'SyntaxError' }),
      at('4', 'LLM_CALL_END', { task_id: 'T5_FIX1', agent: 'seed_coder', elapsed_s: 2 }),
      at('5', 'TASK_FAILED', { task_id: 'T5' }),
      at('6', 'TASK_START', { task_id: 'Q3_FIX1' }),
      at('7', 'TASK_DONE', { task_id: 'Q3_FIX1' }),
    ])
    const [t5, q3] = entries
    expect(t5).toMatchObject({ title: 'T5', status: 'fail', phase: 'building', subtitle: 'env.py · seed_coder · SML' })
    expect(t5!.attempts.map(a => a.kind)).toEqual(['verdict', 'rejected'])
    expect(t5!.llm).toEqual({ calls: 1, seconds: 2, agents: ['seed_coder'] })
    expect(q3).toMatchObject({ title: 'Q3_FIX1', status: 'ok', phase: 'repairs' })
  })

  it('shows planning in stages: the outline, each module, the fused plan, a reopened part', () => {
    const author = (agent: string) => ({ agent, task_id: null })
    const { entries } = buildTimeline([
      at('1', 'LLM_CALL_END', { ...author('plan_outline'), elapsed_s: 30 }),
      at('1', 'PLAN_OUTLINE_CHECKED', { attempt: 1, modules: ['a.py', 'x.py'], problems: ['OUTLINE [x.py]: unused'], critic: [] }),
      at('2', 'LLM_CALL_END', { ...author('plan_outline'), elapsed_s: 20 }),
      at('2', 'LLM_CALL_END', { ...author('outline_critic_guard'), elapsed_s: 10 }),
      at('2', 'PLAN_OUTLINE_CHECKED', { attempt: 2, modules: ['a.py'], problems: [], critic: [] }),
      at('2', 'PLAN_OUTLINE_ACCEPTED', { attempts: 2, order: ['a.py'] }),
      at('3', 'LLM_CALL_END', { ...author('plan_module'), elapsed_s: 5 }),
      at('3', 'PLAN_MODULE_CHECKED', { module: 'a.py', attempt: 1, problems: [], critic: [] }),
      at('3', 'PLAN_MODULE_ACCEPTED', { module: 'a.py', attempts: 1, over_critic: [] }),
      at('4', 'PLAN_FUSED', { modules: ['a.py'], tasks: 7 }),
      at('5', 'PLAN_MODULE_REOPENED', { module: 'a.py', reasons: ['PLAN_CRITIC [a.py]: wrong'] }),
      at('5', 'PLAN_MODULE_CHECKED', { module: 'a.py', attempt: 1, problems: [], critic: [] }),
    ])
    expect(entries.map(e => [e.title, e.status])).toEqual([
      ['Szkic planu', 'ok'], ['Interfejs a.py', 'ok'], ['Plan złożony', 'ok'], ['Interfejs a.py — ponownie', 'running'],
    ])
    expect(entries[0]).toMatchObject({ subtitle: 'a.py', llm: { calls: 3, seconds: 60, agents: ['plan_outline', 'outline_critic_guard'] } })
    expect(entries[0]!.details.map(d => d.label)).toEqual(['próba 1', 'kod', 'próba 2'])
    expect(entries[2]!.subtitle).toBe('7 zadań · 1 modułów')
    expect(entries[3]!.details[0]).toMatchObject({ label: 'powód', status: 'warn' })
  })

  it('shows each version of the plan with the critic and the patch', () => {
    const { entries } = buildTimeline([
      at('1', 'PLAN_CHECKED', { attempt: 0, modules: ['a.py'], blockers: { code: ['STUB_DOES_NOT_IMPORT'], instruction: [], critic: [] } }),
      at('2', 'PLAN_PATCHED', { accepted: true, changed: ['a.py'], fixed: ['STUB_DOES_NOT_IMPORT'], new: [], rejected: [] }),
      at('3', 'PLAN_REVIEWED', { status: 'PASS' }),
      at('4', 'PLAN_CHECKED', { attempt: 1, modules: ['a.py'], blockers: { code: [], instruction: [], critic: [] } }),
    ])
    expect(entries.map(e => [e.title, e.status])).toEqual([['Weryfikacja planu 1', 'fail'], ['Weryfikacja planu 2', 'ok']])
    expect(entries[0]!.details.map(d => d.label)).toEqual(['kod', 'łatka', 'naprawione'])
    expect(entries[1]!.details[0]).toMatchObject({ label: 'krytyk', status: 'ok' })
  })

  it('shows the planner writing the plan, then the critic and the check, each as its own step', () => {
    const planner = { agent: 'task_planner', task_id: null }
    const critic = { agent: 'plan_critic_guard', task_id: null }
    const events = [
      at('1', 'LLM_CALL_START', planner),
      at('2', 'LLM_CALL_END', { ...planner, elapsed_s: 100, decision: "Plan: 13 zadan [T1, T2], cel: 'Q-learning'" }),
      at('3', 'LLM_CALL_START', critic),
      at('4', 'LLM_CALL_END', { ...critic, elapsed_s: 40 }),
      at('4', 'PLAN_REVIEWED', { status: 'FAIL' }),
      at('4', 'PLAN_CHECKED', { attempt: 0, modules: ['a.py'], blockers: { code: [], instruction: [], critic: ['doctest'] } }),
      at('5', 'LLM_CALL_START', planner),
    ]
    const { entries } = buildTimeline(events)
    expect(entries.map(e => [e.title, e.status])).toEqual([
      ['Plan początkowy', 'ok'],
      ['Weryfikacja planu 1', 'fail'],
      ['Poprawka planu 1', 'running'],
    ])
    expect(entries[0]).toMatchObject({ subtitle: '13 zadań', llm: { calls: 1, seconds: 100, agents: ['task_planner'] } })
    expect(entries[0]!.details[0]).toMatchObject({ label: 'cel', text: 'Q-learning' })
    expect(entries[1]!.llm.agents).toEqual(['plan_critic_guard'])
    const newer = buildTimeline([at('1', 'LLM_CALL_START', planner), at('2', 'LLM_CALL_END', { ...planner, decision: 'zadania: 12; interfejsy: 4' })])
    expect(newer.entries[0]!.subtitle).toBe('12 zadań · 4 modułów')
    // While the critic still reads, the check is already on the timeline, running.
    expect(buildTimeline(events.slice(0, 3)).entries[1]).toMatchObject({ title: 'Weryfikacja planu 1', status: 'running' })
  })
})

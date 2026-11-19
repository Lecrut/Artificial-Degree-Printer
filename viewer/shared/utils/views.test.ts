import { describe, expect, it } from 'bun:test'
import type { Hypergraph } from '../types/hypergraph'
import type { RunEvent } from '../types/run'
import { parseCsv } from './csv'
import { incidenceMatrix } from './incidence'
import { activeTask, boardColumns, openCall } from './live'
import { renderThesis } from './markdown'

const v = (kind: string) => ({ kind, owner: null, state: 'spec', description: '', attempts: 0, history: [], last_writer: null, files: [] })

describe('views', () => {
  it('maps vertices to bags with their roles, code first and bags I, R, N', () => {
    const h: Hypergraph = {
      version: 2,
      vertices: { 'thesis.md#ch1': v('chapter'), 'core.py': v('entry'), 'config.py': v('code') },
      edges: {
        'N:thesis.md#ch1': { type: 'N', members: { 'thesis.md#ch1': 'X', 'core.py': 'C' }, spec: {}, fingerprint: null, observed: ['core.py'] },
        'I:core.py': { type: 'I', members: { 'core.py': 'P', 'config.py': 'C' }, spec: {}, fingerprint: null, observed: [] },
      },
      order: [],
    }
    const m = incidenceMatrix(h)
    expect(m.rows.map(r => r.id)).toEqual(['core.py', 'config.py', 'thesis.md#ch1'])
    expect(m.columns.map(c => c.id)).toEqual(['I:core.py', 'N:thesis.md#ch1'])
    expect(m.cells['core.py']).toEqual({ 'I:core.py': { role: 'P', observed: false }, 'N:thesis.md#ch1': { role: 'C', observed: true } })
  })

  it('renders the thesis with theme classes, marks pointers and escapes raw HTML', () => {
    const html = renderThesis('## Wyniki\n\nWin rate \\ref_csv{results.csv:proposed+win_rate}.\n\n<script>x</script>')
    expect(html).toContain('<h2 class="text-h5')
    expect(html).toContain('⟨csv: results.csv:proposed+win_rate⟩')
    expect(html).not.toContain('<script>')
  })

  it('reads a results file with quoted fields', () => {
    expect(parseCsv('method,note\nbaseline,"a, b"\n')).toEqual({ headers: ['method', 'note'], rows: [{ method: 'baseline', note: 'a, b' }] })
  })

  it('finds the call the harness waits for and sorts the queue into columns', () => {
    const events: RunEvent[] = [
      { ts: '1', event: 'LLM_CALL_START', step: 1, agent: 'task_planner' },
      { ts: '2', event: 'LLM_CALL_END', step: 1 },
      { ts: '3', event: 'LLM_CALL_START', step: 2, agent: 'seed_coder', model: 'qwen', tier: 'SML', task_id: 'T2' },
    ]
    expect(openCall(events)).toMatchObject({ step: 2, agent: 'seed_coder', taskId: 'T2', since: '3' })
    expect(openCall(events.slice(0, 2))).toBeNull()
    const board = boardColumns([
      { task_id: 'T1', description: '', target_node: 'a.py', assigned_agent: 'seed_coder', status: 'DONE' },
      { task_id: 'T2', description: '', target_node: 'b.py', assigned_agent: 'seed_coder', status: 'ODD' },
    ])
    expect(board.DONE.map(t => t.task_id)).toEqual(['T1'])
    expect(board.TODO.map(t => t.task_id)).toEqual(['T2'])
  })

  it('keeps a task under repair in progress, though the queue already says FAILED', () => {
    const repairing: RunEvent[] = [
      { ts: '1', event: 'TASK_START', task_id: 'T7' },
      { ts: '2', event: 'VERDICT', task_id: 'T7', status: 'FAIL' },
      { ts: '3', event: 'LLM_CALL_START', step: 9, agent: 'seed_tester', task_id: 'T7_FIX2' },
    ]
    expect(activeTask(repairing)).toBe('T7')
    expect(activeTask([...repairing, { ts: '4', event: 'TASK_WAITING', task_id: 'T7' }])).toBeNull()
    const queue = [{ task_id: 'T7', description: '', target_node: 't.py', assigned_agent: 'seed_tester', status: 'FAILED', repair_attempts: 2 }]
    expect(boardColumns(queue, 'T7').IN_PROGRESS.map(t => t.task_id)).toEqual(['T7'])
    expect(boardColumns(queue, null).FAILED.map(t => t.task_id)).toEqual(['T7'])
  })
})

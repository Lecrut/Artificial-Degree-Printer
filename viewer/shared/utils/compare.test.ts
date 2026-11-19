import { describe, expect, test } from 'bun:test'
import type { RunEvent } from '../types/run'
import { parseRunKey, runKey, runProfile, valueAt } from './compare'

const at = (minute: number) => `2026-11-18T18:${String(minute).padStart(2, '0')}:00+00:00`
const events: RunEvent[] = [
  { ts: at(0), event: 'LLM_CALL_START', agent: 'task_planner', tier: 'LRM', prompt_chars: 4000 },
  { ts: at(2), event: 'LLM_CALL_END', agent: 'task_planner', tier: 'LRM', elapsed_s: 120 },
  { ts: at(2), event: 'TASK_START', task_id: 'T1' },
  { ts: at(3), event: 'LLM_CALL_START', agent: 'seed_coder', tier: 'SML', prompt_chars: 800 },
  { ts: at(4), event: 'LLM_CALL_END', agent: 'seed_coder', tier: 'SML', elapsed_s: 30 },
  { ts: at(5), event: 'TASK_DONE', task_id: 'T1' },
]

describe('runProfile', () => {
  const profile = runProfile('01_rl_tictactoe', events)

  test('totals per tier and per agent', () => {
    expect(profile.llmSeconds).toBe(150)
    expect(profile.tierSeconds).toEqual({ LRM: 120, SML: 30 })
    expect(profile.agents.seed_coder).toEqual({ calls: 1, seconds: 30 })
    expect(profile.promptChars).toBe(4800)
  })

  test('running totals start at zero and step at each event, in minutes since the start', () => {
    expect(profile.over.calls).toEqual([[0, 0], [2, 1], [4, 2]])
    expect(profile.over.llmMinutes.at(-1)).toEqual([4, 2.5])
    expect(profile.over.tasksDone).toEqual([[0, 0], [5, 1]])
    expect(profile.over.promptTokens.at(-1)).toEqual([3, 1200])
  })
})

describe('run keys', () => {
  test('round trip and rejection of foreign sources', () => {
    const ref = { source: 'git' as const, ref: '362092f', task: '01_rl_tictactoe' }
    expect(parseRunKey(runKey(ref))).toEqual(ref)
    expect(parseRunKey('ftp:x:y')).toBeNull()
    expect(parseRunKey('git:362092f')).toBeNull()
  })
})

describe('valueAt', () => {
  test('a running total holds its last step until the next one', () => {
    const points: [number, number][] = [[0, 0], [2, 1], [4, 2]]
    expect(valueAt(points, 3)).toBe(1)
    expect(valueAt(points, 4)).toBe(2)
    expect(valueAt(points, 90)).toBe(2)
    expect(valueAt([], 1)).toBeNull()
  })
})

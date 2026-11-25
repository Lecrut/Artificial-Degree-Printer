import { describe, expect, it } from 'bun:test'
import type { RunEvent } from '../types/run'
import { parseTraceCalls, toCallDetail } from './calls'

describe('parseTraceCalls', () => {
  it('shows an open request on a live run and replaces it once the answer arrives', () => {
    const req = {
      timestamp: '2026-11-25T15:00:00Z',
      phase: 'request',
      step: 1,
      agent_md: 'adk/agents/building/seed_coder.md',
      provider: 'ollama',
      model_tier: 'SML',
      model_name: 'qwen3.5:4b',
      user_payload: { task: { task_id: 'T2' }, target_file: 'core.py' },
    }
    const livePending = parseTraceCalls([req], [], true)
    expect(livePending).toHaveLength(1)
    expect(livePending[0]!.summary).toMatchObject({
      step: 1,
      agent: 'seed_coder',
      tier: 'SML',
      model: 'qwen3.5:4b',
      taskId: 'T2',
      ok: true,
      running: true,
      elapsedMs: null,
    })
    expect(toCallDetail(livePending[0]!, '# seed_coder')).toMatchObject({
      systemPrompt: '# seed_coder',
      payload: { task: { task_id: 'T2' }, target_file: 'core.py' },
      answer: null,
    })

    // Archived runs ignore unmatched requests unless includeRunning is enabled.
    expect(parseTraceCalls([req], [], false)).toHaveLength(0)

    const ans = {
      ...req,
      timestamp: '2026-11-25T15:00:06Z',
      phase: 'answer',
      elapsed_ms: 5820,
      system_prompt: '# prompt from trace',
      raw_response: '{"source_code": "x = 1"}',
      parsed_output: { source_code: 'x = 1' },
    }
    const end: RunEvent = { ts: '2026-11-25T15:00:06Z', event: 'LLM_CALL_END', step: 1, decision: 'pliki: 1', verdict: 'PASS' }
    const settled = parseTraceCalls([req, ans], [end], true)
    expect(settled).toHaveLength(1)
    expect(settled[0]!.summary).toMatchObject({
      step: 1,
      agent: 'seed_coder',
      elapsedMs: 5820,
      ok: true,
      verdict: 'PASS',
      decision: 'pliki: 1',
    })
    expect(settled[0]!.summary.running).toBeUndefined()
  })

  it('preserves request payload and tier when an error row omits them, and supports legacy traces', () => {
    const req = {
      timestamp: '2026-11-25T15:01:00Z',
      phase: 'request',
      step: 2,
      agent_md: 'adk/agents/planning/plan_module.md',
      provider: 'ollama',
      model_tier: 'LRM',
      model_name: 'qwen3.6:35b',
      user_payload: { module: { file: 'a.py' } },
    }
    const err = {
      timestamp: '2026-11-25T15:01:10Z',
      phase: 'error',
      step: 2,
      agent_md: 'adk/agents/planning/plan_module.md',
      provider: 'ollama',
      model_name: 'qwen3.6:35b',
      error: 'TimeoutError: limit',
    }
    const calls = parseTraceCalls([req, err], [], false)
    expect(calls[0]!.summary).toMatchObject({ step: 2, ok: false, tier: 'LRM', agent: 'plan_module' })
    expect(toCallDetail(calls[0]!).payload).toEqual({ module: { file: 'a.py' } })
    expect(toCallDetail(calls[0]!).error).toBe('TimeoutError: limit')

    const legacy = parseTraceCalls([{ timestamp: 't', agent_md: 'seed_writer.md', parsed_output: {} }], [], false)
    expect(legacy[0]!.summary).toMatchObject({ step: 1, agent: 'seed_writer', ok: true })
  })
})

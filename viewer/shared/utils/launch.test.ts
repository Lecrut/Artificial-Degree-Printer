import { describe, expect, test } from 'bun:test'
import { launchArgs, normalizeTasks } from './launch'

describe('launch', () => {
  test('tasks come out in suite order, without repeats and unknown keys', () => {
    expect(normalizeTasks(['2', '1', '2', 'x'])).toEqual(['1', '2'])
    expect(normalizeTasks([])).toEqual([])
  })

  test('several tasks are one comma-separated --benchmark-task', () => {
    expect(launchArgs({ tasks: ['2', '1'], provider: 'ollama', template: null }))
      .toEqual(['main.py', '--provider', 'ollama', '--benchmark-task', '1,2'])
  })

  test('the template is passed when chosen', () => {
    expect(launchArgs({ tasks: ['3'], provider: 'mock', template: 'paper_ieee' }))
      .toEqual(['main.py', '--provider', 'mock', '--benchmark-task', '3', '--template', 'paper_ieee'])
  })
})

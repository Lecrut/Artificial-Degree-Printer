import { describe, expect, test } from 'bun:test'
import { parseJson, parseJsonLines } from './json'

describe('json', () => {
  test('missing or broken JSON is null, not a throw', () => {
    expect(parseJson<{ a: number }>('{"a":1}')).toEqual({ a: 1 })
    expect(parseJson(null)).toBeNull()
    expect(parseJson('{"a":')).toBeNull()
  })

  test('JSONL keeps complete lines and skips one cut off mid-write', () => {
    expect(parseJsonLines<{ n: number }>('{"n":1}\n\n{"n":2}\n{"n":')).toEqual([{ n: 1 }, { n: 2 }])
  })
})

import type { RunEvent } from '../types/run'
import { parseJsonLines } from './json'

/** Typed reads of the loosely typed fields of a run event. */
export function str(event: RunEvent, field: string): string {
  const value = event[field]
  return typeof value === 'string' ? value : value == null ? '' : String(value)
}

export function num(event: RunEvent, field: string): number {
  const value = Number(event[field])
  return Number.isFinite(value) ? value : 0
}

export function list(event: RunEvent, field: string): string[] {
  const value = event[field]
  return Array.isArray(value) ? value.map(item => (typeof item === 'string' ? item : JSON.stringify(item))) : []
}

export function count(events: RunEvent[], name: string): number {
  return events.filter(e => e.event === name).length
}

/** The events of an events.jsonl; a line cut off by a crash mid-write is skipped. */
export function parseJsonl(text: string): RunEvent[] {
  return parseJsonLines<RunEvent>(text)
}

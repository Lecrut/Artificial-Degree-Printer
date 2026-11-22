import { spawn, type ChildProcess } from 'node:child_process'
import { join } from 'node:path'
import type { LaunchRequest, LaunchStatus } from '#shared/types/live'
import { launchArgs } from '#shared/utils/launch'
import { REPO_ROOT } from './repo'

const MAX_LINES = 500
const PYTHON = process.env.ADK_PYTHON ?? join(REPO_ROOT, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')

// One benchmark at a time, started from the viewer; the harness itself is untouched (it runs as `main.py`).
let child: ChildProcess | null = null
const status: LaunchStatus = { running: false, pid: null, args: [], startedAt: null, exitCode: null, lines: [] }

function collect(chunk: Buffer) {
  status.lines.push(...chunk.toString('utf-8').split(/\r?\n/).filter(Boolean))
  status.lines.splice(0, Math.max(0, status.lines.length - MAX_LINES))
}

export function launchStatus(): LaunchStatus {
  return { ...status, lines: status.lines.slice(-200) }
}

export function startLaunch(request: LaunchRequest): LaunchStatus {
  if (status.running) throw createError({ statusCode: 409, statusMessage: 'A benchmark is already running' })
  const args = launchArgs(request)
  child = spawn(PYTHON, args, { cwd: REPO_ROOT, env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1' } })
  Object.assign(status, { running: true, pid: child.pid ?? null, args, startedAt: new Date().toISOString(), exitCode: null, lines: [] })
  child.stdout?.on('data', collect)
  child.stderr?.on('data', collect)
  child.on('error', (error) => {
    status.lines.push(`[viewer] ${error.message}`)
    status.running = false
  })
  child.on('exit', (code) => {
    Object.assign(status, { running: false, exitCode: code })
    child = null
  })
  return launchStatus()
}

export function stopLaunch(): LaunchStatus {
  if (child?.pid) {
    // On Windows the benchmark spawns its own children (pytest, the experiment): the whole tree goes.
    if (process.platform === 'win32') spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'])
    else child.kill('SIGTERM')
    status.lines.push('[viewer] zatrzymano')
  }
  return launchStatus()
}

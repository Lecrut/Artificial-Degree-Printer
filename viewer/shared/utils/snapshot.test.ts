import { describe, expect, it } from 'bun:test'
import { snapshotRoute } from './snapshot'

const route = (url: string) => {
  const u = new URL(url, 'http://x')
  return snapshotRoute(u.pathname, u.searchParams)
}

describe('snapshotRoute', () => {
  it('maps every git-history address of the API', () => {
    expect(route('/api/history')).toEqual({ kind: 'history' })
    expect(route('/api/changelog')).toEqual({ kind: 'changelog' })
    expect(route('/api/runs/git/abc1234')).toEqual({ kind: 'commit', ref: 'abc1234' })
    expect(route('/api/runs/git/abc1234/01_rl_tictactoe')).toEqual({ kind: 'bundle', ref: 'abc1234', task: '01_rl_tictactoe' })
    expect(route('/api/runs/git/abc1234/01_x/calls')).toEqual({ kind: 'calls', ref: 'abc1234', task: '01_x' })
    expect(route('/api/runs/git/abc1234/01_x/calls/17')).toEqual({ kind: 'detail', ref: 'abc1234', task: '01_x', step: '17' })
    expect(route(`/api/runs/git/abc1234/01_x/file?path=${encodeURIComponent('thesis/figures/a b.png')}`))
      .toEqual({ kind: 'file', ref: 'abc1234', task: '01_x', path: 'thesis/figures/a b.png' })
  })

  it('answers the results on disk with nothing and refuses what only runs locally', () => {
    expect(route('/api/runs/results/current')).toEqual({ kind: 'empty' })
    expect(route('/api/runs/results/current/01_x')).toBeNull()
    expect(route('/api/live/stream')).toBeNull()
    expect(route('/api/launch')).toBeNull()
    expect(route('/api/runs/git/abc1234/01_x/file')).toBeNull()
  })
})

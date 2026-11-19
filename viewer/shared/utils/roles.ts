import type { StateColor } from './states'

/** Colors of the roles a vertex has in a bag: producer, consumer, test, output, citing chapter. */
const ROLE: Record<string, StateColor> = { P: 'primary', C: 'secondary', T: 'info', O: 'warning', X: 'success' }

export function roleColor(role: string): StateColor {
  return ROLE[role] ?? 'grey'
}

export const BAG_COLOR: Record<string, StateColor> = { I: 'primary', R: 'info', N: 'secondary' }

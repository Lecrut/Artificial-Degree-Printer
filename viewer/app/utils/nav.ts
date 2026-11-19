import { mdiBookOpenPageVariantOutline, mdiCompareHorizontal, mdiHistory, mdiPulse } from '@mdi/js'
import { labels } from './labels'

export interface NavPage {
  to: string
  icon: string
  title: string
  exact: boolean
}

// The pages of the viewer, in menu order; the side rail, the bottom bar and the search palette all read this list.
export const NAV_PAGES: NavPage[] = [
  { to: '/', icon: mdiHistory, title: labels.tabs.history, exact: true },
  { to: '/compare', icon: mdiCompareHorizontal, title: labels.tabs.compare, exact: false },
  { to: '/changelog', icon: mdiBookOpenPageVariantOutline, title: labels.tabs.changelog, exact: false },
  { to: '/live', icon: mdiPulse, title: labels.tabs.live, exact: false },
]

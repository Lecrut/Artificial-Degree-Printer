import { mdiBookOpenPageVariantOutline, mdiCompareHorizontal, mdiHistory, mdiPulse, mdiSitemapOutline } from '@mdi/js'
import { labels } from './labels'

export interface NavPage {
  to: string
  icon: string
  title: string
  exact: boolean
  /** Only on the computer running the harness; the deployed viewer has no such page. */
  localOnly?: boolean
}

// The pages of the viewer, in menu order; the side rail, the bottom bar and the search palette all read this list.
export const NAV_PAGES: NavPage[] = [
  { to: '/', icon: mdiHistory, title: labels.tabs.history, exact: true },
  { to: '/compare', icon: mdiCompareHorizontal, title: labels.tabs.compare, exact: false },
  { to: '/changelog', icon: mdiBookOpenPageVariantOutline, title: labels.tabs.changelog, exact: false },
  { to: '/flow', icon: mdiSitemapOutline, title: labels.tabs.flow, exact: false, localOnly: true },
  { to: '/live', icon: mdiPulse, title: labels.tabs.live, exact: false, localOnly: true },
]

// Addresses the deployed viewer turns away (the old /launch opens the live page's panel).
export const LOCAL_ONLY = ['/live', '/launch', '/flow']

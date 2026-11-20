import { NAV_PAGES } from '~/utils/nav'

/** The pages of the menu; the deployed viewer leaves out those that only work next to the harness. */
export function useNavPages() {
  const deployed = useDeployed()
  return computed(() => NAV_PAGES.filter(page => !(deployed && page.localOnly)))
}

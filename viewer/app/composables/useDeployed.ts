/** Whether this is the deployed viewer (history only, from the snapshot) rather than the one next to the harness. */
export function useDeployed(): boolean {
  return !!useRuntimeConfig().public.deployed
}

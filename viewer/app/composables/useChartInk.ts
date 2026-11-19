import { useTheme } from 'vuetify'
import type { ChartInk } from '~/utils/chartOptions'

const alpha = (hex: string, opacity: number) => {
  const digits = hex.replace('#', '')
  const full = digits.length === 3 ? [...digits].map(d => d + d).join('') : digits
  const n = Number.parseInt(full, 16)
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${opacity})`
}

/** The theme's inks for charts: text stays in text colors, grid and axes recede. */
export function useChartInk() {
  const theme = useTheme()
  return computed<ChartInk>(() => {
    const c = theme.current.value.colors as Record<string, string>
    const onSurface = c['on-surface'] ?? '#ffffff'
    return {
      text: alpha(onSurface, 0.94),
      muted: alpha(onSurface, 0.62),
      grid: alpha(onSurface, 0.08),
      axis: alpha(onSurface, 0.24),
      tooltip: c['surface-bright'] ?? '#11204a',
    }
  })
}

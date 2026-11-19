import type { EChartsOption } from 'echarts'
import type { Point } from '#shared/types/compare'
import { valueAt } from '#shared/utils/compare'

/** Theme colors a chart needs; values and labels wear text inks, never a series color. */
export interface ChartInk {
  text: string
  muted: string
  grid: string
  axis: string
  tooltip: string
}

export interface LineSeries {
  name: string
  color: string
  points: Point[]
}

export interface BarSeries {
  name: string
  color: string
  values: number[]
}

export type Format = (value: number) => string

export const base = (ink: ChartInk): EChartsOption => ({
  backgroundColor: 'transparent',
  textStyle: { color: ink.muted, fontFamily: 'Roboto, sans-serif' },
  animationDuration: 700,
  legend: { top: 0, icon: 'roundRect', itemWidth: 14, itemHeight: 4, textStyle: { color: ink.text } },
  tooltip: {
    backgroundColor: ink.tooltip,
    borderWidth: 0,
    padding: [8, 12],
    textStyle: { color: ink.text },
    extraCssText: 'border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,.35);',
  },
})

export const valueAxis = (ink: ChartInk, format: Format) => ({
  type: 'value' as const,
  axisLabel: { color: ink.muted, formatter: (v: number) => format(v) },
  splitLine: { lineStyle: { color: ink.grid } },
  axisLine: { show: false },
})

const timeAxis = (ink: ChartInk, name: string) => ({
  type: 'value' as const,
  name,
  nameLocation: 'middle' as const,
  nameGap: 28,
  nameTextStyle: { color: ink.muted },
  axisLabel: { color: ink.muted, formatter: (v: number) => `${Math.round(v)}` },
  axisLine: { lineStyle: { color: ink.axis } },
  splitLine: { show: false },
})

export const escape = (text: string) => text.replace(/[&<>"]/g, c => `&#${c.charCodeAt(0)};`)

// Every run at the hovered minute, not only the one whose point is nearest. ECharts renders this HTML itself.
function lineTooltip(ink: ChartInk, series: LineSeries[], minute: number, xName: string, format: Format): string {
  const rows = series.map((s) => {
    const value = valueAt(s.points, minute)
    const ended = minute > (s.points.at(-1)?.[0] ?? 0)
    return `<div style="display:flex;gap:10px;align-items:center"><span style="width:10px;height:10px;border-radius:50%;background:${s.color}"></span>`
      + `<span style="flex:1">${escape(s.name)}</span><b>${value === null ? '—' : format(value)}</b>${ended ? `<span style="color:${ink.muted}">✓</span>` : ''}</div>`
  })
  return `<div style="color:${ink.muted};margin-bottom:6px">${Math.round(minute)} · ${xName}</div>${rows.join('')}`
}

/** Running totals of several runs on one time axis: stepped 2px lines, a crosshair, drag or wheel to zoom. */
export function lineOverlay(ink: ChartInk, series: LineSeries[], xName: string, format: Format): EChartsOption {
  return {
    ...base(ink),
    grid: { top: 40, right: 24, bottom: 48, left: 16, containLabel: true },
    tooltip: {
      ...base(ink).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: ink.axis } },
      formatter: (params) => {
        const first = (Array.isArray(params) ? params[0] : params) as { axisValue?: number } | undefined
        const minute = Number(first?.axisValue ?? 0)
        return lineTooltip(ink, series, minute, xName, format)
      },
    },
    xAxis: timeAxis(ink, xName),
    yAxis: valueAxis(ink, format),
    dataZoom: [{ type: 'inside', filterMode: 'none' }],
    series: series.map(s => ({
      type: 'line',
      name: s.name,
      data: s.points,
      step: 'end',
      showSymbol: false,
      symbolSize: 8,
      color: s.color,
      lineStyle: { width: 2 },
      emphasis: { focus: 'series' },
      endLabel: { show: series.length > 1, color: ink.text, formatter: ({ value }) => format((value as Point)[1]) },
      labelLayout: { moveOverlap: 'shiftY' },
    })),
  }
}

/** One value per category for several runs, side by side; categories read top-down. */
export function groupedBars(ink: ChartInk, categories: string[], series: BarSeries[], format: Format, stacked = false): EChartsOption {
  return {
    ...base(ink),
    grid: { top: 40, right: 24, bottom: 8, left: 8, containLabel: true },
    tooltip: { ...base(ink).tooltip, trigger: 'axis', axisPointer: { type: 'shadow', shadowStyle: { color: ink.grid } }, valueFormatter: v => format(Number(v)) },
    xAxis: valueAxis(ink, format),
    yAxis: { type: 'category', data: categories, inverse: true, axisLabel: { color: ink.text }, axisLine: { lineStyle: { color: ink.axis } }, axisTick: { show: false } },
    series: series.map(s => ({
      type: 'bar',
      name: s.name,
      data: s.values,
      color: s.color,
      stack: stacked ? 'all' : undefined,
      barMaxWidth: 14,
      barGap: '20%',
      itemStyle: { borderRadius: stacked ? 0 : [0, 4, 4, 0], borderColor: 'transparent' },
      emphasis: { focus: 'series' },
    })),
  }
}

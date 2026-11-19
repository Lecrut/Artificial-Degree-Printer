import type { EChartsOption } from 'echarts'
import { SERIES_COLORS } from '#shared/utils/compare'
import type { TrendPoint } from '#shared/utils/historyStats'
import { base, escape, valueAxis, type ChartInk, type Format } from './chartOptions'

const COLOR = SERIES_COLORS[0]

// The hovered commit: which one, when, how the run ended, and the value.
function tooltip(ink: ChartInk, point: TrendPoint, metric: string, format: Format, hint: string): string {
  return `<div style="font-weight:600">${escape(point.message)}</div>`
    + `<div style="color:${ink.muted};margin-bottom:6px">${point.date.slice(0, 16).replace('T', ' ')} · ${point.short} · ${escape(point.status)}</div>`
    + `<div style="display:flex;gap:10px;align-items:center"><span style="width:10px;height:10px;border-radius:50%;background:${COLOR}"></span>`
    + `<span style="flex:1">${escape(metric)}</span><b>${format(point.value)}</b></div>`
    + `<div style="color:${ink.muted};margin-top:6px;font-size:11px">${escape(hint)}</div>`
}

/** One task's value across commits, oldest first: a 2px line with points, a crosshair and a tooltip per commit. */
export function trendLine(ink: ChartInk, points: TrendPoint[], metric: string, format: Format, hint: string): EChartsOption {
  return {
    ...base(ink),
    legend: { show: false },
    grid: { top: 16, right: 24, bottom: 8, left: 8, containLabel: true },
    tooltip: {
      ...base(ink).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: ink.axis } },
      formatter: (params) => {
        const first = (Array.isArray(params) ? params[0] : params) as { dataIndex?: number } | undefined
        const point = points[first?.dataIndex ?? -1]
        return point ? tooltip(ink, point, metric, format, hint) : ''
      },
    },
    xAxis: {
      type: 'category',
      data: points.map(p => p.label),
      boundaryGap: false,
      axisLabel: { color: ink.muted, hideOverlap: true },
      axisLine: { lineStyle: { color: ink.axis } },
      axisTick: { show: false },
    },
    yAxis: valueAxis(ink, format),
    series: [{
      type: 'line',
      name: metric,
      data: points.map(p => p.value),
      color: COLOR,
      lineStyle: { width: 2 },
      symbol: 'circle',
      symbolSize: 8,
      showSymbol: points.length <= 30,
      itemStyle: { borderColor: ink.tooltip, borderWidth: 2 },
      emphasis: { scale: 1.6 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${COLOR}55` }, { offset: 1, color: `${COLOR}00` }] } },
      cursor: 'pointer',
    }],
  }
}

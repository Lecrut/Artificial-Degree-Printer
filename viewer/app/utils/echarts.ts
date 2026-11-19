import { BarChart, LineChart } from 'echarts/charts'
import { AxisPointerComponent, DataZoomComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

// Only the pieces the compare page draws: lines over time and grouped bars.
use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, AxisPointerComponent, DataZoomComponent, CanvasRenderer])

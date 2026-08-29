import * as echarts from 'echarts'

export const PALETTE = ['#00e5ff', '#00ff9d', '#ffc53d', '#ff3b5c', '#7c8cff', '#ff8f5c', '#c792ea']

export function baseOption() {
  return {
    backgroundColor: 'transparent',
    animation: false,
    grid: { left: 52, right: 14, top: 26, bottom: 22 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 14, 23, 0.94)',
      borderColor: 'rgba(0, 229, 255, 0.3)',
      borderWidth: 1,
      textStyle: { color: '#e6f1ff', fontSize: 11 },
      axisPointer: { lineStyle: { color: 'rgba(0, 229, 255, 0.4)' } }
    },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: 'rgba(143, 163, 200, 0.3)' } },
      axisLabel: {
        color: '#8fa3c8',
        fontSize: 10,
        formatter: (v) => {
          const d = new Date(v)
          return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
        }
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8fa3c8', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(143, 163, 200, 0.12)' } }
    }
  }
}

export function lineSeries(name, data, color, opts = {}) {
  const s = {
    name,
    type: 'line',
    data,
    smooth: opts.step ? false : 0.2,
    step: opts.step ? 'start' : false,
    symbol: 'none',
    connectNulls: false,
    lineStyle: { width: 1.5, color, shadowBlur: 8, shadowColor: `${color}55` },
    itemStyle: { color },
    emphasis: { focus: 'series' }
  }
  if (opts.stack) s.stack = opts.stack
  if (opts.area) {
    s.areaStyle = {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: `${color}40` },
        { offset: 1, color: `${color}00` }
      ])
    }
  }
  if (opts.yAxisIndex !== undefined) s.yAxisIndex = opts.yAxisIndex
  if (opts.markLine) s.markLine = opts.markLine
  return s
}

export function initChart(el) {
  return echarts.init(el, null, { renderer: 'canvas' })
}

export function gaugeOption(value, color, zones) {
  const has = value !== null && value !== undefined && Number.isFinite(value)
  const v = has ? Math.max(0, Math.min(100, value)) : 0
  const zoneColors = zones || [
    [0.8, 'rgba(0,229,255,0.10)'],
    [0.9, 'rgba(255,197,61,0.16)'],
    [1, 'rgba(255,59,92,0.18)']
  ]
  return {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 300,
    animationDurationUpdate: 300,
    animationEasingUpdate: 'cubicOut',
    series: [
      {
        type: 'gauge',
        min: 0,
        max: 100,
        startAngle: 210,
        endAngle: -30,
        radius: '80%',
        center: ['50%', '58%'],
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 12,
            color: zoneColors
          }
        },
        pointer: {
          length: '58%',
          width: 3,
          itemStyle: {
            color,
            shadowBlur: 6,
            shadowColor: `${color}88`
          }
        },
        anchor: {
          show: true,
          size: 8,
          itemStyle: { color: '#0d1526', borderColor: color, borderWidth: 2 }
        },
        progress: {
          show: true,
          width: 12,
          roundCap: true,
          itemStyle: {
            color,
            shadowBlur: 10,
            shadowColor: `${color}55`
          }
        },
        axisTick: {
          show: true,
          splitNumber: 5,
          distance: -14,
          length: 3,
          lineStyle: { color: 'rgba(143,163,200,0.28)', width: 1 }
        },
        splitLine: {
          show: true,
          distance: -15,
          length: 7,
          lineStyle: { color: 'rgba(143,163,200,0.5)', width: 1 }
        },
        axisLabel: {
          show: true,
          distance: 10,
          color: '#5a6b8c',
          fontSize: 9,
          fontFamily: 'JetBrains Mono, Roboto Mono, monospace'
        },
        title: { show: false },
        detail: { show: false },
        data: [{ value: Math.round(v * 10) / 10 }]
      }
    ]
  }
}

<template>
  <div class="gpu glass" :class="levelClass">
    <div class="gpu-head">
      <span class="gpu-name">GPU{{ gpu.index }} · {{ gpu.name || 'NVIDIA GPU' }}</span>
      <span class="mono faint small">{{ gpu.driver }}</span>
    </div>

    <div class="gpu-body">
      <div class="gauge-wrap">
        <svg class="gauge" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(143,163,200,0.15)" stroke-width="8" />
          <circle
            cx="50" cy="50" r="42" fill="none"
            :stroke="gaugeColor" stroke-width="8" stroke-linecap="round"
            :stroke-dasharray="dash"
            transform="rotate(-90 50 50)"
            style="transition: stroke-dasharray 0.3s ease; filter: drop-shadow(0 0 4px currentColor)"
          />
        </svg>
        <div class="gauge-center">
          <span class="mono val" :class="levelClass">{{ utilText }}</span>
          <span class="unit">利用率</span>
        </div>
      </div>

      <div class="gpu-metrics">
        <div class="mem-block">
          <div class="mem-label mono small dim">
            显存 {{ fmtNum(gpu.mem_used_mb, 0) }} / {{ fmtNum(gpu.mem_total_mb, 0) }} MB
            <span :class="memLevelClass">{{ memPctText }}</span>
          </div>
          <div class="bar"><i :class="memBarClass" :style="{ width: memPctNum + '%' }"></i></div>
        </div>

        <div class="grid2">
          <div class="kv"><span class="k">温度</span><span class="v mono" :class="tempLevelClass">{{ tempText }}°C</span></div>
          <div class="kv"><span class="k">功耗</span><span class="v mono">{{ powerText }} W</span></div>
          <div class="kv"><span class="k">风扇</span><span class="v mono">{{ fanText }}</span></div>
          <div class="kv"><span class="k">频率</span><span class="v mono">{{ clockText }}</span></div>
          <div class="kv"><span class="k">PCIe</span><span class="v mono">gen{{ gpu.pcie_gen ?? '—' }} x{{ gpu.pcie_width ?? '—' }}</span></div>
          <div class="kv"><span class="k">P-State</span><span class="v mono">{{ gpu.pstate || '—' }}</span></div>
        </div>

        <div v-if="apps.length" class="apps">
          <div class="apps-title small dim">占用进程</div>
          <div v-for="a in apps" :key="a.pid" class="kv small mono">
            <span class="k">{{ a.name }}</span>
            <span class="v">pid {{ a.pid }} · {{ fmtNum(a.mem_mb, 0) }} MB</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { fmtNum, alertOf } from '../utils'

const props = defineProps({
  gpu: { type: Object, required: true },
  alerts: { type: Array, default: () => [] }
})

const idx = computed(() => props.gpu.index ?? 0)
const util = computed(() => props.gpu.util_pct ?? null)
const utilText = computed(() => (util.value === null ? '—' : Math.round(util.value) + '%'))

const CIRC = 2 * Math.PI * 42
const dash = computed(() => {
  const p = util.value === null ? 0 : Math.min(100, util.value)
  return `${(p / 100) * CIRC} ${CIRC}`
})
const gaugeColor = computed(() => {
  const p = util.value
  if (p === null) return 'var(--text-faint)'
  if (p >= 90) return 'var(--red)'
  if (p >= 80) return 'var(--amber)'
  return 'var(--cyan)'
})

const memTotal = computed(() => props.gpu.mem_total_mb || 0)
const memUsed = computed(() => props.gpu.mem_used_mb ?? 0)
const memPctNum = computed(() => (memTotal.value ? Math.min(100, (memUsed.value / memTotal.value) * 100) : 0))
const memPctText = computed(() => (memTotal.value ? (memPctNum.value).toFixed(1) + '%' : '—'))
const memLevel = computed(() => {
  const p = memPctNum.value
  if (p >= 95) return 'danger'
  if (p >= 85) return 'warn'
  return 'normal'
})
const memLevelClass = computed(() => (memLevel.value === 'danger' ? 'lv-danger' : memLevel.value === 'warn' ? 'lv-warn' : 'lv-green'))
const memBarClass = computed(() => (memLevel.value === 'danger' ? 'danger' : memLevel.value === 'warn' ? 'warn' : 'green'))

const temp = computed(() => props.gpu.temp_c ?? null)
const tempText = computed(() => (temp.value === null ? '—' : Math.round(temp.value)))
const tempLevelClass = computed(() => {
  const t = temp.value
  if (t === null) return ''
  if (t >= 85) return 'lv-danger'
  if (t >= 75) return 'lv-warn'
  return ''
})

const powerText = computed(() => {
  const p = props.gpu.power_w
  const lim = props.gpu.power_limit_w
  if (p === null || p === undefined) return '—'
  return `${p.toFixed(1)}${lim ? ' / ' + lim.toFixed(0) : ''}`
})
const fanText = computed(() => (props.gpu.fan_pct === null || props.gpu.fan_pct === undefined ? '—' : Math.round(props.gpu.fan_pct) + '%'))
const clockText = computed(() => {
  const c = props.gpu.clock_mhz
  const mc = props.gpu.mem_clock_mhz
  if (!c && !mc) return '—'
  return `${c ?? '—'} / ${mc ?? '—'} MHz`
})

const apps = computed(() => props.gpu.apps || [])

// 卡片级别：取该卡所有告警的最高级别
const cardLevel = computed(() => {
  let level = 'normal'
  for (const a of props.alerts || []) {
    if (!a.metric.startsWith(`gpu${idx.value}.`)) continue
    if (a.level === 'danger') return 'danger'
    if (a.level === 'warn') level = 'warn'
  }
  return level
})
const levelClass = computed(() => (cardLevel.value === 'danger' ? 'card-danger' : cardLevel.value === 'warn' ? 'card-warn' : ''))
</script>

<style scoped>
.gpu { padding: 14px 16px; }
.gpu-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.gpu-name { font-size: 13px; font-weight: 600; }
.gpu-body { display: flex; gap: 18px; align-items: center; }
.gauge-wrap { position: relative; width: 108px; height: 108px; flex: none; }
.gauge { width: 100%; height: 100%; }
.gauge-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.gauge-center .val { font-size: 22px; font-weight: 700; color: var(--text); }
.gauge-center .unit { font-size: 10px; color: var(--text-faint); }
.gpu-metrics { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.mem-label { display: flex; gap: 8px; margin-bottom: 4px; }
.mem-label span:last-child { margin-left: auto; font-weight: 700; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.apps { border-top: 1px solid rgba(143, 163, 200, 0.1); padding-top: 6px; }
.apps-title { margin-bottom: 2px; }
</style>

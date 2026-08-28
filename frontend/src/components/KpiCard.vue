<template>
  <div class="kpi glass" :class="levelClass">
    <div class="kpi-title">{{ title }}<span v-if="source" class="src mono">{{ source }}</span></div>
    <div class="kpi-value">
      <span class="mono num" :class="levelClass">{{ text }}</span>
      <span v-if="unit" class="unit">{{ unit }}</span>
    </div>
    <svg v-if="sparkD" class="spark" :viewBox="`0 0 ${sparkW} ${sparkH}`" preserveAspectRatio="none">
      <path :d="sparkD" fill="none" :stroke="sparkColor" stroke-width="1.5" />
    </svg>
    <div v-if="sub" class="kpi-sub mono">{{ sub }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { sparkPath, useCountUp } from '../utils'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, default: null },
  unit: { type: String, default: '' },
  digits: { type: Number, default: 1 },
  level: { type: String, default: 'normal' }, // normal | warn | danger
  spark: { type: Array, default: () => [] },
  sub: { type: String, default: '' },
  source: { type: String, default: '' }
})

const animated = useCountUp(computed(() => (typeof props.value === 'number' ? props.value : 0)))
const text = computed(() => {
  if (props.value === null || props.value === undefined) return '—'
  const n = Number(animated.value)
  return Number.isFinite(n) ? n.toFixed(props.digits) : '—'
})

const sparkW = 150
const sparkH = 26
const sparkD = computed(() => sparkPath(props.spark || [], sparkW, sparkH))
const sparkColor = computed(() => {
  if (props.level === 'danger') return 'var(--red)'
  if (props.level === 'warn') return 'var(--amber)'
  return 'var(--cyan)'
})
const levelClass = computed(() => (props.level === 'danger' ? 'lv-danger' : props.level === 'warn' ? 'lv-warn' : ''))
</script>

<style scoped>
.kpi { padding: 12px 16px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.kpi-title {
  font-size: 11px;
  color: var(--text-dim);
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.src {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 6px;
  border: 1px solid rgba(0, 229, 255, 0.3);
  color: var(--cyan);
  letter-spacing: 0;
}
.kpi-value { display: flex; align-items: baseline; gap: 6px; }
.num { font-size: 24px; font-weight: 700; color: var(--text); line-height: 1.1; }
.lv-danger .num { text-shadow: 0 0 12px rgba(255, 59, 92, 0.5); }
.lv-warn .num { text-shadow: 0 0 12px rgba(255, 197, 61, 0.4); }
.unit { color: var(--text-dim); font-size: 11px; }
.spark { width: 100%; height: 26px; margin-top: 2px; }
.kpi-sub { color: var(--text-faint); font-size: 11px; }
</style>

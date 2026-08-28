<template>
  <div class="ctx-card glass" :class="levelClass">
    <div class="head">
      <span class="title">上下文占用</span>
      <span v-if="truncated" class="badge danger small">已截断</span>
    </div>
    <template v-if="used !== null && total">
      <div class="nums mono">
        <span class="used" :class="levelClass">{{ fmtNum(used) }}</span>
        <span class="sep">/ {{ fmtNum(total) }}</span>
        <span class="pct" :class="levelClass">{{ pctText }}</span>
      </div>
      <div class="bar"><i :class="barLevel" :style="{ width: pctNum + '%' }"></i></div>
      <div class="kv">
        <span class="k">剩余</span>
        <span class="v mono">{{ fmtNum(remaining) }} tokens</span>
      </div>
    </template>
    <div v-else class="placeholder small"><span class="icon">⌁</span>暂无数据（等待任务结束）</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { fmtNum } from '../utils'

const props = defineProps({
  context: { type: Object, default: () => ({}) }
})

const used = computed(() => props.context.used ?? null)
const total = computed(() => props.context.total ?? null)
const remaining = computed(() => props.context.remaining ?? null)
const truncated = computed(() => !!props.context.truncated)
const pctNum = computed(() => {
  const p = props.context.pct
  return p === null || p === undefined ? 0 : Math.min(100, p)
})
const pctText = computed(() => {
  const p = props.context.pct
  return p === null || p === undefined ? '—' : p.toFixed(1) + '%'
})
const level = computed(() => {
  const p = pctNum.value
  if (p >= 90) return 'danger'
  if (p >= 80) return 'warn'
  return 'normal'
})
const levelClass = computed(() => (level.value === 'danger' ? 'lv-danger' : level.value === 'warn' ? 'lv-warn' : ''))
const barLevel = computed(() => (level.value === 'danger' ? 'danger' : level.value === 'warn' ? 'warn' : ''))
</script>

<style scoped>
.ctx-card { padding: 12px 16px; display: flex; flex-direction: column; gap: 6px; }
.head { display: flex; align-items: center; justify-content: space-between; }
.title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; }
.nums { display: flex; align-items: baseline; gap: 6px; }
.used { font-size: 22px; font-weight: 700; color: var(--text); }
.sep { color: var(--text-faint); font-size: 12px; }
.pct { font-size: 16px; font-weight: 700; color: var(--cyan); margin-left: auto; }
</style>

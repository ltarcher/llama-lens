<template>
  <div class="mtp-card glass" :class="levelClass">
    <div class="head">
      <span class="title">MTP 投机解码</span>
      <span class="badge dim small mono">{{ specType }} · n_max {{ specNMax }}</span>
    </div>
    <template v-if="acceptance !== null">
      <div class="nums">
        <span class="mono acc" :class="levelClass">{{ (acceptance * 100).toFixed(1) }}<span class="pctsign">%</span></span>
        <span class="label dim small">接受率</span>
      </div>
      <div class="bar"><i :class="barLevel" :style="{ width: acceptance * 100 + '%' }"></i></div>
      <div class="row mono small">
        <span class="dim">接受 {{ accepted ?? '—' }}</span>
        <span class="dim">/ 生成 {{ generated ?? '—' }}</span>
        <span class="dim">mean len {{ meanLen === null ? '—' : meanLen.toFixed(2) }}</span>
      </div>
    </template>
    <div v-else class="placeholder small"><span class="icon">⌁</span>暂无数据（等待任务结束）</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mtp: { type: Object, default: () => ({}) },
  flags: { type: Object, default: () => ({}) }
})

const acceptance = computed(() => props.mtp.acceptance ?? null)
const accepted = computed(() => props.mtp.accepted ?? null)
const generated = computed(() => props.mtp.generated ?? null)
const meanLen = computed(() => props.mtp.mean_len ?? null)
const specType = computed(() => props.flags.spec_type || 'draft-mtp')
const specNMax = computed(() => props.flags.spec_draft_n_max || '—')

const level = computed(() => {
  const a = acceptance.value
  if (a === null) return 'normal'
  const pct = a * 100
  if (pct < 65) return 'danger'
  if (pct < 80) return 'warn'
  return 'normal'
})
const levelClass = computed(() => (level.value === 'danger' ? 'lv-danger' : level.value === 'warn' ? 'lv-warn' : ''))
const barLevel = computed(() => (level.value === 'danger' ? 'danger' : level.value === 'warn' ? 'warn' : 'green'))
</script>

<style scoped>
.mtp-card { padding: 12px 16px; display: flex; flex-direction: column; gap: 6px; }
.head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; }
.nums { display: flex; align-items: baseline; gap: 8px; }
.acc { font-size: 22px; font-weight: 700; color: var(--green); }
.pctsign { font-size: 13px; }
.label { color: var(--text-dim); }
.row { display: flex; gap: 14px; }
</style>

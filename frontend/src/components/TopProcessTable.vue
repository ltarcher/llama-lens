<template>
  <div class="top glass">
    <div class="panel-head">
      <span class="panel-title">{{ mode === 'cpu' ? 'Top CPU' : 'Top 内存' }}</span>
      <span class="mono faint small">Top {{ rows.length }}</span>
    </div>
    <table class="tbl mono">
      <thead>
        <tr><th>PID</th><th>进程</th><th class="num">CPU%</th><th class="num">MEM%</th><th class="num">RSS</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.pid">
          <td class="dim">{{ r.pid }}</td>
          <td :class="{ hl: r.name === 'llama-server' }">{{ r.name }}</td>
          <td class="num" :class="cpuClass(r.cpu_pct)">{{ r.cpu_pct.toFixed(1) }}</td>
          <td class="num">{{ r.mem_pct.toFixed(1) }}</td>
          <td class="num dim">{{ fmtBytes(r.rss_mb * 1024 * 1024) }}</td>
        </tr>
        <tr v-if="!rows.length"><td colspan="5" class="faint">无数据</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { fmtBytes } from '../utils'

defineProps({
  rows: { type: Array, default: () => [] },
  mode: { type: String, default: 'cpu' } // cpu | mem
})

function cpuClass(v) {
  if (v >= 90) return 'lv-danger'
  if (v >= 50) return 'lv-warn'
  return ''
}
</script>

<style scoped>
.top { padding: 12px 16px; }
.panel-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 6px; }
.panel-title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; }
.hl { color: var(--cyan); font-weight: 600; }
</style>

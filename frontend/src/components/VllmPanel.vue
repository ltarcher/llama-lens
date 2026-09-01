<template>
  <div class="vllm-panel glass">
    <div class="panel-head">
      <span class="panel-title">vLLM 服务</span>
      <span class="badge" :class="onlineBadgeClass">{{ onlineBadgeText }}</span>
    </div>

    <template v-if="hasData">
      <div class="cache-block">
        <div class="cache-label mono small dim">
          KV 缓存占用 <span :class="kvLevelClass">{{ kvCacheText }}</span>
        </div>
        <div class="bar"><i :class="kvBarClass" :style="{ width: kvCachePct + '%' }"></i></div>
      </div>

      <div class="grid2">
        <div class="kv"><span class="k">运行中请求</span><span class="v mono">{{ runningText }}</span></div>
        <div class="kv"><span class="k">等待中请求</span><span class="v mono">{{ waitingText }}</span></div>
        <div class="kv"><span class="k">Prompt 累计</span><span class="v mono">{{ promptTotalText }}</span></div>
        <div class="kv"><span class="k">生成累计</span><span class="v mono">{{ genTotalText }}</span></div>
        <div class="kv"><span class="k">抢占次数</span><span class="v mono">{{ preemptionText }}</span></div>
        <div class="kv"><span class="k">最近采集</span><span class="v mono">{{ lastPollText }}</span></div>
      </div>
    </template>
    <div v-else class="placeholder"><span class="icon">⌁</span>vLLM 离线或无数据</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { fmtNum } from '../utils'

const props = defineProps({
  vllm: { type: Object, default: null }
})

const hasData = computed(() => !!(props.vllm && props.vllm.online))

const onlineBadgeClass = computed(() =>
  props.vllm && props.vllm.online ? 'ok' : 'danger'
)
const onlineBadgeText = computed(() =>
  props.vllm && props.vllm.online ? '在线' : '离线'
)

// KV 缓存（vllm:kv_cache_usage_perc，后端已换算 0-100）
const kvCachePct = computed(() => {
  const p = props.vllm ? props.vllm.gpu_cache_pct : null
  return p === null || p === undefined ? 0 : p
})
const kvCacheText = computed(() => kvCachePct.value.toFixed(1) + '%')
const kvLevel = computed(() => {
  const p = kvCachePct.value
  if (p >= 95) return 'danger'
  if (p >= 85) return 'warn'
  return 'normal'
})
const kvLevelClass = computed(() =>
  kvLevel.value === 'danger' ? 'lv-danger' :
  kvLevel.value === 'warn' ? 'lv-warn' : ''
)
const kvBarClass = computed(() =>
  kvLevel.value === 'danger' ? 'danger' :
  kvLevel.value === 'warn' ? 'warn' : ''
)

const numText = (v) => (v === null || v === undefined ? '—' : fmtNum(v))
const runningText = computed(() => numText(props.vllm && props.vllm.running_requests))
const waitingText = computed(() => numText(props.vllm && props.vllm.waiting_requests))
const promptTotalText = computed(() => numText(props.vllm && props.vllm.prompt_tokens_total))
const genTotalText = computed(() => numText(props.vllm && props.vllm.generation_tokens_total))
const preemptionText = computed(() => numText(props.vllm && props.vllm.preemptions_total))

const lastPollText = computed(() => {
  const ts = props.vllm && props.vllm.last_poll_ts
  if (!ts) return '—'
  const elapsed = (Date.now() - ts * 1000) / 1000
  if (elapsed < 30) return Math.max(0, Math.round(elapsed)) + 's 前'
  if (elapsed < 3600) return Math.round(elapsed / 60) + ' 分钟前'
  return Math.round(elapsed / 3600) + ' 小时前'
})
</script>

<style scoped>
.vllm-panel { padding: 12px 16px; }
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.panel-title { font-size: 11px; color: var(--text-dim); letter-spacing: 1px; }
.cache-block { margin-bottom: 10px; }
.cache-label { display: flex; justify-content: space-between; margin-bottom: 3px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.grid2 .kv { padding: 3px 0; font-size: 12px; }
</style>

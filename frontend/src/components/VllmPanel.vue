<template>
  <div class="vllm-panel glass">
    <div class="panel-head">
      <span class="panel-title">vLLM 服务</span>
      <span class="badge" :class="onlineBadgeClass">{{ onlineBadgeText }}</span>
    </div>

    <template v-if="hasData">
      <!-- ============ 模型信息 ============ -->
      <div class="model-block">
        <div class="model-name">{{ modelIdText }}</div>
        <div class="kv small"><span class="k">模型路径</span><span class="v mono">{{ modelPathText }}</span></div>
        <div class="grid2">
          <div class="kv"><span class="k">上下文长度</span><span class="v mono">{{ ctxText }}</span></div>
          <div class="kv"><span class="k">引擎状态</span><span class="v mono" :class="engineLevelClass">{{ engineStateText }}</span></div>
          <div class="kv"><span class="k">Sampling 权限</span><span class="v mono">{{ samplingText }}</span></div>
          <div class="kv"><span class="k">LogProbs 权限</span><span class="v mono">{{ logprobsText }}</span></div>
        </div>
      </div>

      <!-- ============ KV 缓存 ============ -->
      <div class="cache-block">
        <div class="cache-label mono small dim">
          KV 缓存占用 <span :class="kvLevelClass">{{ kvCacheText }}</span>
        </div>
        <div class="bar"><i :class="kvBarClass" :style="{ width: kvCachePct + '%' }"></i></div>
      </div>

      <!-- ============ 实时调度 ============ -->
      <div class="section-title">实时调度</div>
      <div class="grid2">
        <div class="kv"><span class="k">运行中请求</span><span class="v mono">{{ runningText }}</span></div>
        <div class="kv"><span class="k">等待中请求</span><span class="v mono">{{ waitingText }}</span></div>
        <div class="kv"><span class="k">Prompt 累计</span><span class="v mono">{{ promptTotalText }}</span></div>
        <div class="kv"><span class="k">生成累计</span><span class="v mono">{{ genTotalText }}</span></div>
        <div class="kv"><span class="k">抢占次数</span><span class="v mono">{{ preemptionText }}</span></div>
        <div class="kv"><span class="k">最近采集</span><span class="v mono">{{ lastPollText }}</span></div>
      </div>

      <!-- ============ 推理配置 ============ -->
      <div class="section-title">推理配置</div>
      <div class="grid2">
        <div class="kv"><span class="k">Prefix Caching</span><span class="v mono">{{ prefixCachingText }}</span></div>
        <div class="kv"><span class="k">Sliding Window</span><span class="v mono">{{ slidingWindowText }}</span></div>
        <div class="kv"><span class="k">Fine-tuning</span><span class="v mono">{{ fineTuneText }}</span></div>
        <div class="kv"><span class="k">Block Size</span><span class="v mono">{{ blockSizeText }}</span></div>
        <div class="kv"><span class="k">KV Cache 容量</span><span class="v mono">{{ kvCapText }}</span></div>
        <div class="kv"><span class="k">GPU 利用率上限</span><span class="v mono">{{ gpuCapText }}</span></div>
      </div>

      <!-- ============ 缓存类型 ============ -->
      <div class="section-title">缓存类型</div>
      <div class="grid2">
        <div class="kv"><span class="k">KV 数据类型</span><span class="v mono">{{ kvDtypeText }}</span></div>
        <div class="kv"><span class="k">Mamba 数据类型</span><span class="v mono">{{ mambaDtypeText }}</span></div>
        <div class="kv"><span class="k">Mamba 缓存模式</span><span class="v mono">{{ mambaModeText }}</span></div>
      </div>

      <!-- ============ 速度统计（总计） ============ -->
      <div class="section-title">速度统计（总计）</div>
      <div class="grid2">
        <div class="kv">
          <span class="k">Token 生成速度（总）</span>
          <span class="v mono cyan">{{ totalGenTpsText }} <span class="unit">t/s</span></span>
        </div>
        <div class="kv">
          <span class="k">Token 生成速度（平均）</span>
          <span class="v mono cyan">{{ avgGenTpsText }} <span class="unit">t/s</span></span>
        </div>
        <div class="kv">
          <span class="k">预填充速度（总）</span>
          <span class="v mono green">{{ totalPromptTpsText }} <span class="unit">t/s</span></span>
        </div>
        <div class="kv">
          <span class="k">预填充速度（平均）</span>
          <span class="v mono green">{{ avgPromptTpsText }} <span class="unit">t/s</span></span>
        </div>
      </div>

      <!-- ============ MTP 统计 ============ -->
      <div class="section-title">MTP / 投机解码</div>
      <div class="kv-grid">
        <div class="kv" v-if="mtpAcceptance !== null && mtpAcceptance !== undefined">
          <span class="k">MTP 接受率</span>
          <span class="v mono" :class="mtpClass">{{ mtpAcceptanceText }}</span>
        </div>
        <div class="kv" v-if="mtpAccepted !== null && mtpAccepted !== undefined">
          <span class="k">接受 / 生成</span>
          <span class="v mono">{{ fmtNum(mtpAccepted) }} / {{ fmtNum(mtpGenerated) }}</span>
        </div>
        <div class="kv" v-if="mtpMeanLen !== null && mtpMeanLen !== undefined">
          <span class="k">平均接受长度</span>
          <span class="v mono">{{ mtpMeanLen.toFixed(2) }}</span>
        </div>
        <div class="kv" v-if="mtpSpecDecodeTps !== null && mtpSpecDecodeTps !== undefined">
          <span class="k">投机解码速度</span>
          <span class="v mono">{{ mtpSpecDecodeTps.toFixed(2) }} <span class="unit">t/s</span></span>
        </div>
      </div>

      <!-- ============ 每个请求的统计 ============ -->
      <div class="section-title" v-if="requests.length">
        请求统计（Histogram 分位数）
      </div>
      <div v-if="requests.length" class="request-stats">
        <div class="stat-group">
          <div class="stat-group-title">Prompt Tokens</div>
          <div class="stat-row">
            <span class="stat-label">P50</span>
            <span class="stat-value mono">{{ fmtNum(reqStats.prompt_tokens.p50) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P90</span>
            <span class="stat-value mono">{{ fmtNum(reqStats.prompt_tokens.p90) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P99</span>
            <span class="stat-value mono">{{ fmtNum(reqStats.prompt_tokens.p99) }}</span>
          </div>
        </div>
        <div class="stat-group">
          <div class="stat-group-title">生成 Tokens</div>
          <div class="stat-row">
            <span class="stat-label">P50</span>
            <span class="stat-value mono cyan">{{ fmtNum(reqStats.generation_tokens.p50) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P90</span>
            <span class="stat-value mono cyan">{{ fmtNum(reqStats.generation_tokens.p90) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P99</span>
            <span class="stat-value mono cyan">{{ fmtNum(reqStats.generation_tokens.p99) }}</span>
          </div>
        </div>
        <div class="stat-group">
          <div class="stat-group-title">TTFT (首 token 延迟)</div>
          <div class="stat-row">
            <span class="stat-label">P50</span>
            <span class="stat-value mono">{{ reqStats.ttft_seconds.p50 === null ? '—' : reqStats.ttft_seconds.p50.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P90</span>
            <span class="stat-value mono">{{ reqStats.ttft_seconds.p90 === null ? '—' : reqStats.ttft_seconds.p90.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P99</span>
            <span class="stat-value mono">{{ reqStats.ttft_seconds.p99 === null ? '—' : reqStats.ttft_seconds.p99.toFixed(3) }}s</span>
          </div>
        </div>
        <div class="stat-group">
          <div class="stat-group-title">端到端延迟</div>
          <div class="stat-row">
            <span class="stat-label">P50</span>
            <span class="stat-value mono">{{ reqStats.e2e_latency_seconds.p50 === null ? '—' : reqStats.e2e_latency_seconds.p50.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P90</span>
            <span class="stat-value mono">{{ reqStats.e2e_latency_seconds.p90 === null ? '—' : reqStats.e2e_latency_seconds.p90.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">P99</span>
            <span class="stat-value mono">{{ reqStats.e2e_latency_seconds.p99 === null ? '—' : reqStats.e2e_latency_seconds.p99.toFixed(3) }}s</span>
          </div>
        </div>
        <div class="stat-group">
          <div class="stat-group-title">Prefill / Decode 时间</div>
          <div class="stat-row">
            <span class="stat-label">Prefill P50</span>
            <span class="stat-value mono green">{{ reqStats.prefill_time_seconds.p50 === null ? '—' : reqStats.prefill_time_seconds.p50.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Prefill P99</span>
            <span class="stat-value mono green">{{ reqStats.prefill_time_seconds.p99 === null ? '—' : reqStats.prefill_time_seconds.p99.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Decode P50</span>
            <span class="stat-value mono">{{ reqStats.decode_time_seconds.p50 === null ? '—' : reqStats.decode_time_seconds.p50.toFixed(3) }}s</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Decode P99</span>
            <span class="stat-value mono">{{ reqStats.decode_time_seconds.p99 === null ? '—' : reqStats.decode_time_seconds.p99.toFixed(3) }}s</span>
          </div>
        </div>
        <div class="stat-group">
          <div class="stat-group-title">请求总数</div>
          <div class="stat-row">
            <span class="stat-label">成功请求</span>
            <span class="stat-value mono">{{ fmtNum(reqStats.request_count) }}</span>
          </div>
        </div>
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

// ---------------- KV 缓存 ----------------
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

// ---------------- 模型信息 ----------------
const modelIdText = computed(() => (props.vllm && props.vllm.model_id) || '—')
const modelPathText = computed(() => (props.vllm && props.vllm.model_path) || '—')
const ctxText = computed(() => {
  const n = props.vllm && props.vllm.max_model_len
  return n ? fmtNum(n) : '—'
})
// 引擎状态：awake=在线；weights_offloaded/discard_all=休眠
const engineStateText = computed(() => {
  const s = props.vllm && props.vllm.engine_state
  if (!s) return '—'
  const map = {
    awake: '在线 (awake)',
    weights_offloaded: '休眠 (weights_offloaded)',
    discard_all: '休眠 (discard_all)'
  }
  return map[s] || s
})
const engineLevelClass = computed(() => {
  const s = props.vllm && props.vllm.engine_state
  if (s === 'awake') return ''
  if (s === 'weights_offloaded' || s === 'discard_all') return 'lv-warn'
  return ''
})

// ---------------- 权限 ----------------
const boolText = (v) => {
  if (v === null || v === undefined) return '—'
  return v ? '启用' : '禁用'
}
const samplingText = computed(() => boolText(props.vllm && props.vllm.allow_sampling))
const logprobsText = computed(() => boolText(props.vllm && props.vllm.allow_logprobs))
const fineTuneText = computed(() => boolText(props.vllm && props.vllm.allow_fine_tuning))

// ---------------- 实时调度 ----------------
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

// ---------------- 推理配置 ----------------
const prefixCachingText = computed(() => boolText(props.vllm && props.vllm.prefix_caching))
const slidingWindowText = computed(() => {
  const s = props.vllm && props.vllm.sliding_window
  if (!s || s === 'None') return '禁用'
  return s
})
const blockSizeText = computed(() => numText(props.vllm && props.vllm.block_size))
const kvCapText = computed(() => {
  const n = props.vllm && props.vllm.num_gpu_blocks
  return n ? fmtNum(n) + ' blocks' : '—'
})
const gpuCapText = computed(() => {
  const p = props.vllm && props.vllm.gpu_mem_utilization
  if (p === null || p === undefined) return '—'
  return (p * 100).toFixed(1) + '%'
})

// ---------------- 缓存类型 ----------------
const kvDtypeText = computed(() => (props.vllm && props.vllm.kv_cache_dtype) || '—')
const mambaDtypeText = computed(() => (props.vllm && props.vllm.mamba_cache_dtype) || '—')
const mambaModeText = computed(() => (props.vllm && props.vllm.mamba_cache_mode) || '—')

// ---------------- 速度统计（总计） ----------------
const totalGenTpsText = computed(() => {
  const v = props.vllm && props.vllm.total_gen_tps
  return v === null || v === undefined ? '—' : v.toFixed(2)
})
const totalPromptTpsText = computed(() => {
  const v = props.vllm && props.vllm.total_prompt_tps
  return v === null || v === undefined ? '—' : v.toFixed(2)
})
const avgGenTpsText = computed(() => {
  const v = props.vllm && props.vllm.avg_gen_tps
  return v === null || v === undefined ? '—' : v.toFixed(2)
})
const avgPromptTpsText = computed(() => {
  const v = props.vllm && props.vllm.avg_prompt_tps
  return v === null || v === undefined ? '—' : v.toFixed(2)
})

// ---------------- MTP 统计 ----------------
const mtpAcceptance = computed(() => props.vllm && props.vllm.mtp_acceptance_rate)
const mtpAccepted = computed(() => props.vllm && props.vllm.mtp_accepted)
const mtpGenerated = computed(() => props.vllm && props.vllm.mtp_generated)
const mtpMeanLen = computed(() => props.vllm && props.vllm.mtp_mean_len)
const mtpSpecDecodeTps = computed(() => props.vllm && props.vllm.mtp_spec_decode_tps)
const mtpAcceptanceText = computed(() => {
  const a = mtpAcceptance.value
  if (a === null || a === undefined) return '—'
  return (a * 100).toFixed(1) + '%'
})
const mtpClass = computed(() => {
  const a = mtpAcceptance.value
  if (a === null || a === undefined) return ''
  if (a < 0.65) return 'lv-danger'
  if (a < 0.8) return 'lv-warn'
  return 'lv-green'
})

// ---------------- 每个请求的统计 ----------------
const requests = computed(() => (props.vllm && props.vllm.requests) || [])
const reqStats = computed(() => {
  if (!requests.value.length) return {}
  return requests.value[0]
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
.model-block { margin-bottom: 10px; }
.model-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--cyan);
  margin-bottom: 4px;
}
.section-title {
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--text-faint);
  padding: 8px 0 4px;
  border-bottom: 1px solid rgba(143, 163, 200, 0.12);
  margin-bottom: 6px;
}
.cache-block { margin-bottom: 10px; }
.cache-label { display: flex; justify-content: space-between; margin-bottom: 3px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.grid2 .kv { padding: 3px 0; font-size: 12px; }
.small { font-size: 11px; }
.unit { font-size: 10px; color: var(--text-faint); }
.cyan { color: var(--cyan); }
.green { color: var(--green); }
.request-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 6px;
}
.stat-group {
  background: rgba(143, 163, 200, 0.05);
  border: 1px solid rgba(143, 163, 200, 0.1);
  border-radius: 6px;
  padding: 8px;
}
.stat-group-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
  font-size: 11px;
}
.stat-label {
  color: var(--text-faint);
}
.stat-value {
  min-width: 60px;
  text-align: right;
}
</style>

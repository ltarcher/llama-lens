<template>
  <div class="detail">
    <TopBar
      :host-name="hostName"
      :model-name="modelName"
      :model-title="modelTitle"
      :llama-online="llamaOnline"
      :ssh-ok="sshOk"
      :stats="topStats"
      :mode="mode"
      :degraded="degraded"
      :connected="connected"
      @update:mode="setMode"
    />

    <div v-if="!llamaOnline && !sshOk" class="banner-danger">主机不可达（llama 离线 + SSH 断开）</div>

    <main class="content">
      <!-- 首次加载骨架 -->
      <template v-if="!snap">
        <div class="skeleton" style="height: 120px; margin-bottom: 16px"></div>
        <div class="skeleton" style="height: 200px; margin-bottom: 16px"></div>
        <div class="skeleton" style="height: 300px"></div>
      </template>

      <template v-else>
        <!-- ============ AI 核心指标区 ============ -->
        <section>
          <div class="section-title">AI 核心指标</div>
          <div class="kpi-row">
            <KpiCard
              title="Token 生成速度"
              :value="llamaOnline ? snap.llama.gen_speed_tps : null"
              unit="tok/s"
              :level="genLevel"
              :spark="sparkGen"
              :source="snap.llama.speed_source"
              :sub="offlineNote"
            />
            <KpiCard
              title="Prompt 处理速度"
              :value="llamaOnline ? snap.llama.prompt_speed_tps : null"
              unit="tok/s"
              :spark="sparkPrompt"
              :sub="offlineNote"
            />
            <KpiCard
              title="上下文占用"
              :value="ctxPct"
              unit="%"
              :digits="1"
              :level="ctxLevel"
              :sub="ctxSub"
            />
            <KpiCard
              title="MTP 接受率"
              :value="mtpPct"
              unit="%"
              :digits="1"
              :level="mtpLevel"
              :sub="mtpSub"
            />
          </div>

          <div class="state-row">
            <LlamaStateCard :log="snap.llama.log" :online="llamaOnline" />
            <ContextCard :context="ctx" />
            <MtpCard :mtp="mtp" :flags="flags" />
          </div>
        </section>

        <!-- ============ GPU 区 ============ -->
        <section>
          <div class="section-title">GPU（按卡聚合）</div>
          <div v-if="sshOk" class="gpu-grid" :class="{ single: gpus.length <= 1 }">
            <GpuPanel v-for="g in gpus" :key="g.index" :gpu="g" :alerts="alerts" />
          </div>
          <div v-else class="glass placeholder"><span class="icon">▣</span>数据不可用（SSH 断开）</div>
        </section>

        <!-- ============ 系统区 ============ -->
        <section>
          <div class="section-title">系统资源</div>
          <template v-if="sshOk">
            <div class="sys-grid">
              <CpuPanel :cpu="cpu" :alerts="alerts" />
              <MemPanel :mem="mem" :alerts="alerts" />
            </div>
            <div class="sys-grid">
              <DiskPanel :disk="disk" :alerts="alerts" />
              <NetPanel :net="net" />
            </div>
          </template>
          <div v-else class="glass placeholder"><span class="icon">▣</span>数据不可用（SSH 断开）</div>
        </section>

        <!-- ============ 模型与 Slot 区 ============ -->
        <section>
          <div class="section-title">模型与 Slot</div>
          <div class="model-grid">
            <ModelInfoCard :model="model" />
            <SlotTable :slots="slots" />
          </div>
        </section>

        <!-- ============ 进程区 ============ -->
        <section>
          <div class="section-title">进程</div>
          <template v-if="sshOk">
            <div class="proc-grid">
              <LlamaProcessCard :process="process" :service="service" />
              <div class="proc-side">
                <TopProcessTable :rows="topCpu" mode="cpu" />
                <TopProcessTable :rows="topMem" mode="mem" />
              </div>
            </div>
          </template>
          <div v-else class="glass placeholder"><span class="icon">▣</span>数据不可用（SSH 断开）</div>
        </section>

        <!-- ============ 趋势区 ============ -->
        <section>
          <div class="section-title trend-title-row">
            历史趋势
            <span class="win-switch mono">
              <button v-for="w in windows" :key="w.s" :class="{ on: winS === w.s }" @click="winS = w.s">{{ w.label }}</button>
            </span>
          </div>
          <div class="trend-grid">
            <TrendChart title="Token 速度" unit="tok/s" :series="chartSpeed" :height="170" />
            <TrendChart title="GPU 利用率" unit="%" :series="chartGpuUtil" :height="170" :y-max="100" />
            <TrendChart title="GPU 显存" unit="MB" :series="chartGpuMem" :height="170" />
            <TrendChart title="GPU 温度" unit="°C" :series="chartGpuTemp" :height="170" />
            <TrendChart title="GPU 功耗" unit="W" :series="chartGpuPower" :height="170" />
            <TrendChart title="CPU" unit="%" :series="chartCpu" :height="170" :y-max="100" />
            <TrendChart title="内存" unit="MB" :series="chartMem" :height="170" />
            <TrendChart title="网络" unit="MB/s" :series="chartNet" :height="170" />
            <TrendChart title="上下文占用" unit="tokens" :series="chartCtx" :height="170" />
            <TrendChart title="MTP 接受率" unit="%" :series="chartMtp" :height="170" :y-max="100" :y-min="0" />
          </div>
        </section>

        <!-- ============ 事件流 ============ -->
        <section>
          <EventFeed :events="events" />
        </section>
      </template>
    </main>

    <div v-if="mode === 'paused'" class="paused-watermark"><span>已暂停</span></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useHostStream } from '../stream'
import { fmtNum, fmtClock, alertLevel } from '../utils'
import TopBar from '../components/TopBar.vue'
import KpiCard from '../components/KpiCard.vue'
import LlamaStateCard from '../components/LlamaStateCard.vue'
import ContextCard from '../components/ContextCard.vue'
import MtpCard from '../components/MtpCard.vue'
import GpuPanel from '../components/GpuPanel.vue'
import CpuPanel from '../components/CpuPanel.vue'
import MemPanel from '../components/MemPanel.vue'
import DiskPanel from '../components/DiskPanel.vue'
import NetPanel from '../components/NetPanel.vue'
import LlamaProcessCard from '../components/LlamaProcessCard.vue'
import TopProcessTable from '../components/TopProcessTable.vue'
import ModelInfoCard from '../components/ModelInfoCard.vue'
import SlotTable from '../components/SlotTable.vue'
import TrendChart from '../components/TrendChart.vue'
import EventFeed from '../components/EventFeed.vue'

const props = defineProps({ id: { type: String, required: true } })

const { snapshot, connected, degraded, mode, setMode } = useHostStream(props.id)
const snap = computed(() => snapshot.value)

// ---------------- 基础字段 ----------------
const hostName = computed(() => (snap.value ? snap.value.host.name : props.id))
const llama = computed(() => (snap.value ? snap.value.llama : {}))
const hm = computed(() => (snap.value ? snap.value.host_metrics : {}))
const alerts = computed(() => (snap.value ? snap.value.alerts : []))
const events = computed(() => (snap.value ? snap.value.events : []))

const llamaOnline = computed(() => !!(snap.value && snap.value.llama.online))
const sshOk = computed(() => !!(snap.value && snap.value.host_metrics.reachable))
const model = computed(() => llama.value.model || {})
const modelName = computed(() => (model.value.name || model.value.path || '').split('/').pop())
const modelTitle = computed(() => model.value.name || model.value.path || '')
const offlineNote = computed(() =>
  snap.value && !llamaOnline.value ? `数据截至 ${fmtClock(snap.value.ts)}` : ''
)

// ---------------- AI 核心 ----------------
const ctx = computed(() => (llama.value.log && llama.value.log.context) || {})
const mtp = computed(() => (llama.value.log && llama.value.log.mtp) || {})
const flags = computed(() => (hm.value.process && hm.value.process.flags) || {})

const ctxPct = computed(() => (ctx.value.pct === null || ctx.value.pct === undefined ? null : ctx.value.pct))
const ctxLevel = computed(() => alertLevel(alerts.value, 'ctx'))
const ctxSub = computed(() => {
  if (ctx.value.used === null || ctx.value.used === undefined) return '等待任务结束'
  return `${fmtNum(ctx.value.used)} / ${fmtNum(ctx.value.total || 0)} tokens`
})
// 原始值依赖：避免 chartCtx 随每秒 WS 快照（ctx 新对象）重算
const ctxTotal = computed(() => {
  const t = ctx.value.total
  return t === null || t === undefined ? null : t
})

const mtpPct = computed(() => {
  const a = mtp.value.acceptance
  return a === null || a === undefined ? null : a * 100
})
const mtpLevel = computed(() => alertLevel(alerts.value, 'mtp'))
const mtpSub = computed(() => {
  if (mtpPct.value === null) return '等待任务结束'
  return `mean len ${mtp.value.mean_len === null || mtp.value.mean_len === undefined ? '—' : mtp.value.mean_len.toFixed(2)}`
})

const genLevel = computed(() => {
  // 生成速度本身无阈值告警；llama 离线时置灰
  return 'normal'
})

// ---------------- 系统数据 ----------------
const gpus = computed(() => hm.value.gpus || [])
const cpu = computed(() => hm.value.cpu || {})
const mem = computed(() => hm.value.mem || {})
const disk = computed(() => hm.value.disk || {})
const net = computed(() => hm.value.net || {})
const process = computed(() => hm.value.process || {})
const service = computed(() => hm.value.service || {})
const topCpu = computed(() => (hm.value.top && hm.value.top.cpu) || [])
const topMem = computed(() => (hm.value.top && hm.value.top.mem) || [])
const slots = computed(() => llama.value.slots || [])

const topStats = computed(() => {
  const s = snap.value
  if (!s) return null
  const ll = s.llama || {}
  const hm = s.host_metrics || {}
  const log = ll.log || {}
  const ctx = log.context || {}
  const mtp = log.mtp || {}
  const mem = hm.mem || {}
  const cpu = hm.cpu || {}
  return {
    online: !!ll.online,
    gen: ll.gen_speed_tps,
    prompt: ll.prompt_speed_tps,
    speedSource: ll.speed_source || '',
    mtp: mtp.acceptance === null || mtp.acceptance === undefined ? null : mtp.acceptance * 100,
    ctxUsed: ctx.used,
    ctxRemain: ctx.remaining,
    ctxTotal: ctx.total,
    ctxPct: ctx.pct,
    gpus: (hm.gpus || []).map((g) => ({
      idx: g.index,
      util: g.util_pct,
      temp: g.temp_c,
      power: g.power_w,
      memUsed: g.mem_used_mb,
      memTotal: g.mem_total_mb
    })),
    memUsed: mem.used_mb,
    memTotal: mem.total_mb,
    cpu: cpu.usage_pct,
    alerts: s.alerts || []
  }
})

// ---------------- 趋势图 ----------------
const windows = [
  { s: 300, label: '5m' },
  { s: 900, label: '15m' },
  { s: 3600, label: '1h' }
]
const winS = ref(300)
const history = ref(null)
let histTimer = null

async function loadHistory() {
  try {
    history.value = await api.history(props.id, winS.value)
  } catch (e) { /* ignore */ }
}

function seriesOf(name, opts = {}) {
  const s = history.value && history.value.series ? history.value.series[name] : null
  if (!s) return null
  return { name: opts.name || name, ts: s.ts, values: s.values, color: opts.color, step: opts.step, area: opts.area, stack: opts.stack, markLine: opts.markLine }
}

const chartSpeed = computed(() => {
  const out = []
  const g = seriesOf('gen_speed', { name: 'gen', color: '#00e5ff', area: true })
  const p = seriesOf('prompt_speed', { name: 'prompt', color: '#00ff9d', area: true })
  if (g) out.push(g)
  if (p) out.push(p)
  return out
})
const chartGpuUtil = computed(() => {
  const colors = ['#00e5ff', '#00ff9d', '#ffc53d', '#ff3b5c']
  const out = []
  for (let i = 0; i < 8; i++) {
    const s = seriesOf(`gpu_util_${i}`, { name: `GPU${i}`, color: colors[i % colors.length] })
    if (s) out.push(s)
  }
  return out
})
const chartGpuMem = computed(() => {
  const colors = ['#00e5ff', '#00ff9d', '#ffc53d', '#ff3b5c']
  const out = []
  for (let i = 0; i < 8; i++) {
    const s = seriesOf(`gpu_mem_${i}`, { name: `GPU${i}`, color: colors[i % colors.length] })
    if (s) out.push(s)
  }
  return out
})
const chartGpuTemp = computed(() => {
  const colors = ['#00e5ff', '#00ff9d', '#ffc53d', '#ff3b5c']
  const out = []
  for (let i = 0; i < 8; i++) {
    const s = seriesOf(`gpu_temp_${i}`, { name: `GPU${i}`, color: colors[i % colors.length] })
    if (s) out.push(s)
  }
  return out
})
const chartGpuPower = computed(() => {
  const colors = ['#00e5ff', '#00ff9d', '#ffc53d', '#ff3b5c']
  const out = []
  for (let i = 0; i < 8; i++) {
    const s = seriesOf(`gpu_power_${i}`, { name: `GPU${i}`, color: colors[i % colors.length] })
    if (s) out.push(s)
  }
  return out
})
const chartCpu = computed(() => {
  const s = seriesOf('cpu', { name: 'CPU', color: '#00e5ff', area: true })
  return s ? [s] : []
})
const chartMem = computed(() => {
  const out = []
  const u = seriesOf('mem_used', { name: '已用', color: '#00e5ff', area: true, stack: 'mem' })
  const c = seriesOf('mem_buff_cache', { name: 'buff/cache', color: '#00ff9d', area: true, stack: 'mem' })
  if (u) out.push(u)
  if (c) out.push(c)
  return out
})
const chartNet = computed(() => {
  const out = []
  const r = seriesOf('net_rx', { name: '下行', color: '#00e5ff' })
  const t = seriesOf('net_tx', { name: '上行', color: '#00ff9d' })
  if (r) out.push(r)
  if (t) out.push(t)
  return out
})
const chartCtx = computed(() => {
  const s = seriesOf('ctx_used', { name: 'n_tokens', color: '#00e5ff', step: true })
  if (!s) return []
  const total = ctxTotal.value
  if (total) {
    s.markLine = {
      silent: true,
      symbol: 'none',
      lineStyle: { color: '#ff3b5c', type: 'dashed', width: 1 },
      label: { color: '#ff3b5c', fontSize: 10, formatter: `n_ctx ${fmtNum(total)}` },
      data: [{ yAxis: total }]
    }
  }
  return [s]
})
const chartMtp = computed(() => {
  const s = seriesOf('mtp_acceptance', { name: '接受率', color: '#00ff9d', step: true })
  if (!s) return []
  s.values = s.values.map((v) => (v === null ? null : v * 100))
  return [s]
})

// KPI sparkline（60s，取自历史序列尾部）
function tail60(name) {
  const s = history.value && history.value.series ? history.value.series[name] : null
  if (!s || !s.ts.length) return []
  const now = s.ts[s.ts.length - 1]
  const pts = []
  for (let i = 0; i < s.ts.length; i++) {
    if (now - s.ts[i] <= 60) pts.push([s.ts[i], s.values[i]])
  }
  return pts
}
const sparkGen = computed(() => tail60('gen_speed'))
const sparkPrompt = computed(() => tail60('prompt_speed'))

onMounted(() => {
  loadHistory()
  histTimer = setInterval(loadHistory, 5000)
})
watch(winS, loadHistory)
onBeforeUnmount(() => {
  if (histTimer) clearInterval(histTimer)
})
</script>

<style scoped>
.content {
  max-width: 1720px;
  margin: 0 auto;
  padding: 18px 24px 40px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.banner-danger {
  margin: 14px 24px 0;
  padding: 10px 16px;
  border-radius: 8px;
  background: rgba(255, 59, 92, 0.12);
  border: 1px solid rgba(255, 59, 92, 0.5);
  color: var(--red);
  font-weight: 600;
  text-align: center;
  animation: dangerPulse 1.2s infinite;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.state-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.gpu-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.gpu-grid.single { grid-template-columns: 1fr; }
.sys-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.sys-grid:last-child { margin-bottom: 0; }
.model-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.proc-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}
.proc-side { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.proc-side > .top { flex: 1; }
.trend-title-row { justify-content: flex-start; gap: 16px; }
.win-switch { display: inline-flex; gap: 4px; margin-left: auto; }
.win-switch button {
  background: transparent;
  border: 1px solid var(--card-border);
  color: var(--text-dim);
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 12px;
  cursor: pointer;
}
.win-switch button.on {
  color: var(--cyan);
  border-color: rgba(0, 229, 255, 0.5);
  background: rgba(0, 229, 255, 0.08);
}
.trend-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
@media (max-width: 1500px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .state-row { grid-template-columns: 1fr; }
  .gpu-grid { grid-template-columns: 1fr; }
  .model-grid { grid-template-columns: 1fr; }
  .proc-grid { grid-template-columns: 1fr; }
}
</style>

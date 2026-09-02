<template>
  <div class="host-card-wrapper">
    <router-link :to="`/host/${host.id}`" class="host-card glass glass-hover" :class="cardClass">
      <div class="top">
        <span class="dot" :class="dotClass"></span>
        <span class="hostname">{{ host.name }}</span>
        <span class="hid mono faint">{{ host.id }}</span>
        <div class="actions">
          <button class="action-btn" @click.stop="$emit('edit', host)" title="编辑">✎</button>
          <button class="action-btn danger" @click.stop="$emit('delete', host)" title="删除">✕</button>
        </div>
        <span v-if="host.alerts_count > 0" class="alert-badge mono">{{ host.alerts_count }}</span>
      </div>

      <div class="model">
        <span class="model-name" :class="{ muted: !host.online }">{{ host.model_name || '未加载模型' }}</span>
        <span v-if="host.n_params" class="model-params mono dim">{{ fmtParams(host.n_params) }} 参数</span>
      </div>

      <div class="speed" :class="{ muted: !host.online }">
        <div class="speed-num">
          <span class="mono big" :class="speedLevel">{{ speedText }}</span>
          <span class="unit">tok/s</span>
        </div>
        <svg v-if="sparkD" class="spark" :viewBox="`0 0 ${sparkW} ${sparkH}`" preserveAspectRatio="none">
          <path :d="sparkD" fill="none" :stroke="sparkColor" stroke-width="1.5" vector-effect="non-scaling-stroke" />
        </svg>
      </div>

      <div class="gpus">
        <div v-for="g in host.gpus" :key="g.index" class="gpu-row">
          <span class="gpu-label mono">GPU{{ g.index }}</span>
          <div class="bar"><i :class="barClass(g.util_pct)" :style="{ width: (g.util_pct || 0) + '%' }"></i></div>
          <span class="gpu-val mono" :class="valClass(g.util_pct)">{{ g.util_pct === null ? '—' : Math.round(g.util_pct) + '%' }}</span>
          <span class="gpu-mem mono faint">{{ g.mem_pct === null ? '' : '显存 ' + Math.round(g.mem_pct) + '%' }}</span>
        </div>
        <div v-if="!host.gpus.length" class="faint small">无 GPU 数据</div>
      </div>

      <div class="bottom mono">
        <span>CPU <b :class="valClass(host.cpu_pct)">{{ host.cpu_pct === null ? '—' : Math.round(host.cpu_pct) + '%' }}</b></span>
        <span>MEM <b :class="valClass(host.mem_pct)">{{ host.mem_pct === null ? '—' : Math.round(host.mem_pct) + '%' }}</b></span>
        <span v-if="!host.ssh_ok" class="lv-warn">SSH 断开</span>
        <span v-if="!host.online" class="lv-danger">llama 离线</span>
        <span v-if="host.llama_ok" class="llama-badge ok">llama-server 在线</span>
        <span v-else-if="host.llama_ok === false" class="llama-badge warn">llama-server 离线</span>
        <span v-if="host.vllm_online" class="vllm-badge ok">vLLM 在线</span>
        <span v-else-if="host.vllm_online === false" class="vllm-badge warn">vLLM 离线</span>
      </div>
    </router-link>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { fmtParams, sparkPath, useCountUp, alertLevel } from '../utils'

defineEmits(['edit', 'delete'])

const props = defineProps({
  host: { type: Object, required: true }
})

const speed = useCountUp(computed(() => (props.host.online ? props.host.gen_speed_tps || 0 : 0)))
const speedText = computed(() => (speed.value === null || speed.value === undefined ? '—' : Number(speed.value).toFixed(1)))

const sparkW = 130
const sparkH = 30
const sparkD = computed(() => sparkPath(props.host.speed_spark || [], sparkW, sparkH))
const sparkColor = computed(() => (props.host.online ? 'var(--cyan)' : 'var(--text-faint)'))

const cardLevel = computed(() => alertLevel(props.host.alerts, ''))
const cardClass = computed(() => (cardLevel.value === 'danger' ? 'card-danger' : cardLevel.value === 'warn' ? 'card-warn' : ''))
const dotClass = computed(() => {
  if (props.host.online) return 'online'
  if (props.host.ssh_ok) return 'warn'
  return 'offline'
})
const speedLevel = computed(() => (props.host.online ? '' : 'muted'))

function barClass(v) {
  if (v === null) return ''
  if (v >= 90) return 'danger'
  if (v >= 80) return 'warn'
  return ''
}
function valClass(v) {
  if (v === null) return ''
  if (v >= 90) return 'lv-danger'
  if (v >= 80) return 'lv-warn'
  return ''
}
</script>

<style scoped>
.host-card-wrapper {
  position: relative;
}
.host-card {
  display: block;
  padding: 16px 18px;
  color: var(--text);
  text-decoration: none;
  position: relative;
}
.host-card:hover { text-decoration: none; }
.top { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.hostname { font-size: 15px; font-weight: 600; }
.hid { font-size: 11px; }
.actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}
.action-btn {
  background: none;
  border: 1px solid transparent;
  color: var(--text-faint);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.15s, border-color 0.15s;
}
.host-card:hover .action-btn {
  opacity: 1;
}
.action-btn:hover {
  border-color: var(--cyan);
  color: var(--cyan);
}
.action-btn.danger:hover {
  border-color: var(--red);
  color: var(--red);
}
.alert-badge {
  margin-left: auto;
  background: var(--red);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  box-shadow: 0 0 10px rgba(255, 59, 92, 0.6);
}
.model { display: flex; align-items: baseline; gap: 8px; margin-bottom: 12px; min-height: 18px; }
.model-name { font-size: 13px; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.model-params { font-size: 11px; flex: none; }
.speed {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}
.speed-num { display: flex; align-items: baseline; gap: 6px; }
.big { font-size: 32px; font-weight: 700; color: var(--cyan); text-shadow: 0 0 14px rgba(0, 229, 255, 0.45); line-height: 1; }
.unit { color: var(--text-dim); font-size: 11px; }
.muted { opacity: 0.45; }
.spark { width: 130px; height: 30px; flex: none; }
.gpus { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.gpu-row { display: flex; align-items: center; gap: 8px; }
.gpu-label { width: 38px; font-size: 11px; color: var(--text-dim); flex: none; }
.gpu-row .bar { flex: 1; }
.gpu-val { width: 38px; text-align: right; font-size: 12px; flex: none; }
.gpu-mem { width: 64px; text-align: right; font-size: 10px; flex: none; }
.bottom { display: flex; gap: 16px; font-size: 12px; color: var(--text-dim); }
.bottom b { color: var(--text); font-weight: 600; }
.vllm-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 10px;
  border: 1px solid;
}
.vllm-badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 5px currentColor;
}
.vllm-badge.ok { color: var(--green); border-color: rgba(0, 255, 157, 0.4); background: rgba(0, 255, 157, 0.08); }
.vllm-badge.warn { color: var(--amber); border-color: rgba(255, 197, 61, 0.4); background: rgba(255, 197, 61, 0.08); }
.llama-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 10px;
  border: 1px solid;
}
.llama-badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 5px currentColor;
}
.llama-badge.ok { color: var(--green); border-color: rgba(0, 229, 255, 0.4); background: rgba(0, 229, 255, 0.08); }
.llama-badge.warn { color: var(--amber); border-color: rgba(255, 197, 61, 0.4); background: rgba(255, 197, 61, 0.08); }
</style>

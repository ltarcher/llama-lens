<template>
  <header class="topbar">
    <router-link to="/" class="back">← 门户</router-link>
    <div class="host-info">
      <span class="dot" :class="dotClass"></span>
      <span class="hostname">{{ hostName }}</span>
      <span v-if="modelName" class="model mono dim">· {{ modelName }} ({{ paramsText }})</span>
    </div>

    <div class="right">
      <span v-if="!llamaOnline" class="badge danger">llama 离线</span>
      <span v-else-if="!sshOk" class="badge warn">SSH 断开</span>
      <span v-else class="badge ok">在线</span>
      <span v-if="uptimeText" class="mono dim small">运行 {{ uptimeText }}</span>

      <span class="mode-indicator" :class="modeDotClass" title="数据通道"></span>
      <select :value="mode" class="mode-select mono" @change="onModeChange">
        <option value="ws">实时 (WS)</option>
        <option value="1s">1s</option>
        <option value="2s">2s</option>
        <option value="5s">5s</option>
        <option value="paused">暂停</option>
      </select>
      <span v-if="degraded" class="badge warn small">WS 断线 · 轮询中</span>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { fmtParams, fmtDuration } from '../utils'

const props = defineProps({
  hostName: { type: String, default: '' },
  modelName: { type: String, default: '' },
  nParams: { type: [Number, String], default: null },
  llamaOnline: { type: Boolean, default: false },
  sshOk: { type: Boolean, default: false },
  uptimeS: { type: Number, default: null },
  mode: { type: String, default: 'ws' },
  degraded: { type: Boolean, default: false },
  connected: { type: Boolean, default: false }
})
const emit = defineEmits(['update:mode'])

const paramsText = computed(() => (props.nParams ? fmtParams(props.nParams) : ''))
const uptimeText = computed(() => (props.uptimeS ? fmtDuration(props.uptimeS) : ''))
const dotClass = computed(() => {
  if (props.llamaOnline && props.sshOk) return 'online'
  if (props.sshOk) return 'warn'
  return 'offline'
})
const modeDotClass = computed(() => {
  if (props.mode === 'paused') return 'gray'
  if (props.mode === 'ws') return props.connected ? 'green' : 'amber'
  return 'amber'
})

function onModeChange(e) {
  emit('update:mode', e.target.value)
}
</script>

<style scoped>
.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(0, 229, 255, 0.12);
  background: rgba(10, 14, 23, 0.6);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 20;
}
.back { color: var(--text-dim); font-size: 13px; flex: none; }
.back:hover { color: var(--cyan); text-decoration: none; }
.host-info { display: flex; align-items: center; gap: 10px; min-width: 0; }
.hostname { font-size: 15px; font-weight: 600; }
.model { color: var(--text-dim); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.mode-indicator { width: 8px; height: 8px; border-radius: 50%; }
.mode-indicator.green { background: var(--green); box-shadow: 0 0 6px var(--green); }
.mode-indicator.amber { background: var(--amber); box-shadow: 0 0 6px var(--amber); }
.mode-indicator.gray { background: var(--text-faint); }
.mode-select {
  background: rgba(16, 24, 40, 0.9);
  color: var(--text);
  border: 1px solid var(--card-border);
  border-radius: 6px;
  font-size: 12px;
  padding: 4px 8px;
  outline: none;
  cursor: pointer;
}
.mode-select:hover { border-color: var(--card-border-hover); }
</style>

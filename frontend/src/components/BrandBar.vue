<template>
  <header class="brandbar">
    <div class="brand">
      <span class="logo">◉</span>
      <span class="name">LlamaLens</span>
      <span class="sub">llama-server 实时监控</span>
    </div>
    <div class="stats mono">
      <span>主机 <b>{{ hostsTotal }}</b></span>
      <span class="sep">·</span>
      <span>在线 <b class="lv-green">{{ onlineCount }}</b></span>
      <span v-if="totalSpeed > 0" class="sep">·</span>
      <span v-if="totalSpeed > 0">Token 速度 <b class="lv-cyan">{{ totalSpeed.toFixed(1) }} tok/s</b></span>
      <span class="conn" :class="connected ? 'ok' : 'bad'">{{ connected ? 'WS 实时' : '轮询中' }}</span>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  hosts: { type: Array, default: () => [] },
  connected: { type: Boolean, default: false }
})

const hostsTotal = computed(() => props.hosts.length)
const onlineCount = computed(() => props.hosts.filter((h) => h.online).length)
const totalSpeed = computed(() => props.hosts.reduce((s, h) => s + (h.gen_speed_tps || 0), 0))
</script>

<style scoped>
.brandbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid rgba(0, 229, 255, 0.12);
  background: rgba(10, 14, 23, 0.6);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 20;
}
.brand { display: flex; align-items: baseline; gap: 10px; }
.logo {
  color: var(--cyan);
  font-size: 20px;
  text-shadow: 0 0 12px rgba(0, 229, 255, 0.8);
  align-self: center;
}
.name {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #00e5ff, #00ff9d);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.sub { color: var(--text-faint); font-size: 11px; }
.stats { display: flex; align-items: center; gap: 10px; color: var(--text-dim); font-size: 12px; }
.stats b { color: var(--text); font-weight: 600; }
.sep { color: var(--text-faint); }
.lv-green { color: var(--green) !important; }
.lv-cyan { color: var(--cyan) !important; }
.conn { padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.conn.ok { color: var(--green); border: 1px solid rgba(0, 255, 157, 0.35); }
.conn.bad { color: var(--amber); border: 1px solid rgba(255, 197, 61, 0.35); }
</style>

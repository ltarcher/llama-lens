<template>
  <div class="state-card glass" :class="cardClass">
    <div class="head">
      <span class="phase" :class="phaseClass">{{ phaseText }}</span>
      <span v-if="logAvailable" class="badge ok small">日志实时</span>
      <span v-else class="badge dim small">日志不可用 · API 数据</span>
    </div>

    <template v-if="logAvailable">
      <div class="kv" v-if="state.task_id !== null && state.task_id !== undefined">
        <span class="k">任务 ID</span><span class="v mono">#{{ state.task_id }}</span>
      </div>
      <div class="kv" v-if="state.is_child !== null && state.is_child !== undefined">
        <span class="k">子任务</span><span class="v mono">{{ state.is_child ? '是' : '否' }}</span>
      </div>

      <template v-if="phase === 'prompt_processing'">
        <div class="progress-wrap">
          <div class="bar"><i class="green" :style="{ width: (state.prompt_progress || 0) * 100 + '%' }"></i></div>
          <span class="mono small dim">{{ ((state.prompt_progress || 0) * 100).toFixed(0) }}%</span>
        </div>
        <div class="kv">
          <span class="k">Prompt 速度</span>
          <span class="v mono" style="color: var(--green)">{{ state.prompt_speed_tps === null ? '—' : state.prompt_speed_tps.toFixed(1) + ' t/s' }}</span>
        </div>
      </template>

      <template v-else-if="phase === 'decoding'">
        <div class="kv">
          <span class="k">已解码</span><span class="v mono">{{ fmtNum(state.n_decoded) }} tokens</span>
        </div>
        <div class="kv">
          <span class="k">实时速度 (3s)</span>
          <span class="v mono" style="color: var(--cyan)">{{ state.tg_3s_tps === null ? '—' : state.tg_3s_tps.toFixed(2) + ' t/s' }}</span>
        </div>
        <div class="kv">
          <span class="k">任务均速</span>
          <span class="v mono dim">{{ state.tg_tps === null ? '—' : state.tg_tps.toFixed(2) + ' t/s' }}</span>
        </div>
      </template>

      <template v-else>
        <div class="idle-note">空闲 · 等待新任务</div>
        <div v-if="lastTask" class="last-task small dim">
          上一任务 #{{ lastTask.task_id }}：{{ lastTask.total_tokens || lastTask.decoded_tokens || '—' }} tokens
          <template v-if="lastTask.gen_speed_tps"> · 均速 {{ lastTask.gen_speed_tps.toFixed(1) }} t/s</template>
          <template v-if="lastTask.mtp && lastTask.mtp.acceptance !== null"> · MTP {{ (lastTask.mtp.acceptance * 100).toFixed(1) }}%</template>
        </div>
      </template>
    </template>

    <div v-else class="placeholder"><span class="icon">⌁</span>日志不可用，使用 API 数据</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { fmtNum } from '../utils'

const props = defineProps({
  log: { type: Object, default: () => ({}) },
  online: { type: Boolean, default: false }
})

const logAvailable = computed(() => !!(props.log && props.log.available))
const state = computed(() => (props.log && props.log.state) || {})
const lastTask = computed(() => (props.log && props.log.last_task) || null)

const phase = computed(() => state.value.phase || 'idle')
const phaseText = computed(() => {
  if (!props.online) return 'llama 离线'
  if (!logAvailable.value) return '未知（API）'
  if (phase.value === 'prompt_processing') return 'Prompt 处理中'
  if (phase.value === 'decoding') return '生成中'
  return '空闲'
})
const phaseClass = computed(() => {
  if (!props.online) return 'lv-danger'
  if (phase.value === 'decoding') return 'lv-cyan'
  if (phase.value === 'prompt_processing') return 'lv-green'
  return ''
})
const cardClass = computed(() => (phase.value === 'decoding' && props.online ? 'active' : ''))
</script>

<style scoped>
.state-card { padding: 12px 16px; display: flex; flex-direction: column; gap: 4px; }
.state-card.active { border-color: rgba(0, 229, 255, 0.35); box-shadow: 0 0 12px rgba(0, 229, 255, 0.15); }
.head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.phase { font-size: 16px; font-weight: 700; }
.lv-cyan { color: var(--cyan); text-shadow: 0 0 10px rgba(0, 229, 255, 0.5); }
.lv-green { color: var(--green); text-shadow: 0 0 10px rgba(0, 255, 157, 0.5); }
.progress-wrap { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.progress-wrap .bar { flex: 1; }
.idle-note { color: var(--text-faint); font-size: 12px; padding: 6px 0; }
.last-task { line-height: 1.6; }
</style>

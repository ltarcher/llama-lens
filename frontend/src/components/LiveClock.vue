<template>
  <span class="live-clock mono dim">{{ text }}</span>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const text = ref('')
let timer = null

function tick() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  text.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.live-clock { font-size: 12px; white-space: nowrap; }
</style>

<template>
  <div class="portal">
    <BrandBar :hosts="hosts" :connected="connected" />
    <main class="grid">
      <template v-if="hosts.length">
        <HostCard v-for="h in hosts" :key="h.id" :host="h" />
      </template>
      <div v-else class="glass placeholder" style="grid-column: 1 / -1; min-height: 300px">
        <span class="icon">◉</span>
        <span>未注册主机</span>
        <span class="small">在 config/hosts.yaml 中添加主机后重启面板</span>
      </div>
    </main>
  </div>
</template>

<script setup>
import BrandBar from '../components/BrandBar.vue'
import HostCard from '../components/HostCard.vue'
import { usePortalStream } from '../stream'

const { hosts, connected } = usePortalStream()
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
  padding: 20px 24px;
  max-width: 1720px;
  margin: 0 auto;
}
</style>

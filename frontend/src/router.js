import { createRouter, createWebHistory } from 'vue-router'
import PortalView from './views/PortalView.vue'
import HostDetailView from './views/HostDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'portal', component: PortalView },
    { path: '/host/:id', name: 'host', component: HostDetailView, props: true }
  ]
})

export default router

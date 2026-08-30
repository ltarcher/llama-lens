import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './theme/global.css'
import './theme/terminal.css'
import './theme/light.css'
import './theme/monokai.css'
import './theme/nord.css'
import './theme/dracula.css'
import './theme/synthwave.css'
import './theme/tokyonight.css'
import './theme/matrix.css'
import { initTheme } from './theme'

initTheme()
createApp(App).use(router).mount('#app')

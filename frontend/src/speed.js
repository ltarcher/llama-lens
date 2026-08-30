import { ref } from 'vue'

// 全局 token 速度（门户级聚合：各主机 gen_speed_tps 求和）。
// 由 BrandBar（门户）写入；浏览器标签页标题（App.vue）与
// Terminal 主题窗口标题栏（TerminalFrame.vue）共同读取，
// 使速度在任意视图/任意“标题”位置都可见。
export const totalSpeed = ref(0)

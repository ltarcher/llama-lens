<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3>{{ isEdit ? '编辑主机' : '添加主机' }}</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <form @submit.prevent="handleSubmit" class="modal-body">
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="form-title">基本信息</div>
          <div class="form-row">
            <label>主机 ID <span class="req">*</span></label>
            <input v-model="form.id" :disabled="isEdit" required placeholder="例如: ai-prod" />
          </div>
          <div class="form-row">
            <label>主机名称 <span class="req">*</span></label>
            <input v-model="form.name" required placeholder="例如: AI 生产服务器" />
          </div>
        </div>

        <!-- llama-server 配置 -->
        <div class="form-section">
          <div class="form-title">
            llama-server 引擎
            <label class="toggle-label">
              <input type="checkbox" v-model="enableLlama" />
              <span class="toggle"></span>
            </label>
          </div>
          <template v-if="enableLlama">
            <div class="form-row">
              <label>llama-server 地址 <span class="req">*</span></label>
              <input v-model="llamaForm.host" required placeholder="IP 或域名" />
            </div>
            <div class="form-row">
              <label>端口 <span class="req">*</span></label>
              <input v-model.number="llamaForm.port" type="number" required placeholder="8080" />
            </div>
            <div class="form-row">
              <label>轮询间隔（秒）</label>
              <input v-model.number="llamaForm.interval" type="number" step="0.1" min="0.1" />
            </div>
            <div class="form-row">
              <label>超时（秒）</label>
              <input v-model.number="llamaForm.timeout" type="number" step="0.1" min="0.5" />
            </div>
          </template>
        </div>

        <!-- vLLM 配置 -->
        <div class="form-section">
          <div class="form-title">
            vLLM 引擎
            <label class="toggle-label">
              <input type="checkbox" v-model="enableVllm" />
              <span class="toggle"></span>
            </label>
          </div>
          <template v-if="enableVllm">
            <div class="form-row">
              <label>vLLM 地址 <span class="req">*</span></label>
              <input v-model="vllmForm.host" required placeholder="IP 或域名" />
            </div>
            <div class="form-row">
              <label>端口 <span class="req">*</span></label>
              <input v-model.number="vllmForm.port" type="number" required placeholder="8100" />
            </div>
            <div class="form-row">
              <label>轮询间隔（秒）</label>
              <input v-model.number="vllmForm.interval" type="number" step="0.1" min="0.5" />
            </div>
            <div class="form-row">
              <label>超时（秒）</label>
              <input v-model.number="vllmForm.timeout" type="number" step="0.1" min="0.5" />
            </div>
          </template>
        </div>

        <!-- SSH 配置 -->
        <div class="form-section">
          <div class="form-title">SSH 配置</div>
          <div class="form-row">
            <label>SSH 地址 <span class="req">*</span></label>
            <input v-model="sshForm.host" required placeholder="IP 或域名" />
          </div>
          <div class="form-row">
            <label>端口</label>
            <input v-model.number="sshForm.port" type="number" placeholder="22" />
          </div>
          <div class="form-row">
            <label>用户名</label>
            <input v-model="sshForm.user" placeholder="root" />
          </div>
          <div class="form-row">
            <label>密码</label>
            <input v-model="sshForm.password" type="password" placeholder="SSH 密码" />
          </div>
          <div class="form-row">
            <label>密钥路径</label>
            <input v-model="sshForm.key_path" placeholder="~/.ssh/id_ed25519" />
          </div>
        </div>

        <!-- 日志配置 -->
        <div class="form-section">
          <div class="form-title">日志配置</div>
          <div class="form-row">
            <label>日志来源</label>
            <select v-model="logForm.source">
              <option value="journal">journal（systemd）</option>
              <option value="file">file（日志文件）</option>
            </select>
          </div>
          <div v-if="logForm.source === 'journal'" class="form-row">
            <label>Systemd Unit</label>
            <input v-model="logForm.unit" placeholder="llama-server" />
          </div>
          <div v-else class="form-row">
            <label>日志路径</label>
            <input v-model="logForm.path" placeholder="/var/log/llama-server.log" />
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn cancel" @click="$emit('close')">取消</button>
          <button type="submit" class="btn submit" :disabled="loading">
            {{ loading ? '保存中...' : (isEdit ? '更新' : '添加') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  host: { type: Object, default: null }
})

const emit = defineEmits(['close', 'save'])

const isEdit = computed(() => !!props.host)

// 默认表单值
const defaultLlama = { host: '', port: 8080, interval: 1.0, timeout: 3.0, slow_interval: 30.0 }
const defaultVllm = { host: '', port: 8100, interval: 1.0, timeout: 3.0 }
const defaultSsh = { host: '', port: 22, user: 'root', password: '', key_path: '' }
const defaultLog = { source: 'journal', unit: 'llama-server', path: '', follow: true, catchup_sec: 30 }

const llamaForm = ref({ ...defaultLlama })
const vllmForm = ref({ ...defaultVllm })
const sshForm = ref({ ...defaultSsh })
const logForm = ref({ ...defaultLog })
const enableLlama = ref(false)
const enableVllm = ref(false)

const form = ref({
  id: '',
  name: '',
  llama: [defaultLlama],
  ssh: defaultSsh,
  log: defaultLog,
  process: { name: 'llama-server' },
  systemd_unit: 'llama-server.service',
  disk_mounts: ['/']
})

const loading = ref(false)

// 监听 host 变化，填充表单
watch(() => props.host, (newHost) => {
  if (newHost) {
    form.value.id = newHost.id || ''
    form.value.name = newHost.name || ''
    
    // llama
    const llama = newHost.llama
    if (llama && llama.length > 0) {
      llamaForm.value = { ...defaultLlama, ...llama[0] }
      enableLlama.value = true
      form.value.llama = [llamaForm.value]
    } else {
      enableLlama.value = false
    }
    
    // vllm
    const vllm = newHost.vllm
    if (vllm) {
      vllmForm.value = { ...defaultVllm, ...vllm }
      enableVllm.value = true
      form.value.vllm = vllmForm.value
    } else {
      enableVllm.value = false
    }
    
    // ssh
    const ssh = newHost.ssh || defaultSsh
    sshForm.value = { ...defaultSsh, ...ssh }
    form.value.ssh = sshForm.value
    
    // log
    const log = newHost.log || defaultLog
    logForm.value = { ...defaultLog, ...log }
    form.value.log = logForm.value
  } else {
    resetForm()
  }
}, { immediate: true })

function resetForm() {
  form.value = {
    id: '',
    name: '',
    llama: [{ ...defaultLlama }],
    ssh: { ...defaultSsh },
    log: { ...defaultLog },
    process: { name: 'llama-server' },
    systemd_unit: 'llama-server.service',
    disk_mounts: ['/']
  }
  llamaForm.value = { ...defaultLlama }
  vllmForm.value = { ...defaultVllm }
  enableLlama.value = true
  enableVllm.value = false
  sshForm.value = { ...defaultSsh }
  logForm.value = { ...defaultLog }
}

function handleSubmit() {
  // 验证至少启用一个引擎
  if (!enableLlama.value && !enableVllm.value) {
    alert('请至少启用一个引擎（llama-server 或 vLLM）')
    return
  }
  
  // 构建提交数据
  const data = { ...form.value }
  
  if (enableLlama.value) {
    data.llama = [llamaForm.value]
  } else {
    delete data.llama
  }
  
  if (enableVllm.value) {
    data.vllm = { ...vllmForm.value }
  } else {
    delete data.vllm
  }
  
  loading.value = true
  emit('save', data, () => {
    loading.value = false
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  width: 560px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
}

.close-btn:hover {
  color: var(--text);
}

.modal-body {
  padding: 20px;
}

.form-section {
  margin-bottom: 20px;
}

.form-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--cyan);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  text-transform: none;
  letter-spacing: normal;
  font-weight: 400;
  font-size: 12px;
  color: var(--text-dim);
  margin-left: auto;
}

.toggle-label input[type="checkbox"] {
  appearance: none;
  width: 36px;
  height: 20px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 10px;
  position: relative;
  cursor: pointer;
  margin: 0;
  transition: background 0.2s;
}

.toggle-label input[type="checkbox"]::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: var(--text-dim);
  border-radius: 50%;
  top: 1px;
  left: 1px;
  transition: transform 0.2s, background 0.2s;
}

.toggle-label input[type="checkbox"]:checked {
  background: var(--cyan);
  border-color: var(--cyan);
}

.toggle-label input[type="checkbox"]:checked::after {
  transform: translateX(16px);
  background: #000;
}

.form-row {
  margin-bottom: 12px;
}

.form-row label {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 4px;
}

.req {
  color: #ff4444;
}

.form-row input,
.form-row select {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-size: 13px;
  font-family: inherit;
}

.form-row input:focus,
.form-row select:focus {
  outline: none;
  border-color: var(--cyan);
  box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.2);
}

.form-row input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.btn {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text);
}

.btn:hover {
  background: var(--bg-hover);
}

.btn.cancel {
  color: var(--text-dim);
}

.btn.submit {
  background: var(--cyan);
  color: #000;
  border-color: var(--cyan);
}

.btn.submit:hover {
  background: #00d4e6;
}

.btn.submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

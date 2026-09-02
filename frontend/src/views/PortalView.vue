<template>
  <div class="portal">
    <BrandBar :hosts="hosts" :connected="connected" @add-host="showModal = true" />
    <main class="grid">
      <template v-if="hosts.length">
        <HostCard v-for="h in hosts" :key="h.id" :host="h" @edit="openEdit" @delete="confirmDelete" />
      </template>
      <div v-else class="glass placeholder" style="grid-column: 1 / -1; min-height: 300px">
        <span class="icon">◉</span>
        <span>未注册主机</span>
        <span class="small">点击右下角 + 按钮添加主机</span>
      </div>
      <!-- 添加主机浮动按钮 -->
      <button class="fab" @click="showModal = true" title="添加主机">+</button>
    </main>

    <!-- 表单模态框 -->
    <HostFormModal
      :visible="showModal"
      :host="editingHost"
      @close="closeModal"
      @save="handleSave"
    />

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal small">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="close-btn" @click="showDeleteConfirm = false">×</button>
        </div>
        <div class="modal-body">
          <p>确定要删除主机 <b>{{ deleteHost?.name }}</b>（{{ deleteHost?.id }}）吗？</p>
          <p class="hint">删除后将从 hosts.yaml 中移除并停止监控。</p>
        </div>
        <div class="modal-footer">
          <button class="btn cancel" @click="showDeleteConfirm = false">取消</button>
          <button class="btn danger" @click="handleDelete" :disabled="deleting">
            {{ deleting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BrandBar from '../components/BrandBar.vue'
import HostCard from '../components/HostCard.vue'
import HostFormModal from '../components/HostFormModal.vue'
import { usePortalStream } from '../stream'
import { api } from '../api'

const { hosts, connected } = usePortalStream()

const showModal = ref(false)
const editingHost = ref(null)
const showDeleteConfirm = ref(false)
const deleteHost = ref(null)
const deleting = ref(false)

function openEdit(host) {
  editingHost.value = host
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingHost.value = null
}

async function handleSave(formData, done) {
  try {
    if (editingHost.value) {
      await api.updateHost(editingHost.value.id, formData)
    } else {
      await api.addHost(formData)
    }
    closeModal()
    // 刷新主机列表
    window.location.reload()
  } catch (e) {
    alert('保存失败：' + (e.message || '未知错误'))
  } finally {
    done()
  }
}

function confirmDelete(host) {
  deleteHost.value = host
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!deleteHost.value) return
  deleting.value = true
  try {
    await api.deleteHost(deleteHost.value.id)
    showDeleteConfirm.value = false
    window.location.reload()
  } catch (e) {
    alert('删除失败：' + (e.message || '未知错误'))
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(360px, 100%), 1fr));
  gap: 16px;
  padding: 20px 24px;
}

.fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--cyan);
  color: #000;
  border: none;
  font-size: 28px;
  font-weight: 300;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 229, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, box-shadow 0.15s;
  z-index: 100;
}

.fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 229, 255, 0.6);
}

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
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal.small {
  width: 360px;
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

.modal-body p {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--text);
}

.hint {
  font-size: 12px;
  color: var(--text-dim);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
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

.btn.danger {
  background: var(--red);
  color: #fff;
  border-color: var(--red);
}

.btn.danger:hover {
  background: #e63946;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractApiError } from '@/api/http'

const router = useRouter()
const authStore = useAuthStore()

const mustChange = computed(() => authStore.currentUser?.mustChangePassword ?? false)

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

async function handleChangePassword() {
  errorMsg.value = ''
  successMsg.value = ''

  if (!form.currentPassword.trim() || !form.newPassword.trim() || !form.confirmPassword.trim()) {
    errorMsg.value = '请填写所有密码字段'
    return
  }
  if (form.newPassword.length < 6) { errorMsg.value = '新密码长度至少 6 个字符'; return }
  if (form.newPassword !== form.confirmPassword) { errorMsg.value = '两次输入的新密码不一致'; return }
  if (form.currentPassword === form.newPassword) { errorMsg.value = '新密码不能与当前密码相同'; return }

  loading.value = true
  try {
    await authStore.changePassword({ currentPassword: form.currentPassword, newPassword: form.newPassword })
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    successMsg.value = '密码修改成功'
    if (mustChange.value) { setTimeout(() => router.push(authStore.homePath), 1200) }
  } catch (err) {
    errorMsg.value = extractApiError(err, '修改密码失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>账号安全与密码管理</p>
    </div>

    <div v-if="mustChange" class="must-change-banner">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
        <path d="M12 8v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <circle cx="12" cy="16" r="0.5" fill="currentColor" stroke="none"/>
      </svg>
      <span>出于安全考虑，您需要先修改密码后才能继续使用系统</span>
    </div>

    <div class="settings-card">
      <h2 class="card-title">修改密码</h2>
      <form class="password-form" @submit.prevent="handleChangePassword">
        <div class="input-group">
          <label>当前密码</label>
          <input v-model="form.currentPassword" type="password" placeholder="输入当前密码" autocomplete="current-password" />
        </div>
        <div class="input-group">
          <label>新密码</label>
          <input v-model="form.newPassword" type="password" placeholder="输入新密码（至少 6 位）" autocomplete="new-password" />
        </div>
        <div class="input-group">
          <label>确认新密码</label>
          <input v-model="form.confirmPassword" type="password" placeholder="再次输入新密码" autocomplete="new-password" />
        </div>

        <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>
        <p v-if="successMsg" class="form-success">{{ successMsg }}</p>

        <button type="submit" class="btn-submit" :disabled="loading">
          <span v-if="!loading">保存修改</span>
          <span v-else>保存中...</span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-family: 'Manrope', system-ui, sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin-bottom: 4px; }
.page-header p { font-size: 0.88rem; color: var(--text-secondary); margin: 0; }

.must-change-banner {
  display: flex; align-items: center; gap: 10px; padding: 14px 18px;
  background: #fffbeb; border: 1px solid rgba(217, 119, 6, 0.2);
  border-radius: var(--radius-sm); color: #b45309; font-size: 0.88rem; font-weight: 500; margin-bottom: 24px;
}
.must-change-banner svg { flex-shrink: 0; color: #f59e0b; }

.settings-card {
  max-width: 480px; background: var(--surface-white); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); padding: 28px 32px; box-shadow: var(--shadow-xs);
}

.card-title { font-family: 'Manrope', system-ui, sans-serif; font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 22px; }

.password-form { display: flex; flex-direction: column; gap: 16px; }

.input-group { display: flex; flex-direction: column; gap: 4px; }
.input-group label { font-family: 'Manrope', system-ui, sans-serif; font-size: 0.8rem; font-weight: 700; color: var(--text-secondary); }

.input-group input {
  width: 100%; padding: 10px 14px; border: 1.5px solid var(--border-default); border-radius: var(--radius-sm);
  font-size: 0.9rem; font-family: inherit; color: var(--text-primary); background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s; outline: none;
}
.input-group input::placeholder { color: var(--text-muted); }
.input-group input:focus { border-color: var(--brand-primary); box-shadow: var(--shadow-glow); }

.form-error { font-size: 0.82rem; color: #dc2626; margin: 0; font-weight: 500; }
.form-success { font-size: 0.82rem; color: #059669; margin: 0; font-weight: 500; }

.btn-submit {
  padding: 11px 24px; border-radius: var(--radius-full); background: var(--brand-primary);
  color: #fff; font-family: 'Manrope', system-ui, sans-serif; font-size: 0.88rem; font-weight: 700;
  cursor: pointer; transition: all var(--ease-out); box-shadow: 0 4px 14px rgba(29, 78, 216, 0.2); margin-top: 4px;
}
.btn-submit:hover:not(:disabled) { background: var(--brand-primary-dark); transform: translateY(-1px); box-shadow: 0 6px 20px rgba(29, 78, 216, 0.3); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
</style>

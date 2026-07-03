<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractApiError } from '@/api/http'
import type { LoginPayload } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive<LoginPayload>({ loginId: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  if (!form.loginId.trim() || !form.password.trim()) {
    errorMsg.value = '请输入登录标识和密码'
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    await authStore.login({ loginId: form.loginId.trim(), password: form.password })
    router.push(authStore.resolveLandingPath())
  } catch (err) {
    errorMsg.value = extractApiError(err, '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">

    <div class="login-card">
      <!-- Brand -->
      <a href="/" class="login-brand">
        <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
          <defs>
            <linearGradient id="lg2" x1="2" y1="2" x2="30" y2="30">
              <stop offset="0" stop-color="#1d4ed8" />
              <stop offset="1" stop-color="#0284c7" />
            </linearGradient>
          </defs>
          <circle cx="16" cy="16" r="14" fill="none" stroke="url(#lg2)" stroke-width="1.8" />
          <circle cx="16" cy="15" r="4" fill="url(#lg2)" opacity="0.9" />
          <circle cx="16" cy="14" r="1.8" fill="#fff" opacity="0.9" />
        </svg>
        <span>KnowOcean</span>
      </a>

      <h1>欢迎回来</h1>
      <p class="login-subtitle">登录您的 KnowOcean 知识平台账号</p>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">登录标识</label>
          <input
            v-model="form.loginId"
            type="text"
            class="form-input"
            placeholder="用户名或邮箱"
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="输入密码"
            autocomplete="current-password"
          />
        </div>

        <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>

        <button type="submit" class="btn-login" :disabled="loading">
          <span v-if="!loading">登录</span>
          <span v-else>登录中...</span>
        </button>
      </form>

      <p class="form-footer">
        还没有账号？<a href="/">返回首页注册</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-root);
  padding: 40px 24px;
  position: relative;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 42px 38px;
  background: var(--surface-white);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Manrope', system-ui, sans-serif;
  font-weight: 800;
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: 28px;
  text-decoration: none;
}

.login-card h1 {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.login-subtitle {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin-bottom: 28px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid var(--border-default);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-family: inherit;
  color: var(--text-primary);
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}

.form-group input::placeholder { color: var(--text-muted); }

.form-group input:focus {
  border-color: var(--brand-primary);
  box-shadow: var(--shadow-glow);
}

.form-error {
  font-size: 0.82rem;
  color: #dc2626;
  margin: 0;
  font-weight: 500;
}

.btn-login {
  width: 100%;
  padding: 12px 24px;
  border-radius: var(--radius-full);
  background: var(--brand-primary);
  color: #fff;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--ease-out);
  margin-top: 4px;
  box-shadow: 0 4px 14px rgba(29, 78, 216, 0.2);
}

.btn-login:hover:not(:disabled) {
  background: var(--brand-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(29, 78, 216, 0.3);
}

.btn-login:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 0.86rem;
  color: var(--text-muted);
}

.form-footer a {
  color: var(--brand-primary);
  font-weight: 600;
}

.form-footer a:hover { text-decoration: underline; }
</style>

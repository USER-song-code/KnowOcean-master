<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const userName = computed(() => authStore.currentUser?.displayName ?? '用户')

// ── Sidebar collapse ──
const sidebarCollapsed = ref(false)
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// ── User menu ──
const showUserMenu = ref(false)
function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
}

async function handleLogout() {
  showUserMenu.value = false
  await authStore.logout()
  router.push('/')
}

function onDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-wrapper')) {
    showUserMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

// ── Active menu ──
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/app/documents')) return 'documents'
  if (path.startsWith('/app/qa')) return 'qa'
  if (path.startsWith('/app/assistant')) return 'assistant'
  if (path.startsWith('/app/groups')) return 'groups'
  if (path.startsWith('/app/admin/metrics')) return 'metrics'
  if (path.startsWith('/app/admin/operation-logs')) return 'oplogs'
  if (path.startsWith('/app/admin')) return 'admin'
  if (path.startsWith('/app/settings')) return 'settings'
  return 'documents'
})

// ── Menu items ──
const menuItems = computed(() => {
  const role = authStore.currentUser?.systemRole
  const items = [
    { key: 'documents', label: '文档管理', path: '/app/documents', roles: ['USER'], icon: 'doc' },
    { key: 'qa', label: '知识库问答', path: '/app/qa', roles: ['USER'], icon: 'qa' },
    { key: 'assistant', label: 'AI 助手', path: '/app/assistant', roles: ['USER'], icon: 'bot' },
    { key: 'groups', label: '协作小组', path: '/app/groups', roles: ['USER'], icon: 'group' },
  ]
  return items.filter(i => role && (i.roles as readonly string[]).includes(role))
})

const bottomItems = computed(() => {
  const role = authStore.currentUser?.systemRole
  const items = [
    { key: 'admin', label: '用户管理', path: '/app/admin/users', roles: ['ADMIN'], icon: 'admin' },
    { key: 'metrics', label: '使用统计', path: '/app/admin/metrics', roles: ['ADMIN'], icon: 'chart' },
    { key: 'oplogs', label: '操作日志', path: '/app/admin/operation-logs', roles: ['ADMIN'], icon: 'oplogs' },
    { key: 'settings', label: '系统设置', path: '/app/settings', roles: ['ADMIN', 'USER'], icon: 'settings' },
  ]
  return items.filter(i => role && (i.roles as readonly string[]).includes(role))
})

function navigateTo(path: string) {
  router.push(path)
}

// ── SVG icons ──
const iconPaths: Record<string, string> = {
  doc: `<path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-6Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M14 2v6h6" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>`,
  qa: `<circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="1.6"/><path d="m19 19-3-3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>`,
  bot: `<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/>`,
  group: `<circle cx="7" cy="7" r="3" stroke="currentColor" stroke-width="1.6"/><circle cx="17" cy="7" r="3" stroke="currentColor" stroke-width="1.6"/><path d="M1 20v-1a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5v1" stroke="currentColor" stroke-width="1.6"/><path d="M15 14h2a5 5 0 0 1 5 5v1" stroke="currentColor" stroke-width="1.6"/>`,
  admin: `<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="1.6"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.6"/><path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" stroke-width="1.6"/><path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="1.6"/>`,
  chart: `<path d="M3 3v18h18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M7 16l4-8 4 4 4-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>`,
  settings: `<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M4.93 4.93l2.12 2.12m9.9 9.9 2.12 2.12M19.07 4.93l-2.12 2.12m-9.9 9.9-2.12 2.12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>`,
  oplogs: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M14 2v6h6" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 18v-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M9 15h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>`,
}
</script>

<template>
  <div class="app-layout" :class="{ collapsed: sidebarCollapsed }">
    <!-- ════════════ Sidebar ════════════ -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-brand" @click="router.push('/')">
        <div class="brand-icon">
          <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
            <defs>
              <linearGradient id="sGrad" x1="2" y1="2" x2="30" y2="30">
                <stop offset="0" stop-color="#1d4ed8" />
                <stop offset="1" stop-color="#0284c7" />
              </linearGradient>
            </defs>
            <circle cx="16" cy="16" r="14" fill="none" stroke="url(#sGrad)" stroke-width="1.6"/>
            <circle cx="16" cy="15" r="5" fill="url(#sGrad)" opacity="0.9"/>
            <circle cx="16" cy="14" r="2" fill="#fff" opacity="0.9"/>
          </svg>
        </div>
        <div v-show="!sidebarCollapsed" class="brand-text">
          <span class="brand-name">KnowOcean</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <span v-show="!sidebarCollapsed" class="nav-section-label">工作区</span>
        <div
          v-for="item in menuItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeMenu === item.key }"
          :title="sidebarCollapsed ? item.label : undefined"
          @click="navigateTo(item.path)"
        >
          <span class="nav-item__indicator" />
          <span class="nav-icon" v-html="`<svg width='20' height='20' viewBox='0 0 24 24' fill='none'>${iconPaths[item.icon]}</svg>`" />
          <span v-show="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </div>
      </nav>

      <!-- Bottom -->
      <div class="sidebar-bottom">
        <span v-show="!sidebarCollapsed" class="nav-section-label">系统</span>
        <div
          v-for="item in bottomItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeMenu === item.key }"
          :title="sidebarCollapsed ? item.label : undefined"
          @click="navigateTo(item.path)"
        >
          <span class="nav-item__indicator" />
          <span class="nav-icon" v-html="`<svg width='20' height='20' viewBox='0 0 24 24' fill='none'>${iconPaths[item.icon]}</svg>`" />
          <span v-show="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </div>
      </div>
    </aside>

    <!-- ════════════ Main Area ════════════ -->
    <div class="main-area">
      <!-- Topbar -->
      <header class="topbar">
        <div class="topbar-left">
          <button class="btn-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? '展开' : '折叠'">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M3 6h18M3 12h12M3 18h18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="breadcrumb">
            <span class="breadcrumb-current">{{ route.meta.title || '知识海洋平台' }}</span>
          </div>
        </div>
        <div class="topbar-right">
          <div class="user-menu-wrapper">
            <button class="user-chip" :class="{ 'is-open': showUserMenu }" @click="toggleUserMenu">
              <span class="user-chip__avatar">{{ userName.charAt(0).toUpperCase() }}</span>
              <span class="user-chip__name">{{ userName }}</span>
              <svg class="user-chip__caret" width="12" height="12" viewBox="0 0 24 24" fill="none">
                <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div v-if="showUserMenu" class="user-dropdown">
              <div class="dropdown-header">
                <div class="dropdown-avatar">{{ userName.charAt(0).toUpperCase() }}</div>
                <div class="dropdown-info">
                  <span class="dropdown-name">{{ userName }}</span>
                  <span class="dropdown-role">{{ authStore.isAdmin ? '系统管理员' : '用户' }}</span>
                </div>
              </div>
              <button class="dropdown-item" @click="handleLogout">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
                  <path d="m16 17 5-5-5-5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M21 12H9" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
                </svg>
                退出登录
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Content -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ════════════ Layout ════════════ */
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--surface-root);
}

/* ════════════ Sidebar ════════════ */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #fff;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-default);
  transition: width 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 50;
}

.collapsed .sidebar { width: 64px; }

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--surface-accent);
  flex-shrink: 0;
}

.brand-name {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 1rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.collapsed .sidebar-brand {
  justify-content: center;
  padding: 18px 0;
}

/* Nav sections */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.sidebar-bottom {
  padding: 8px 8px 16px;
  border-top: 1px solid var(--border-subtle);
}

.nav-section-label {
  display: block;
  padding: 6px 12px 8px;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}

/* Nav items */
.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  margin-bottom: 2px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.86rem;
  font-weight: 600;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--surface-muted);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--surface-accent);
  color: var(--brand-primary);
  font-weight: 700;
}

.nav-item__indicator {
  position: absolute;
  left: 2px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 18px;
  border-radius: 2px;
  background: transparent;
  transition: background 0.2s;
}

.nav-item.active .nav-item__indicator {
  background: var(--brand-primary);
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.7;
}

.nav-item.active .nav-icon { opacity: 1; }

.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed .nav-item {
  padding: 9px;
  justify-content: center;
}

/* ════════════ Main Area ════════════ */
.main-area {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.collapsed .main-area { margin-left: 64px; }

/* ════════════ Topbar ════════════ */
.topbar {
  height: 60px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 40;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.btn-toggle:hover {
  background: var(--surface-muted);
  color: var(--text-primary);
}

.breadcrumb-current {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* User chip */
.user-menu-wrapper { position: relative; }

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px 5px 5px;
  background: var(--surface-subtle);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.18s;
}

.user-chip:hover {
  border-color: var(--brand-primary-light);
  box-shadow: var(--shadow-glow);
}

.user-chip.is-open {
  border-color: var(--brand-primary);
  box-shadow: var(--shadow-glow);
}

.user-chip__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--brand-primary);
  color: #fff;
  font-size: 0.74rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-chip__name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-primary);
}

.user-chip__caret {
  color: var(--text-muted);
  transition: transform 0.2s;
  flex-shrink: 0;
}

.user-chip.is-open .user-chip__caret {
  transform: rotate(180deg);
  color: var(--brand-primary);
}

/* Dropdown */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 220px;
  background: #fff;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xl);
  z-index: 100;
  animation: dropdown-in 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

@keyframes dropdown-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px 12px;
  background: var(--surface-subtle);
}

.dropdown-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--brand-primary);
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  flex-shrink: 0;
}

.dropdown-info { display: flex; flex-direction: column; gap: 1px; }

.dropdown-name {
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--text-primary);
}

.dropdown-role {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--brand-primary);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  font-family: inherit;
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.dropdown-item:hover {
  background: #fef2f2;
  color: #dc2626;
}

/* ════════════ Content ════════════ */
.main-content {
  flex: 1;
  padding: 24px 28px;
}

/* ════════════ Responsive ════════════ */
@media (max-width: 768px) {
  .sidebar { width: 0; }
  .app-layout:not(.collapsed) .sidebar { width: 240px; }
  .main-area { margin-left: 0; }
  .collapsed .sidebar { width: 0; }
  .main-content { padding: 16px; }
}
</style>

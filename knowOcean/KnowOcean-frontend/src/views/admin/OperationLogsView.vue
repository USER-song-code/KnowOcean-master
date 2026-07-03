<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchOperationLogs, type ActivityItem } from '@/api/operation-logs'
import { extractApiError } from '@/api/http'
import PageHeaderHero from '@/components/layout/PageHeaderHero.vue'

// ── 类别筛选 ──
const categoryOptions: { key: string; label: string }[] = [
  { key: '', label: '全部' },
  { key: 'AUTH', label: '认证' },
  { key: 'ADMIN', label: '管理' },
  { key: 'DOCUMENT', label: '文档' },
  { key: 'QA', label: '知识问答' },
  { key: 'ASSISTANT', label: 'AI 助手' },
]

// ── 数据状态 ──
const items = ref<ActivityItem[]>([])
const total = ref(0)
const isLoading = ref(false)
const errorMsg = ref('')

const activeCategory = ref('')
const currentPage = ref(1)
const pageSize = 20

// ── 格式化 ──
function formatTime(iso: string): string {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  } catch { return iso }
}

function formatDetail(detail: Record<string, unknown>): string {
  if (!detail || Object.keys(detail).length === 0) return '-'
  // 特殊处理 LLM 调用
  if (detail.model) {
    const parts = []
    if (detail.model) parts.push(`模型: ${detail.model}`)
    if (detail.tokens != null) parts.push(`Token: ${detail.tokens}`)
    if (detail.cost != null) parts.push(`费用: ¥${detail.cost}`)
    return parts.join(' | ')
  }
  // 系统操作
  if (detail.targetUser) return `目标用户: ${detail.targetUser}`
  if (detail.fileName) return `${detail.fileName} (${((detail.fileSize as number) || 0).toLocaleString()} B)`
  return JSON.stringify(detail)
}

function getCategoryClass(cat: string): string {
  return `cat-badge cat-badge--${cat.toLowerCase() || 'default'}`
}

// ── 加载数据 ──
async function loadLogs() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const res = await fetchOperationLogs({
      category: activeCategory.value || undefined,
      page: currentPage.value,
      size: pageSize,
    })
    items.value = res.items
    total.value = res.total
  } catch (err) {
    errorMsg.value = extractApiError(err, '加载操作日志失败')
    items.value = []
  } finally {
    isLoading.value = false
  }
}

function onCategoryChange(cat: string) {
  activeCategory.value = cat
  currentPage.value = 1
  loadLogs()
}

const totalPages = (): number => Math.max(1, Math.ceil(total.value / pageSize))

onMounted(() => loadLogs())
</script>

<template>
  <div class="oplog-page">
    <PageHeaderHero
      eyebrow="系统管理"
      title="操作日志"
      description="查看所有用户的操作记录，包括登录、文档管理、LLM 调用等"
    >
      <template #actions>
        <button class="action-btn" @click="loadLogs">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新
        </button>
      </template>
    </PageHeaderHero>

    <!-- 错误 -->
    <div v-if="errorMsg" class="feedback feedback--error">{{ errorMsg }}</div>

    <!-- 类别筛选 -->
    <div class="filter-tabs">
      <button
        v-for="cat in categoryOptions"
        :key="cat.key"
        class="filter-tab"
        :class="{ 'is-active': activeCategory === cat.key }"
        type="button"
        @click="onCategoryChange(cat.key)"
      >{{ cat.label }}</button>
    </div>

    <!-- 加载 -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>加载操作日志...</p>
    </div>

    <!-- 空 -->
    <div v-else-if="items.length === 0" class="empty-state">
      <h3>暂无操作记录</h3>
      <p>系统操作将自动记录在此处</p>
    </div>

    <!-- 日志表格 -->
    <div v-else class="table-wrapper">
      <table class="log-table">
        <thead>
          <tr>
            <th class="th--num">编号</th>
            <th class="th--user">用户名</th>
            <th class="th--cat">类型</th>
            <th class="th--action">操作</th>
            <th class="th--detail">详情</th>
            <th class="th--time">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in items" :key="`${item.source}-${item.id}`">
            <td class="td--num">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
            <td class="td--user">
              <span class="user-chip">{{ item.username }}</span>
              <span class="user-id-chip">#{{ item.userId }}</span>
            </td>
            <td class="td--cat">
              <span :class="['cat-badge', `cat-badge--${item.category.toLowerCase()}`]">
                {{ item.categoryLabel }}
              </span>
            </td>
            <td class="td--action">{{ item.actionLabel }}</td>
            <td class="td--detail">{{ formatDetail(item.detail) }}</td>
            <td class="td--time">{{ formatTime(item.createdAt) }}</td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pagination" v-if="totalPages() > 1">
        <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage--; loadLogs()">上一页</button>
        <span class="page-info">{{ currentPage }} / {{ totalPages() }} (共 {{ total }} 条)</span>
        <button class="page-btn" :disabled="currentPage >= totalPages()" @click="currentPage++; loadLogs()">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ════════════ Layout ════════════ */
.oplog-page {
  width: 100%;
  min-height: 100%;
}

/* ════════════ Action btn ════════════ */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.86rem;
  font-weight: 600;
  border: 1px solid var(--border-default);
  background: var(--surface-white);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.action-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
  background: var(--surface-subtle);
}

/* ════════════ Feedback ════════════ */
.feedback { padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.86rem; margin-bottom: 12px; }
.feedback--error { background: rgba(239,68,68,0.08); color: #ef4444; border: 1px solid rgba(239,68,68,0.15); }

/* ════════════ Loading ════════════ */
.loading-state { text-align: center; padding: 80px 24px; }
.loading-state p { margin-top: 16px; color: var(--text-muted); }
.spinner {
  width: 32px; height: 32px; margin: 0 auto;
  border: 3px solid var(--surface-muted); border-top-color: var(--brand-primary);
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ════════════ Empty ════════════ */
.empty-state { text-align: center; padding: 64px 24px; }
.empty-state h3 { font-size: 1rem; color: var(--text-primary); margin: 0 0 6px; }
.empty-state p { color: var(--text-muted); font-size: 0.84rem; margin: 0; }

/* ════════════ Filter Tabs ════════════ */
.filter-tabs { display: flex; gap: 4px; margin-bottom: 20px; }
.filter-tab {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 18px; border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm); background: var(--surface-white);
  color: var(--text-secondary); font-size: 0.88rem; font-weight: 600;
  font-family: inherit; cursor: pointer; transition: all 0.2s ease;
}
.filter-tab:hover { color: var(--text-primary); border-color: var(--border-default); }
.filter-tab.is-active { background: var(--brand-primary); color: #fff; border-color: var(--brand-primary); }

/* ════════════ Table ════════════ */
.table-wrapper {
  background: var(--surface-white);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.log-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
.log-table th {
  padding: 12px 16px; font-size: 0.72rem; font-weight: 700; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.05em; text-align: left;
  background: var(--surface-subtle); border-bottom: 1px solid var(--border-default);
}
.log-table td {
  padding: 11px 16px; border-bottom: 1px solid var(--border-subtle);
  color: var(--text-secondary); vertical-align: middle;
}
.log-table tbody tr:hover { background: rgba(74,144,217,0.02); }
.log-table tbody tr:last-child td { border-bottom: none; }

.th--num { width: 60px; text-align: center; }
.th--user { width: 140px; }
.th--cat { width: 90px; }
.th--action { width: 110px; }
.th--detail { }
.th--time { width: 170px; }

.td--num { text-align: center; font-variant-numeric: tabular-nums; color: var(--text-muted); }
.td--time { font-size: 0.8rem; font-variant-numeric: tabular-nums; white-space: nowrap; }

.user-chip { font-weight: 600; color: var(--text-primary); }
.user-id-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem; color: var(--text-muted); margin-left: 6px;
}

/* Category badges */
.cat-badge {
  display: inline-flex; padding: 3px 10px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600;
}
.cat-badge--auth { background: rgba(99,102,241,0.1); color: #6366f1; }
.cat-badge--admin { background: rgba(245,158,11,0.1); color: #d97706; }
.cat-badge--document { background: rgba(16,185,129,0.1); color: #10b981; }
.cat-badge--qa { background: rgba(59,130,246,0.1); color: #3b82f6; }
.cat-badge--assistant { background: rgba(139,92,246,0.1); color: #8b5cf6; }

.td--detail { font-size: 0.78rem; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Pagination */
.pagination {
  display: flex; align-items: center; justify-content: center; gap: 16px;
  padding: 14px 16px; border-top: 1px solid var(--border-subtle);
}
.page-btn {
  padding: 6px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-default);
  background: var(--surface-white); font-size: 0.82rem; font-weight: 600;
  font-family: inherit; cursor: pointer; color: var(--text-secondary);
  transition: all 0.15s ease;
}
.page-btn:hover:not(:disabled) { background: var(--surface-subtle); color: var(--text-primary); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 0.82rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }
</style>

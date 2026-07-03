import http from './http'
import type { ApiResponse } from './http'

// ─────────────────────────────────────────────
// 类型定义
// ─────────────────────────────────────────────

export interface ActivityItem {
  source: 'SYS_OP' | 'LLM'
  id: number
  userId: number
  username: string
  category: string
  action: string
  categoryLabel: string
  actionLabel: string
  detail: Record<string, unknown>
  createdAt: string
}

export interface OperationLogsResponse {
  items: ActivityItem[]
  total: number
  page: number
  size: number
}

// ─────────────────────────────────────────────
// API 函数
// ─────────────────────────────────────────────

/**
 * 获取统一操作日志（系统操作 + LLM 调用）
 *
 * GET /api/admin/operation-logs?userId=&category=&page=&size=
 */
export async function fetchOperationLogs(params: {
  userId?: number
  category?: string
  page?: number
  size?: number
}): Promise<OperationLogsResponse> {
  const { data } = await http.get<ApiResponse<OperationLogsResponse>>('/admin/operation-logs', { params })
  return unwrapApiResponse(data, '加载操作日志失败')
}

// ─────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────

function unwrapApiResponse<T>(payload: ApiResponse<T>, fallbackMessage: string): T {
  if (!payload.success) {
    throw new Error(payload.message ?? fallbackMessage)
  }
  return payload.data
}

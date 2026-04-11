import { getToken } from "./auth";
import type {
  Transaction, Task, TimelineItem, HealthScore,
  AuditEvent, EventLog, DashboardStats, AuthResponse,
  User,
} from "./types";

const API_BASE = "/api/v1";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (res.status === 403) {
    throw new Error("Forbidden: You don't have permission to access this resource.");
  }
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Auth
export const authLogin = (email: string, password: string) =>
  apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

// Transactions
export const getTransactions = () => apiFetch<Transaction[]>("/transactions");
export const getTransaction = (id: string) => apiFetch<Transaction>(`/transactions/${id}`);
export const getTransactionMembers = (id: string) => apiFetch<User[]>(`/transactions/${id}/members`);
export const createTransaction = (data: { org_id: string; title: string; description?: string; property_address?: string; close_date?: string }) =>
  apiFetch<Transaction>("/transactions", { method: "POST", body: JSON.stringify(data) });

// Health
export const getTransactionHealth = (id: string) => apiFetch<HealthScore>(`/transactions/${id}/health`);

// Timeline
export const getTransactionTimeline = (txnId: string) => apiFetch<TimelineItem[]>(`/timeline/transactions/${txnId}`);
export const markTimelineItemComplete = (itemId: string) =>
  apiFetch<TimelineItem>(`/timeline/${itemId}/complete`, { method: "PATCH" });

// Tasks
export const getTransactionTasks = (txnId: string) => apiFetch<Task[]>(`/transactions/${txnId}/tasks`);
export const createTask = (txnId: string, data: { title: string; description?: string; assignee_id?: string; due_at?: string; severity?: string }) =>
  apiFetch<Task>(`/transactions/${txnId}/tasks`, { method: "POST", body: JSON.stringify(data) });
export const getMyTasks = () => apiFetch<Task[]>("/tasks/mine");
export const updateTaskStatus = (id: string, status: string) =>
  apiFetch<Task>(`/tasks/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
export const assignTask = (id: string, assignee_id: string) =>
  apiFetch<Task>(`/tasks/${id}/assign`, { method: "PATCH", body: JSON.stringify({ assignee_id }) });

// Audit
export const getAuditEvents = (params?: { org_id: string; entity_type?: string; action?: string; page?: number; page_size?: number }) => {
  const query = new URLSearchParams();
  if (params?.org_id) query.set("org_id", params.org_id);
  if (params?.entity_type) query.set("entity_type", params.entity_type);
  if (params?.action) query.set("action", params.action);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  return apiFetch<{ items: AuditEvent[]; total: number; page: number; page_size: number; }>(`/audit?${query.toString()}`);
};

// Event Logs
export const getEventLogs = (txnId: string, eventType?: string) => {
  const query = eventType ? `?event_type=${eventType}` : "";
  return apiFetch<EventLog[]>(`/transactions/${txnId}/events${query}`);
};

// Admin
export const triggerDeadlineCheck = () =>
  apiFetch<{ message: string }>("/admin/check-deadlines", { method: "POST" });

// Dashboard
export const getDashboardStats = () => apiFetch<DashboardStats>("/dashboard/stats");

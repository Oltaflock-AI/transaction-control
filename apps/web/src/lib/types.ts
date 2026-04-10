// Matches backend DB schema exactly

export interface Org {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Membership {
  id: string;
  org_id: string;
  user_id: string;
  role: "member" | "admin";
  created_at: string;
  updated_at: string;
}

export type TransactionStatus = "draft" | "active" | "closed" | "cancelled";

export interface Transaction {
  id: string;
  org_id: string;
  title: string;
  description?: string;
  status: TransactionStatus;
  property_address?: string;
  close_date?: string;
  health_score?: HealthStatus;
  created_at: string;
  updated_at: string;
  // nested from API
  tasks?: Task[];
}

export type TaskStatus = "todo" | "in_progress" | "done" | "overdue";
export type TaskSeverity = "low" | "medium" | "high" | "critical";

export interface Task {
  id: string;
  transaction_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  assignee_id?: string;
  due_at?: string;
  offset_days?: number;
  category?: string;
  severity: TaskSeverity;
  dedupe_key?: string;
  created_at: string;
  updated_at: string;
  // joined fields from API
  transaction_title?: string;
}

export interface TimelineItem {
  id: string;
  transaction_id: string;
  label: string;
  description?: string;
  due_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  org_id: string;
  actor_id?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  detail: string;
  created_at: string;
  updated_at: string;
  // joined
  actor_name?: string;
}

export interface EventLog {
  id: string;
  transaction_id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  detail: string;
  created_at: string;
  updated_at: string;
}

export type HealthStatus = "GREEN" | "YELLOW" | "RED";

export interface HealthScore {
  score: HealthStatus;
  reasons: string[];
}

export interface DashboardStats {
  total_transactions: number;
  tasks_overdue: number;
  tasks_due_soon: number;
  deals_at_risk: Transaction[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

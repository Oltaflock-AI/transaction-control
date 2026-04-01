import type {
  Transaction, Task, TimelineItem, HealthScore,
  AuditEvent, EventLog, DashboardStats, User, Org, Membership,
} from "./types";

export const MOCK_ORG: Org = {
  id: "org-1",
  name: "Dev Organisation",
  slug: "dev-org",
  created_at: "2026-02-01T10:00:00Z",
  updated_at: "2026-02-01T10:00:00Z",
};

export const MOCK_USERS: User[] = [
  { id: "u1", email: "admin@dev.local", full_name: "Neeraj Admin", is_active: true, created_at: "2026-02-01T10:00:00Z", updated_at: "2026-02-01T10:00:00Z" },
  { id: "u2", email: "kawalpreet@dev.local", full_name: "Kawalpreet Singh", is_active: true, created_at: "2026-02-01T10:00:00Z", updated_at: "2026-02-01T10:00:00Z" },
  { id: "u3", email: "amaan@dev.local", full_name: "Amaan Khan", is_active: true, created_at: "2026-02-01T10:00:00Z", updated_at: "2026-02-01T10:00:00Z" },
];

export const MOCK_USER: User = MOCK_USERS[0];

export const MOCK_MEMBERSHIP: Membership = {
  id: "m1",
  org_id: "org-1",
  user_id: "u1",
  role: "admin",
  created_at: "2026-02-01T10:00:00Z",
  updated_at: "2026-02-01T10:00:00Z",
};

export const MOCK_TRANSACTIONS: Transaction[] = [
  {
    id: "t1", org_id: "org-1", title: "123 Oak Street Sale",
    description: "Residential sale in central Austin",
    status: "active", property_address: "123 Oak Street, Austin, TX 78701",
    close_date: "2026-04-15", health_score: "YELLOW",
    created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-28T14:00:00Z",
  },
  {
    id: "t2", org_id: "org-1", title: "456 Maple Ave Purchase",
    description: "Buyer-side purchase deal",
    status: "active", property_address: "456 Maple Ave, Austin, TX 78702",
    close_date: "2026-04-02", health_score: "RED",
    created_at: "2026-03-05T09:00:00Z", updated_at: "2026-03-27T11:00:00Z",
  },
  {
    id: "t3", org_id: "org-1", title: "789 Pine Blvd Listing",
    description: "New listing, pre-market prep",
    status: "draft", property_address: "789 Pine Blvd, Austin, TX 78703",
    close_date: "2026-05-01", health_score: "GREEN",
    created_at: "2026-03-20T08:00:00Z", updated_at: "2026-03-28T09:00:00Z",
  },
  {
    id: "t4", org_id: "org-1", title: "321 Elm Court Close",
    description: "Completed deal, all docs signed",
    status: "closed", property_address: "321 Elm Court, Austin, TX 78704",
    close_date: "2026-03-15", health_score: "GREEN",
    created_at: "2026-02-01T10:00:00Z", updated_at: "2026-03-15T16:00:00Z",
  },
];

export const MOCK_TIMELINE: Record<string, TimelineItem[]> = {
  t1: [
    { id: "tl1", transaction_id: "t1", label: "Review contract", description: "Review the contract with the client", due_at: "2026-03-04T10:00:00Z", completed_at: "2026-03-04T10:00:00Z", created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-04T10:00:00Z" },
    { id: "tl2", transaction_id: "t1", label: "Order inspection", description: "Schedule and order home inspection", due_at: "2026-03-08T10:00:00Z", completed_at: "2026-03-07T14:00:00Z", created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-07T14:00:00Z" },
    { id: "tl3", transaction_id: "t1", label: "Appraisal review", description: "Review appraisal report", due_at: "2026-03-20T10:00:00Z", completed_at: undefined, created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-01T10:00:00Z" },
    { id: "tl4", transaction_id: "t1", label: "Title search", description: "Complete title search", due_at: "2026-03-30T10:00:00Z", completed_at: undefined, created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-01T10:00:00Z" },
    { id: "tl5", transaction_id: "t1", label: "Final walkthrough", description: "Conduct final walkthrough before closing", due_at: "2026-04-14T10:00:00Z", completed_at: undefined, created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-01T10:00:00Z" },
  ],
  t2: [
    { id: "tl6", transaction_id: "t2", label: "Offer submitted", description: "Submit offer to seller", due_at: "2026-03-05T09:00:00Z", completed_at: "2026-03-05T09:00:00Z", created_at: "2026-03-05T09:00:00Z", updated_at: "2026-03-05T09:00:00Z" },
    { id: "tl7", transaction_id: "t2", label: "Inspection", description: "Home inspection", due_at: "2026-03-15T10:00:00Z", completed_at: "2026-03-14T10:00:00Z", created_at: "2026-03-05T09:00:00Z", updated_at: "2026-03-14T10:00:00Z" },
    { id: "tl8", transaction_id: "t2", label: "Financing approval", description: "Get financing approved", due_at: "2026-03-25T10:00:00Z", completed_at: undefined, created_at: "2026-03-05T09:00:00Z", updated_at: "2026-03-05T09:00:00Z" },
    { id: "tl9", transaction_id: "t2", label: "Closing", description: "Final closing", due_at: "2026-04-02T10:00:00Z", completed_at: undefined, created_at: "2026-03-05T09:00:00Z", updated_at: "2026-03-05T09:00:00Z" },
  ],
};

export const MOCK_TASKS: Task[] = [
  { id: "task1", transaction_id: "t1", title: "Schedule home inspection", description: "Coordinate with inspector", status: "done", assignee_id: "u1", due_at: "2026-03-10T17:00:00Z", severity: "medium", category: "Inspection", created_at: "2026-03-02T10:00:00Z", updated_at: "2026-03-09T10:00:00Z", transaction_title: "123 Oak Street Sale" },
  { id: "task2", transaction_id: "t1", title: "Order appraisal report", description: "Order appraisal from approved vendor", status: "in_progress", assignee_id: "u1", due_at: "2026-03-28T17:00:00Z", severity: "high", category: "Appraisal", created_at: "2026-03-10T10:00:00Z", updated_at: "2026-03-25T10:00:00Z", transaction_title: "123 Oak Street Sale" },
  { id: "task3", transaction_id: "t2", title: "Submit financing docs", description: "Submit all financing documents to lender", status: "todo", assignee_id: "u1", due_at: "2026-03-25T17:00:00Z", severity: "critical", category: "Financing", created_at: "2026-03-15T10:00:00Z", updated_at: "2026-03-15T10:00:00Z", transaction_title: "456 Maple Ave Purchase" },
  { id: "task4", transaction_id: "t1", title: "Review title report", description: "Review title report for issues", status: "todo", assignee_id: "u1", due_at: "2026-04-01T17:00:00Z", severity: "high", category: "Title", created_at: "2026-03-20T10:00:00Z", updated_at: "2026-03-20T10:00:00Z", transaction_title: "123 Oak Street Sale" },
  { id: "task5", transaction_id: "t2", title: "Confirm closing date", description: "Confirm final closing date with all parties", status: "overdue", assignee_id: "u1", due_at: "2026-03-27T17:00:00Z", severity: "critical", category: "Closing", created_at: "2026-03-22T10:00:00Z", updated_at: "2026-03-28T10:00:00Z", transaction_title: "456 Maple Ave Purchase" },
  { id: "task6", transaction_id: "t1", title: "Final walkthrough", description: "Conduct final walkthrough before closing", status: "todo", assignee_id: "u1", due_at: "2026-04-14T10:00:00Z", severity: "critical", category: "Closing", created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-01T10:00:00Z", transaction_title: "123 Oak Street Sale" },
];

export const MOCK_HEALTH: Record<string, HealthScore> = {
  t1: { status: "YELLOW", reasons: ["Appraisal not yet ordered", "Title search pending"] },
  t2: { status: "RED", reasons: ["Financing approval overdue", "Close date in 4 days", "1 critical task overdue"] },
  t3: { status: "GREEN", reasons: [] },
  t4: { status: "GREEN", reasons: [] },
};

export const MOCK_AUDIT: AuditEvent[] = [
  { id: "a1", org_id: "org-1", actor_id: "u1", actor_name: "Neeraj Admin", action: "transaction.created", entity_type: "transaction", entity_id: "t1", detail: "Created transaction '123 Oak Street Sale'", created_at: "2026-03-28T14:30:00Z", updated_at: "2026-03-28T14:30:00Z" },
  { id: "a2", org_id: "org-1", actor_id: "u1", actor_name: "Neeraj Admin", action: "task.status_updated", entity_type: "task", entity_id: "task2", detail: "Changed status of 'Order appraisal report' to in_progress", created_at: "2026-03-28T13:00:00Z", updated_at: "2026-03-28T13:00:00Z" },
  { id: "a3", org_id: "org-1", actor_id: "u1", actor_name: "Neeraj Admin", action: "timeline.completed", entity_type: "timeline", entity_id: "tl2", detail: "Marked 'Order inspection' as complete", created_at: "2026-03-27T11:00:00Z", updated_at: "2026-03-27T11:00:00Z" },
  { id: "a4", org_id: "org-1", actor_id: "u1", actor_name: "Kawalpreet", action: "task.created", entity_type: "task", entity_id: "task5", detail: "Created task 'Confirm closing date'", created_at: "2026-03-26T09:00:00Z", updated_at: "2026-03-26T09:00:00Z" },
  { id: "a5", org_id: "org-1", actor_id: undefined, actor_name: "System", action: "task.marked_overdue", entity_type: "task", entity_id: "task5", detail: "Task 'Confirm closing date' marked overdue by deadline checker", created_at: "2026-03-28T15:00:00Z", updated_at: "2026-03-28T15:00:00Z" },
  { id: "a6", org_id: "org-1", actor_id: "u1", actor_name: "Neeraj Admin", action: "transaction.closed", entity_type: "transaction", entity_id: "t4", detail: "Closed transaction '321 Elm Court Close'", created_at: "2026-03-15T16:00:00Z", updated_at: "2026-03-15T16:00:00Z" },
];

export const MOCK_EVENT_LOGS: EventLog[] = [
  { id: "el1", transaction_id: "t2", event_type: "task.overdue", entity_type: "task", entity_id: "task5", detail: JSON.stringify({ task_title: "Confirm closing date", severity: "critical" }), created_at: "2026-03-28T15:00:00Z", updated_at: "2026-03-28T15:00:00Z" },
  { id: "el2", transaction_id: "t2", event_type: "task.due_soon", entity_type: "task", entity_id: "task3", detail: JSON.stringify({ task_title: "Submit financing docs", severity: "critical", hours_remaining: 36 }), created_at: "2026-03-24T05:00:00Z", updated_at: "2026-03-24T05:00:00Z" },
  { id: "el3", transaction_id: "t1", event_type: "timeline.generated", entity_type: "transaction", entity_id: "t1", detail: JSON.stringify({ items_count: 5, tasks_count: 6 }), created_at: "2026-03-01T10:00:00Z", updated_at: "2026-03-01T10:00:00Z" },
];

export const MOCK_DASHBOARD_STATS: DashboardStats = {
  total_transactions: 4,
  tasks_overdue: 2,
  tasks_due_soon: 1,
  deals_at_risk: [MOCK_TRANSACTIONS[1]],
};

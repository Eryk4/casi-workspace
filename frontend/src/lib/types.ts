export type OrganizationId = string;

export type ApiQueryValue = string | number | boolean | null | undefined;

export type ApiQuery = Record<string, ApiQueryValue>;

export type ApiRequestMethod = "GET" | "POST" | "PATCH" | "DELETE";

export type DataViewStatus = "idle" | "loading" | "ready" | "unauthenticated" | "forbidden" | "server-error" | "error";

export type DataViewErrorState<TStatus extends DataViewStatus = DataViewStatus> = {
  status: Exclude<TStatus, "idle" | "loading" | "ready">;
  title: string;
  description: string;
};

export type SessionUser = {
  id: string;
  login: string;
  display_name?: string;
  role?: string;
  organization_id?: OrganizationId;
};

export type CurrentSession = {
  authenticated: boolean;
  user?: SessionUser;
  organization_id?: OrganizationId;
};

export type ModuleMetric = {
  label: string;
  value: string;
  hint: string;
};

export type ModuleAction = {
  label: string;
  href?: string;
};

export type ApiEnvelope<T> = T & {
  error?: string;
  message?: string;
};

export type DashboardCards = {
  nowe_faktury: number;
  do_weryfikacji: number;
  podejrzenia_duplikatow: number;
  pewne_duplikaty: number;
  nowi_kontrahenci: number;
  aktywne_przypomnienia: number;
};

export type DashboardAlertCategory = "invoices" | "tasks" | "knowledge" | "integrations";

export type DashboardAlert = {
  severity?: "info" | "warning" | "danger" | "success";
  category?: DashboardAlertCategory;
  title?: string;
  description?: string;
  action_label?: string;
  action_view?: string;
  action_bucket?: string;
};

export type DashboardReminder = {
  task_id?: number;
  title?: string;
  task_type?: string;
  priority?: string;
  due_at?: string;
  remind_at?: string;
};

export type DashboardKnowledgeQueueItem = {
  knowledge_document_id?: number;
  title?: string;
  business_status_label?: string;
  workflow_status_label?: string;
  library_path_label?: string;
  updated_at?: string;
};

export type DashboardEvent = {
  id?: number;
  event_type?: string;
  event_time?: string;
  entity_type?: string;
  decision_reason?: string;
  actor?: string;
  details?: unknown;
};

export type DashboardSnapshot = {
  cards: DashboardCards;
  operational_alerts: DashboardAlert[];
  active_reminders: DashboardReminder[];
  knowledge_queue: DashboardKnowledgeQueueItem[];
  recent_events: DashboardEvent[];
};

export type InvoiceVerificationItem = {
  invoice_id: number;
  invoice_number?: string;
  ksef_number?: string;
  issuer_name?: string;
  issuer_nip?: string;
  status?: string;
  duplicate_type?: string;
  source?: string;
  incoming_date?: string;
  issue_date?: string;
  gross_amount?: number;
  currency?: string;
  file_name?: string;
  flag_reason?: string | null;
  organization_name?: string;
  assigned_user_id?: number | null;
  assigned_user_name?: string | null;
  assigned_user_role?: string | null;
  invoice_comment_count?: number;
  pending_override_count?: number | null;
  latest_request_at?: string | null;
};

export type InvoiceVerificationSection = {
  title: string;
  description?: string;
  count: number;
  action_key?: string;
  items: InvoiceVerificationItem[];
};

export type InvoiceVerificationInbox = {
  summary: {
    total_open_count: number;
    generated_at?: string;
  };
  sections: Record<string, InvoiceVerificationSection>;
};

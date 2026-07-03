export type InvoiceStatus = "nowa" | "weryfikacja" | "zaakceptowana" | "odrzucona" | string;
export type InvoiceWorkflowState = "w_pracy" | "gotowa_do_przekazania" | "przekazana" | "zamknieta" | string;
export type InvoiceDuplicateType = "brak" | "podejrzenie" | "pewny" | string;

export type InvoiceRecord = {
  id?: number;
  invoice_id?: number;
  organization_id?: number;
  organization_name?: string;
  invoice_number?: string | null;
  ksef_number?: string | null;
  issuer_name?: string | null;
  issuer_nip?: string | null;
  contractor_name?: string | null;
  issue_date?: string | null;
  incoming_date?: string | null;
  sale_date?: string | null;
  gross_amount?: number | string | null;
  currency?: string | null;
  status?: InvoiceStatus | null;
  workflow_state?: InvoiceWorkflowState | null;
  duplicate_type?: InvoiceDuplicateType | null;
  source?: string | null;
  file_name?: string | null;
  flag_reason?: string | null;
  assigned_user_id?: number | null;
  assigned_user_name?: string | null;
  assigned_user_role?: string | null;
  invoice_comment_count?: number | null;
  updated_at?: string | null;
  created_at?: string | null;
};

export type InvoiceVerificationItem = InvoiceRecord & {
  invoice_id: number;
  attention_label?: string | null;
  age_days?: number | null;
  sla_days?: number | null;
  sla_breached?: boolean;
  pending_override_count?: number | null;
  latest_request_at?: string | null;
  compare_target_invoice_id?: number | null;
};

export type InvoiceVerificationSection = {
  key: string;
  title: string;
  description: string;
  count: number;
  sla_days: number;
  sla_breached_count: number;
  oldest_age_days: number;
  items: InvoiceVerificationItem[];
};

export type InvoiceVerificationWorkspace = {
  summary: {
    total_open_count: number;
    total_sla_breached: number;
    oldest_age_days: number;
    generated_at: string;
    active_bucket: string;
  };
  bucket_order: string[];
  sections: Record<string, InvoiceVerificationSection>;
};

export type InvoiceDetail = {
  invoice: InvoiceRecord;
  relations?: Array<Record<string, unknown>>;
  similar_invoices?: InvoiceRecord[];
  comments?: Array<Record<string, unknown>>;
  history?: Array<Record<string, unknown>>;
  approval_requests?: Array<Record<string, unknown>>;
  contractor?: Record<string, unknown> | null;
  linked_tasks?: Array<Record<string, unknown>>;
  document_intake_items?: Array<Record<string, unknown>>;
  exceptions?: Array<Record<string, unknown>>;
  handoff_batches?: Array<Record<string, unknown>>;
  source_trace?: Record<string, unknown>;
  document_trace?: Record<string, unknown>;
  ksef_protected?: boolean;
  ksef_corrections?: Record<string, unknown>;
  field_provenance?: Record<string, unknown>;
  workflow?: {
    state?: string;
    state_label?: string;
    next_actions?: Array<Record<string, unknown>>;
    [key: string]: unknown;
  };
};

export type InvoiceListFilters = {
  search?: string;
  status?: string;
  workflow_state?: string;
  duplicate_type?: string;
  source?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
};

export type InvoiceActionKind =
  | "confirm-duplicate"
  | "reject-duplicate"
  | "mark-ready"
  | "handoff"
  | "undo-last"
  | "reopen"
  | "close";

export type InvoiceActionPayload = {
  reason?: string;
  handoff_target?: string;
  handoff_note?: string;
};

export type InvoiceActionRequest = {
  action: InvoiceActionKind;
  payload?: InvoiceActionPayload;
};

export type InvoiceActionResult = InvoiceRecord;

export type InvoiceCommentPayload = {
  note_text: string;
  parent_comment_id?: number;
};

export type InvoiceCommentRecord = {
  invoice_comment_id?: number;
  id?: number;
  invoice_id?: number;
  organization_id?: number;
  parent_comment_id?: number | null;
  note_text: string;
  created_by_user_id?: number;
  created_by_user_name?: string | null;
  author_name?: string | null;
  created_at?: string | null;
};

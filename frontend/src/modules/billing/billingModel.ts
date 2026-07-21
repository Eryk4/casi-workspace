import { ApiContractError, ApiError } from "@/lib/api";
import type { DataViewErrorState, DataViewStatus } from "@/lib/types";
import { readInvoiceList } from "../invoices/api";
import type { InvoiceRecord } from "../invoices/types";
import type { ContractorRecord } from "../crm/crmModel";
import type { WorkItemRecord } from "../work-items/workItemsModel";

export type BillingStatus = DataViewStatus;

export type BillingErrorState = DataViewErrorState<BillingStatus>;

export type BillingBalanceRecord = {
  billing_payer_id: number;
  display_name?: string;
  contact_phone?: string | null;
  payment_identifier?: string | null;
  email?: string | null;
  is_active?: boolean;
  total_charges?: number;
  total_matches?: number;
  balance_due?: number;
  last_payment_at?: string | null;
  last_payment_amount?: number | null;
  last_payment_currency?: string | null;
  last_payment_title?: string | null;
  last_payment_reference?: string | null;
  matched_payment_count?: number;
};

export type BillingPayerRecord = {
  billing_payer_id: number;
  display_name?: string;
  contact_phone?: string | null;
  payment_identifier?: string | null;
  email?: string | null;
  has_large_family_card?: boolean;
  notes?: string | null;
  is_active?: boolean;
  billing_total_charges?: number;
  billing_total_matches?: number;
  billing_balance_due?: number;
  billing_last_payment_at?: string | null;
  billing_last_payment_amount?: number | null;
  billing_last_payment_currency?: string | null;
  billing_last_payment_title?: string | null;
  billing_matched_payment_count?: number;
  latest_payment_date?: string | null;
  latest_payment_amount?: number | null;
  latest_payment_currency?: string | null;
  latest_payment_title?: string | null;
};

export type BillingStudentRecord = {
  billing_student_id: number;
  organization_id?: number;
  billing_payer_id: number;
  billing_school_id?: number | null;
  billing_model_id?: number | null;
  full_name?: string | null;
  lesson_day?: string | null;
  family_billing_order?: number;
  group_name?: string | null;
  notes?: string | null;
  is_active?: boolean;
  payer_label?: string | null;
  payer_display_name?: string | null;
  payer_contact_phone?: string | null;
  payer_payment_identifier?: string | null;
  payer_is_active?: boolean;
  school_full_name?: string | null;
  school_short_name?: string | null;
  school_city?: string | null;
  model_name?: string | null;
  model_school_year?: string | null;
  model_lesson_day?: string | null;
  model_settlement_mode?: string | null;
  family_last_payment_date?: string | null;
  family_last_payment_amount?: number | null;
  family_last_payment_currency?: string | null;
  family_last_payment_title?: string | null;
  family_balance_due?: number | null;
};

export type BillingChargeRecord = {
  billing_charge_id: number;
  billing_payer_id: number;
  billing_student_id?: number | null;
  period_label?: string | null;
  due_date?: string | null;
  base_amount?: number;
  intro_free_discount_amount?: number;
  sibling_discount_amount?: number;
  large_family_discount_amount?: number;
  total_amount?: number;
  status?: string | null;
  model_name?: string | null;
  student_full_name?: string | null;
  payer_display_name?: string | null;
};

export type BillingPaymentMatchRecord = {
  billing_payment_match_id: number;
  billing_transaction_id: number;
  billing_payer_id: number;
  billing_charge_id?: number | null;
  matched_amount?: number;
  matched_at?: string | null;
  payer_display_name?: string | null;
  transaction_booking_date?: string | null;
  transaction_amount?: number | null;
  transaction_title?: string | null;
  charge_total_amount?: number | null;
};

export type BillingTransactionRecord = {
  billing_transaction_id: number;
  organization_id?: number;
  booking_date?: string | null;
  value_date?: string | null;
  amount?: number;
  currency?: string | null;
  direction?: string | null;
  counterparty_name?: string | null;
  title?: string | null;
  reference?: string | null;
  matched_status?: string | null;
};

export type BillingBalanceViewRow = {
  id: string;
  payerLabel: string;
  contactLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  totalChargesLabel: string;
  totalMatchesLabel: string;
  balanceDueLabel: string;
  lastPaymentLabel: string;
  matchedPaymentCountLabel: string;
};

export type BillingBalanceExplanationRow = {
  id: string;
  payerLabel: string;
  familyTypeLabel: string;
  chargedLabel: string;
  paidLabel: string;
  balanceLabel: string;
  balanceMeaningLabel: string;
  lastPaymentLabel: string;
  topItemsLabel: string;
  explanationLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export type BillingFamilyFoundationRow = {
  id: string;
  href: string;
  familyLabel: string;
  payerLabel: string;
  contactLabel: string;
  studentsLabel: string;
  studentSummaryLabel: string;
  siblingLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  balanceLabel: string;
  lastPaymentLabel: string;
  contextLabel: string;
};

export type BillingCompanyClientRow = {
  id: string;
  href: string;
  companyLabel: string;
  contactLabel: string;
  invoiceCountLabel: string;
  balanceLabel: string;
  contextLabel: string;
  statusLabel: string;
};

export type BillingKpis = {
  payerCount: number;
  activePayerCount: number;
  totalCharges: number;
  totalMatches: number;
  totalBalanceDue: number;
  overdueCount: number;
  paidOrSettledCount: number;
};

export type BillingMoneySummary = {
  receivables: number;
  overpayments: number;
  netBalance: number;
  attentionCount: number;
  activePayerCount: number;
  payerCount: number;
  lastPaymentLabel: string;
  headline: string;
  headlineTone: "ok" | "warning" | "info" | "neutral";
};

export type BillingAttentionItem = {
  id: string;
  title: string;
  reason: string;
  category: "Rozliczenia" | "Faktury" | "Kontrahenci" | "Sprawy";
  tone: "ok" | "warning" | "danger" | "info" | "neutral";
  href: string;
};

export type BillingInvoicePaymentRow = {
  id: string;
  href: string;
  invoiceLabel: string;
  contractorLabel: string;
  statusLabel: string;
  amountLabel: string;
  dateLabel: string;
  reasonLabel: string;
};

export type BillingContractorSettlementRow = {
  id: string;
  href: string;
  contractorLabel: string;
  contactLabel: string;
  balanceLabel: string;
  invoiceCountLabel: string;
  reasonLabel: string;
};

export type BillingRelatedWorkItemRow = {
  id: string;
  href: string;
  titleLabel: string;
  statusLabel: string;
  priorityLabel: string;
  reasonLabel: string;
};

export type BillingRecentPaymentRow = {
  id: string;
  payerLabel: string;
  amountLabel: string;
  dateLabel: string;
  titleLabel: string;
};

export type BillingPayerPersonRow = {
  id: string;
  personLabel: string;
  serviceLabel: string;
  groupLabel: string;
  statusLabel: string;
  contextLabel: string;
};

export type BillingPayerServiceRow = {
  id: string;
  serviceLabel: string;
  serviceTypeLabel: string;
  peopleLabel: string;
  periodsLabel: string;
  statusLabel: string;
  amountLabel: string;
  chargeCountLabel: string;
  sourceLabel: string;
  contextLabel: string;
};

export type BillingServiceEnrollmentRow = {
  id: string;
  href: string;
  serviceLabel: string;
  serviceTypeLabel: string;
  payerLabel: string;
  personLabel: string;
  periodLabel: string;
  statusLabel: string;
  amountLabel: string;
  chargeCountLabel: string;
  sourceLabel: string;
  contextLabel: string;
};

export type BillingPeriodOptionRow = {
  id: string;
  label: string;
  hintLabel: string;
  chargedLabel: string;
  paidLabel: string;
  balanceLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export type BillingPeriodSummary = {
  chargedLabel: string;
  paidLabel: string;
  balanceLabel: string;
  payerCountLabel: string;
  personCountLabel: string;
  serviceCountLabel: string;
  dueCountLabel: string;
  overpaidCountLabel: string;
  settledCountLabel: string;
  sourceLabel: string;
};

export type BillingPeriodPayerRow = {
  id: string;
  href: string;
  payerLabel: string;
  peopleLabel: string;
  servicesLabel: string;
  chargedLabel: string;
  paidLabel: string;
  balanceLabel: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export type BillingPeriodServiceRow = {
  id: string;
  serviceLabel: string;
  serviceTypeLabel: string;
  payerCountLabel: string;
  personCountLabel: string;
  chargedLabel: string;
  sourceLabel: string;
};

export type BillingPeriodAttentionRow = {
  id: string;
  titleLabel: string;
  reasonLabel: string;
  tone: "ok" | "warning" | "danger" | "info" | "neutral";
  href: string;
};

export type BillingPeriodView = {
  selectedPeriodId: string;
  selectedPeriodLabel: string;
  selectedPeriodHint: string;
  options: BillingPeriodOptionRow[];
  summary: BillingPeriodSummary;
  payerRows: BillingPeriodPayerRow[];
  serviceRows: BillingPeriodServiceRow[];
  attentionRows: BillingPeriodAttentionRow[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingPaymentSummary = {
  totalVisibleAmountLabel: string;
  paymentCountLabel: string;
  chargeAssignedCountLabel: string;
  payerOnlyCountLabel: string;
  unexplainedCountLabel: string;
  chargeAssignedAmountLabel: string;
  needsExplanationAmountLabel: string;
};

export type BillingPaymentAssignmentRow = {
  id: string;
  paymentHref?: string;
  dateLabel: string;
  amountLabel: string;
  payerLabel: string;
  payerHref?: string;
  descriptionLabel: string;
  assignmentLabel: string;
  periodLabel: string;
  periodHref?: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  contextLabel: string;
};

export type BillingPaymentsAllocationView = {
  summary: BillingPaymentSummary;
  chargeAssignedRows: BillingPaymentAssignmentRow[];
  payerOnlyRows: BillingPaymentAssignmentRow[];
  unexplainedRows: BillingPaymentAssignmentRow[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingPaymentDetailAssignmentRow = {
  id: string;
  payerLabel: string;
  payerHref?: string;
  personLabel: string;
  serviceLabel: string;
  periodLabel: string;
  periodHref?: string;
  amountLabel: string;
  statusLabel: string;
  contextLabel: string;
};

export type BillingPaymentDetailChargeRow = {
  id: string;
  periodLabel: string;
  personLabel: string;
  serviceLabel: string;
  amountLabel: string;
  statusLabel: string;
};

export type BillingPaymentDetailView = {
  id: string;
  title: string;
  amountLabel: string;
  dateLabel: string;
  descriptionLabel: string;
  payerLabel: string;
  payerHref?: string;
  statusLabel: "Przypisana do naliczenia" | "Przypisana tylko do płatnika" | "Do wyjaśnienia";
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  assignmentSummaryLabel: string;
  assignedAmountLabel: string;
  remainingAmountLabel: string;
  assignmentRows: BillingPaymentDetailAssignmentRow[];
  chargeRows: BillingPaymentDetailChargeRow[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingDebtsSummary = {
  debtTotal: number;
  debtTotalLabel: string;
  debtPayerCount: number;
  overpaymentTotal: number;
  overpaymentTotalLabel: string;
  overpaymentPayerCount: number;
  settledPayerCount: number;
  explanationCount: number;
  payerOnlyPaymentCount: number;
  limitationLabel: string;
};

export type BillingDebtDecisionRow = {
  id: string;
  payerLabel: string;
  payerHref: string;
  amount: number;
  amountLabel: string;
  peopleLabel: string;
  chargesLabel: string;
  periodsLabel: string;
  servicesLabel: string;
  lastPaymentLabel: string;
  payerOnlyPaymentLabel: string;
  latestNoteLabel: string;
  attentionStatusLabel: "Do kontaktu" | "Do sprawdzenia wpłat" | "Do wyjaśnienia z płatnikiem" | "Niska zaległość" | "Brak pilnej akcji";
  attentionTone: "ok" | "warning" | "danger" | "info" | "neutral";
  reasonLabel: string;
  nextStepLabel: string;
  paymentsHref: string;
  periodsHref?: string;
};

export type BillingOverpaymentDecisionRow = {
  id: string;
  payerLabel: string;
  payerHref: string;
  amount: number;
  amountLabel: string;
  peopleLabel: string;
  lastPaymentLabel: string;
  possibleSourceLabel: string;
  statusLabel: string;
  paymentsHref: string;
};

export type BillingExplanationDecisionRow = {
  id: string;
  payerLabel: string;
  payerHref?: string;
  problemLabel: string;
  amountLabel: string;
  reasonLabel: string;
  nextHref: string;
  tone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export type BillingUrgentDecisionRow = {
  id: string;
  payerLabel: string;
  amountLabel: string;
  reasonLabel: string;
  nextStepLabel: string;
  payerHref: string;
  paymentsHref?: string;
  tone: "ok" | "warning" | "danger" | "info" | "neutral";
};

export type BillingDebtsOverpaymentsView = {
  summary: BillingDebtsSummary;
  urgentRows: BillingUrgentDecisionRow[];
  debtRows: BillingDebtDecisionRow[];
  overpaymentRows: BillingOverpaymentDecisionRow[];
  explanationRows: BillingExplanationDecisionRow[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingPayerChargeRow = {
  id: string;
  periodLabel: string;
  personLabel: string;
  serviceLabel: string;
  amountLabel: string;
  statusLabel: string;
};

export type BillingPayerPaymentRow = {
  id: string;
  dateLabel: string;
  amountLabel: string;
  titleLabel: string;
  contextLabel: string;
};

export type BillingPayerNoteRecord = {
  billing_note_id: number;
  organization_id?: number;
  billing_payer_id: number;
  author_user_id?: number;
  author_user_name?: string | null;
  author_user_role?: string | null;
  note_type?: string | null;
  note_text: string;
  created_at?: string | null;
};

export type BillingPayerNoteRow = {
  id: string;
  authorLabel: string;
  dateLabel: string;
  typeLabel: string;
  noteText: string;
};

export type BillingContactChannel = "sms" | "email" | "phone" | "in_person" | "other";

export type BillingContactAction =
  | "draft_prepared"
  | "contact_logged"
  | "no_answer"
  | "promised_payment"
  | "needs_followup";

export type BillingContactEventRecord = {
  billing_contact_event_id: number;
  organization_id?: number;
  billing_payer_id: number;
  payer_display_name?: string | null;
  related_payment_id?: number | null;
  related_issue_key?: string | null;
  channel: BillingContactChannel;
  contact_action: BillingContactAction;
  message_text?: string | null;
  note_text?: string | null;
  created_by_user_id?: number;
  created_by_user_name?: string | null;
  created_by_user_role?: string | null;
  created_at?: string | null;
};

export type BillingContactEventsResponse = {
  organization_id?: number;
  events: BillingContactEventRecord[];
};

export type BillingContactEventRow = {
  id: string;
  channelLabel: string;
  actionLabel: string;
  authorLabel: string;
  dateLabel: string;
  messageText?: string;
  noteText?: string;
  contextLabel: string;
};

export type BillingContactCenterFilters = {
  channel?: BillingContactChannel | "all";
  action?: BillingContactAction | "all";
  payerQuery?: string;
};

export type BillingContactCenterRow = {
  id: string;
  payerLabel: string;
  payerHref: string;
  paymentHref?: string;
  workQueueHref: string;
  channelLabel: string;
  actionLabel: string;
  dateLabel: string;
  messageExcerpt?: string;
  noteExcerpt?: string;
  contextLabel: string;
  attentionReason: string;
  isDraft: boolean;
  isPromisedPayment: boolean;
  isNoAnswer: boolean;
  needsFollowup: boolean;
};

export type BillingContactCenterSummary = {
  totalCount: number;
  draftCount: number;
  promisedPaymentCount: number;
  noAnswerCount: number;
  needsFollowupCount: number;
  recentCount: number;
};

export type BillingContactCenterView = {
  summary: BillingContactCenterSummary;
  allRows: BillingContactCenterRow[];
  filteredRows: BillingContactCenterRow[];
  attentionRows: BillingContactCenterRow[];
  draftRows: BillingContactCenterRow[];
  promisedPaymentRows: BillingContactCenterRow[];
  followupRows: BillingContactCenterRow[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingNextStepTargetType = "payer" | "payment" | "work_queue_issue" | "contact" | "billing_summary";

export type BillingNextStepType =
  | "call"
  | "send_manual_message"
  | "check_payment"
  | "clarify_payment"
  | "review_overpayment"
  | "wait_for_response"
  | "wait_for_payment"
  | "review_notes"
  | "other";

export type BillingNextStepEventAction = "planned" | "completed" | "snoozed";

export type BillingNextStepEventRecord = {
  billing_next_step_event_id: number;
  organization_id?: number;
  target_type: BillingNextStepTargetType;
  target_id?: number | null;
  related_issue_key?: string | null;
  step_type: BillingNextStepType;
  event_action: BillingNextStepEventAction;
  title: string;
  note_text?: string | null;
  planned_for?: string | null;
  created_by_user_id?: number;
  created_by_user_name?: string | null;
  created_by_user_role?: string | null;
  created_at?: string | null;
};

export type BillingNextStepEventsResponse = {
  organization_id?: number;
  events: BillingNextStepEventRecord[];
};

export type BillingNextStepRow = {
  id: string;
  title: string;
  stepTypeLabel: string;
  eventActionLabel: string;
  targetLabel: string;
  targetHref?: string;
  dateLabel: string;
  noteText?: string;
  relatedIssueKey?: string;
};

export type BillingOperationalReportSummary = {
  debtTotalLabel: string;
  debtPayerCount: number;
  overpaymentTotalLabel: string;
  overpaymentPayerCount: number;
  settledPayerCount: number;
  chargeAssignedPaymentCount: number;
  payerOnlyPaymentCount: number;
  unexplainedPaymentCount: number;
  activeIssueCount: number;
  snoozedIssueCount: number;
  handledIssueCount: number;
  contactCount: number;
  contactActionRequiredCount: number;
};

export type BillingOperationalReportCard = {
  id: string;
  label: string;
  value: string;
  description: string;
};

export type BillingOperationalReportImportantItem = {
  id: string;
  typeLabel: string;
  payerLabel: string;
  amountLabel?: string;
  reasonLabel: string;
  nextStepLabel: string;
  href: string;
};

export type BillingOperationalReportView = {
  summary: BillingOperationalReportSummary;
  summaryCards: BillingOperationalReportCard[];
  importantRows: BillingOperationalReportImportantItem[];
  paymentRows: BillingPaymentAssignmentRow[];
  debtRows: BillingDebtDecisionRow[];
  overpaymentRows: BillingOverpaymentDecisionRow[];
  workQueueRows: BillingWorkQueueIssue[];
  contactRows: BillingContactCenterRow[];
  reportText: string;
  limitations: string[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingPayerRelatedInvoiceRow = {
  id: string;
  href: string;
  invoiceLabel: string;
  contractorLabel: string;
  amountLabel: string;
  statusLabel: string;
};

export type BillingPayerDetailView = {
  id: string;
  title: string;
  statusLabel: string;
  statusTone: "ok" | "warning" | "danger" | "info" | "neutral";
  payerTypeLabel: string;
  contactLabel: string;
  paymentIdentifierLabel: string;
  balanceMeaningLabel: string;
  chargedLabel: string;
  paidLabel: string;
  balanceLabel: string;
  lastPaymentLabel: string;
  peopleRows: BillingPayerPersonRow[];
  serviceRows: BillingPayerServiceRow[];
  balanceExplanationRows: BillingBalanceExplanationRow[];
  chargeRows: BillingPayerChargeRow[];
  paymentRows: BillingPayerPaymentRow[];
  noteRows: BillingPayerNoteRow[];
  contactEventRows: BillingContactEventRow[];
  invoiceRows: BillingPayerRelatedInvoiceRow[];
  workItemRows: BillingRelatedWorkItemRow[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingCenterSnapshot = {
  balances: BillingBalanceRecord[];
  payers: BillingPayerRecord[];
  students: BillingStudentRecord[];
  charges: BillingChargeRecord[];
  paymentMatches?: BillingPaymentMatchRecord[];
  transactions?: BillingTransactionRecord[];
  paymentReviewStatuses?: BillingPaymentReviewStatusRecord[];
  workQueueEvents?: BillingWorkQueueEventRecord[];
  contactEvents?: BillingContactEventRecord[];
  nextStepEvents?: BillingNextStepEventRecord[];
  payerNotes?: BillingPayerNoteRecord[];
  invoices: InvoiceRecord[];
  contractors: ContractorRecord[];
  workItems: WorkItemRecord[];
};

export type BillingPayerNoteValidationResult =
  | {
      ok: true;
      payload: {
        note_text: string;
      };
    }
  | {
      ok: false;
      message: string;
    };

export type BillingPayerNoteErrorState = BillingErrorState;

export type BillingPayerNoteSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "blocked";
      message: string;
    }
  | {
      status: "ignored";
    }
  | {
      status: "error";
      errorState: BillingPayerNoteErrorState;
    };

export type BillingPayerNoteSubmitterDeps = {
  refreshDetail: () => Promise<void>;
  setSubmitting: (isSubmitting: boolean) => void;
  submitNote: (payload: { note_text: string }) => Promise<unknown>;
};

export type BillingContactEventValidationResult =
  | {
      ok: true;
      payload: {
        payer_id: number;
        related_payment_id?: number;
        related_issue_key?: string;
        channel: BillingContactChannel;
        contact_action: BillingContactAction;
        message_text?: string;
        note_text?: string;
      };
    }
  | {
      ok: false;
      message: string;
    };

export type BillingContactEventErrorState = BillingErrorState;

export type BillingContactEventSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "blocked";
      message: string;
    }
  | {
      status: "ignored";
    }
  | {
      status: "error";
      errorState: BillingContactEventErrorState;
    };

export type BillingContactEventSubmitterDeps = {
  refreshDetail: () => Promise<void>;
  setSubmitting: (isSubmitting: boolean) => void;
  submitContact: (payload: {
    payer_id: number;
    related_payment_id?: number;
    related_issue_key?: string;
    channel: BillingContactChannel;
    contact_action: BillingContactAction;
    message_text?: string;
    note_text?: string;
  }) => Promise<unknown>;
};

export type BillingNextStepValidationResult =
  | {
      ok: true;
      payload: {
        target_type: BillingNextStepTargetType;
        target_id?: number;
        related_issue_key?: string;
        step_type: BillingNextStepType;
        event_action: BillingNextStepEventAction;
        title: string;
        note_text?: string;
        planned_for?: string;
      };
    }
  | {
      ok: false;
      message: string;
    };

export type BillingNextStepErrorState = BillingErrorState;

export type BillingNextStepSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "blocked";
      message: string;
    }
  | {
      status: "ignored";
    }
  | {
      status: "error";
      errorState: BillingNextStepErrorState;
    };

export type BillingNextStepSubmitterDeps = {
  refreshDetail: () => Promise<void>;
  setSubmitting: (isSubmitting: boolean) => void;
  submitNextStep: (payload: {
    target_type: BillingNextStepTargetType;
    target_id?: number;
    related_issue_key?: string;
    step_type: BillingNextStepType;
    event_action: BillingNextStepEventAction;
    title: string;
    note_text?: string;
    planned_for?: string;
  }) => Promise<unknown>;
};

export type BillingPaymentReviewStatusCode =
  | "needs_review"
  | "checked"
  | "waiting_for_contact"
  | "waiting_for_payment"
  | "do_not_auto_match";

export type BillingPaymentReviewStatusRecord = {
  billing_payment_review_event_id: number;
  organization_id?: number;
  billing_transaction_id: number;
  status: BillingPaymentReviewStatusCode;
  note_text?: string | null;
  created_by_user_id?: number;
  created_by_user_name?: string | null;
  created_by_user_role?: string | null;
  created_at?: string | null;
};

export type BillingPaymentReviewStatusResponse = {
  billing_transaction_id: number;
  organization_id?: number;
  current: BillingPaymentReviewStatusRecord | null;
  history: BillingPaymentReviewStatusRecord[];
};

export type BillingPaymentReviewStatusesResponse = {
  organization_id?: number;
  statuses: BillingPaymentReviewStatusRecord[];
};

export type BillingWorkQueuePriority = "Wysoki" | "Średni" | "Niski";

export type BillingWorkQueueIssueType =
  | "Wpłata do wyjaśnienia"
  | "Czeka na kontakt"
  | "Czeka na wpłatę"
  | "Nie ruszać automatycznie"
  | "Nadpłata do decyzji"
  | "Zaległość do sprawdzenia"
  | "Sprawdzone";

export type BillingWorkQueueIssue = {
  id: string;
  issueKey: string;
  type: BillingWorkQueueIssueType;
  targetType: BillingWorkQueueTargetType;
  targetId?: number;
  priority: BillingWorkQueuePriority;
  tone: "ok" | "warning" | "danger" | "info" | "neutral";
  payerLabel: string;
  payerHref?: string;
  paymentHref?: string;
  amountLabel: string;
  reason: string;
  nextStep: string;
  href: string;
  createdAt?: string | null;
};

export type BillingWorkQueueSummary = {
  highPriorityCount: number;
  needsReviewCount: number;
  contactCount: number;
  overpaymentCount: number;
  debtCount: number;
  checkedCount: number;
  snoozedCount: number;
  handledCount: number;
};

export type BillingWorkQueueView = {
  summary: BillingWorkQueueSummary;
  firstRows: BillingWorkQueueIssue[];
  paymentRows: BillingWorkQueueIssue[];
  contactRows: BillingWorkQueueIssue[];
  overpaymentRows: BillingWorkQueueIssue[];
  checkedRows: BillingWorkQueueIssue[];
  snoozedRows: BillingWorkQueueIssue[];
  handledRows: BillingWorkQueueIssue[];
  contextItems: Array<{ label: string; value: string }>;
};

export type BillingWorkQueueTargetType = "payment" | "payer" | "debts_overpayments" | "billing_summary";
export type BillingWorkQueueEventAction = "handled" | "snoozed";

export type BillingWorkQueueEventRecord = {
  billing_work_queue_event_id: number;
  organization_id?: number;
  issue_key: string;
  issue_type: BillingWorkQueueIssueType;
  target_type: BillingWorkQueueTargetType;
  target_id?: number | null;
  action: BillingWorkQueueEventAction;
  note_text?: string | null;
  created_by_user_id?: number;
  created_by_user_name?: string | null;
  created_by_user_role?: string | null;
  created_at?: string | null;
};

export type BillingWorkQueueEventsResponse = {
  organization_id?: number;
  events: BillingWorkQueueEventRecord[];
};

export type BillingWorkQueueDecisionValidationResult =
  | {
      ok: true;
      payload: {
        issue_key: string;
        issue_type: BillingWorkQueueIssueType;
        target_type: BillingWorkQueueTargetType;
        target_id?: number;
        action: BillingWorkQueueEventAction;
        note_text?: string;
      };
    }
  | {
      ok: false;
      message: string;
    };

export type BillingPaymentReviewStatusValidationResult =
  | {
      ok: true;
      payload: {
        status: BillingPaymentReviewStatusCode;
        note_text?: string;
      };
    }
  | {
      ok: false;
      message: string;
    };

export type BillingPaymentReviewStatusErrorState = BillingErrorState;

export type BillingPaymentReviewStatusSubmitResult =
  | {
      status: "success";
    }
  | {
      status: "blocked";
      message: string;
    }
  | {
      status: "ignored";
    }
  | {
      status: "error";
      errorState: BillingPaymentReviewStatusErrorState;
    };

export type BillingPaymentReviewStatusSubmitterDeps = {
  refreshStatus: () => Promise<void>;
  setSubmitting: (isSubmitting: boolean) => void;
  submitStatus: (payload: { status: BillingPaymentReviewStatusCode; note_text?: string }) => Promise<unknown>;
};

export const BILLING_BALANCES_ENDPOINT = "/billing/ledger/balances";
export const BILLING_PAYMENT_MATCHES_ENDPOINT = "/billing/ledger/matches";
export const BILLING_TRANSACTIONS_ENDPOINT = "/billing/transactions";
export const BILLING_PAYERS_ENDPOINT = "/billing/payers";
export const BILLING_PAYER_NOTE_ENDPOINT_SUFFIX = "/notes";
export const BILLING_STUDENTS_ENDPOINT = "/billing/students";
export const BILLING_CHARGES_ENDPOINT = "/billing/charges";
export const BILLING_READ_ONLY = true;
export const BILLING_PAYER_NOTE_CREATE_ENABLED = true;
export const BILLING_PAYER_NOTE_MAX_LENGTH = 2000;
export const BILLING_PAYER_NOTE_HELP_TEXT =
  "Notatka nie zmienia salda ani przypisań wpłat. Służy tylko do zapisania kontekstu rozmowy lub decyzji.";

export const BILLING_PAYMENT_REVIEW_STATUS_ENDPOINT_SUFFIX = "/review-status";
export const BILLING_PAYMENT_REVIEW_STATUSES_ENDPOINT = "/billing/payment-review-statuses";
export const BILLING_PAYMENT_REVIEW_STATUS_MAX_NOTE_LENGTH = 1000;
export const BILLING_PAYMENT_REVIEW_STATUS_HELP_TEXT =
  "Status operacyjny nie zmienia salda, naliczeń ani przypisania wpłaty. Służy tylko do oznaczenia, co trzeba sprawdzić.";
export const BILLING_PAYMENT_REVIEW_STATUS_OPTIONS: Array<{ value: BillingPaymentReviewStatusCode; label: string }> = [
  { value: "needs_review", label: "Do wyjaśnienia" },
  { value: "checked", label: "Sprawdzone" },
  { value: "waiting_for_contact", label: "Czeka na kontakt" },
  { value: "waiting_for_payment", label: "Czeka na wpłatę" },
  { value: "do_not_auto_match", label: "Nie ruszać automatycznie" },
];
export const BILLING_WORK_QUEUE_EVENTS_ENDPOINT = "/billing/work-queue/events";
export const BILLING_WORK_QUEUE_DECISION_MAX_NOTE_LENGTH = 1000;
export const BILLING_WORK_QUEUE_DECISION_HELP_TEXT =
  "Ta decyzja nie zmienia salda, wpłat ani naliczeń. Służy tylko do uporządkowania pracy nad rozliczeniami.";
export const BILLING_CONTACT_EVENTS_ENDPOINT = "/billing/contact-events";
export const BILLING_CONTACT_MESSAGE_MAX_LENGTH = 2000;
export const BILLING_CONTACT_NOTE_MAX_LENGTH = 1000;
export const BILLING_CONTACT_NO_SEND_HELP_TEXT =
  "CASI Workspace nie wysyła tej wiadomości. Skopiuj treść i wyślij ją samodzielnie wybranym kanałem.";
export const BILLING_CONTACT_EVENT_HELP_TEXT =
  "Kontakt rozliczeniowy zapisuje tylko roboczą treść albo ślad kontaktu. Nie zmienia salda, naliczeń, wpłat ani przypisań.";
export const BILLING_NEXT_STEP_EVENTS_ENDPOINT = "/billing/next-step-events";
export const BILLING_NEXT_STEP_TITLE_MAX_LENGTH = 200;
export const BILLING_NEXT_STEP_NOTE_MAX_LENGTH = 1000;
export const BILLING_NEXT_STEP_HELP_TEXT =
  "Ten krok nie zmienia salda, wpłat ani naliczeń. Nie tworzy automatycznego przypomnienia.";
export const BILLING_NEXT_STEP_TYPE_OPTIONS: Array<{ value: BillingNextStepType; label: string }> = [
  { value: "call", label: "Zadzwonić" },
  { value: "send_manual_message", label: "Napisać ręcznie" },
  { value: "check_payment", label: "Sprawdzić wpłatę" },
  { value: "clarify_payment", label: "Wyjaśnić wpłatę" },
  { value: "review_overpayment", label: "Sprawdzić nadpłatę" },
  { value: "wait_for_response", label: "Poczekać na odpowiedź" },
  { value: "wait_for_payment", label: "Poczekać na wpłatę" },
  { value: "review_notes", label: "Sprawdzić notatki" },
  { value: "other", label: "Inne" },
];
export const BILLING_NEXT_STEP_ACTION_OPTIONS: Array<{ value: BillingNextStepEventAction; label: string }> = [
  { value: "planned", label: "Zaplanowano" },
  { value: "completed", label: "Wykonano" },
  { value: "snoozed", label: "Odłożono" },
];
export const BILLING_CONTACT_CHANNEL_OPTIONS: Array<{ value: BillingContactChannel; label: string }> = [
  { value: "sms", label: "SMS" },
  { value: "email", label: "E-mail" },
  { value: "phone", label: "Telefon" },
  { value: "in_person", label: "Osobiście" },
  { value: "other", label: "Inny kanał" },
];
export const BILLING_CONTACT_ACTION_OPTIONS: Array<{ value: BillingContactAction; label: string }> = [
  { value: "draft_prepared", label: "Przygotowano treść" },
  { value: "contact_logged", label: "Zapisano kontakt" },
  { value: "no_answer", label: "Brak odpowiedzi" },
  { value: "promised_payment", label: "Deklaracja płatności" },
  { value: "needs_followup", label: "Wymaga ponownego kontaktu" },
];
export const BILLING_CONTACT_DRAFT_TEMPLATES = [
  {
    label: "Delikatne przypomnienie",
    value:
      "Dzień dobry, przypominamy o sprawdzeniu rozliczenia. Jeśli wpłata została już wykonana, prosimy o krótkie potwierdzenie.",
  },
  {
    label: "Wyjaśnienie wpłaty",
    value:
      "Dzień dobry, widzimy wpłatę, która wymaga doprecyzowania. Prosimy o informację, którego okresu lub zajęć dotyczy.",
  },
  {
    label: "Potwierdzenie nadpłaty",
    value:
      "Dzień dobry, w rozliczeniu widoczna jest nadpłata. Prosimy o potwierdzenie, czy zostawić ją na kolejny okres.",
  },
];
export const BILLING_CANONICAL_ROUTE = "/rozliczenia";
export const BILLING_LEGACY_ROUTE = "/kasa";
export const BILLING_PAYER_DETAIL_ROUTE = `${BILLING_CANONICAL_ROUTE}/platnicy`;
export const BILLING_PERIODS_ROUTE = `${BILLING_CANONICAL_ROUTE}/okresy`;
export const BILLING_PAYMENTS_ROUTE = `${BILLING_CANONICAL_ROUTE}/wplaty`;
export const BILLING_DEBTS_ROUTE = `${BILLING_CANONICAL_ROUTE}/zaleglosci`;
export const BILLING_WORK_QUEUE_ROUTE = `${BILLING_CANONICAL_ROUTE}/sprawy`;
export const BILLING_CONTACT_CENTER_ROUTE = `${BILLING_CANONICAL_ROUTE}/kontakty`;
export const BILLING_OPERATIONAL_REPORT_ROUTE = `${BILLING_CANONICAL_ROUTE}/raport`;
export const BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć wpłatę";
export const BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Najpierw wskaż organizację w topbarze. Szczegół wpłaty pokazuje tylko dane z wybranej organizacji.";
export const DEFAULT_CURRENCY = "PLN";
export const BILLING_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć rozliczenia";
export const BILLING_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Najpierw wskaż organizację w topbarze. Rozliczenia pokazują dane tylko dla wybranej firmy.";
export const BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE = "Wybierz organizację, aby zobaczyć płatnika";
export const BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_DESCRIPTION =
  "Najpierw wskaż organizację w topbarze. Szczegół płatnika pokazuje tylko dane z wybranej organizacji.";
export const BILLING_FORBIDDEN_WRITE_ACTIONS = [
  "Dodaj płatność",
  "Edytuj płatność",
  "Usuń płatność",
  "Dodaj usługę",
  "Dodaj zapis",
  "Edytuj usługę",
  "Edytuj zapis",
  "Dodaj wpłatę",
  "Dopasuj wpłatę",
  "Zmień przypisanie",
  "Importuj wyciąg",
  "Wygeneruj naliczenia",
  "Zaksięguj",
  "Eksportuj",
];

export function billingPayerDetailPath(payerId: number | string): string {
  return `${BILLING_PAYER_DETAIL_ROUTE}/${payerId}`;
}

export function billingPaymentDetailPath(paymentId: number | string): string {
  return `${BILLING_PAYMENTS_ROUTE}/${paymentId}`;
}

export function billingPaymentReviewStatusEndpoint(paymentId: number | string): string {
  return `/billing/payments/${paymentId}${BILLING_PAYMENT_REVIEW_STATUS_ENDPOINT_SUFFIX}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(value: unknown, fallback = "-"): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function readNumber(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) {
    return Number(value);
  }
  return undefined;
}

function readBoolean(value: unknown): boolean | undefined {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value === 1;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["1", "true", "tak", "yes"].includes(normalized)) {
      return true;
    }
    if (["0", "false", "nie", "no"].includes(normalized)) {
      return false;
    }
  }
  return undefined;
}

function normalizeText(value: unknown): string {
  return typeof value === "string"
    ? value
        .trim()
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
    : "";
}

const UNSAFE_BILLING_TEXT_PATTERNS = [
  /^[a-z]:\\/i,
  /^\\\\/,
  /^\/users\//i,
  /^\/home\//i,
  /\\users\\/i,
  /data[\\/]magazyn/i,
  /storage_key/i,
  /connection\s*string/i,
  /database_url/i,
  /postgres(ql)?:\/\//i,
  /secret/i,
  /token/i,
  /password/i,
  /api[_-]?key/i,
  /^\s*[{[]/,
];

function isUnsafeBillingText(value: string): boolean {
  return UNSAFE_BILLING_TEXT_PATTERNS.some((pattern) => pattern.test(value.trim()));
}

function safeBillingText(value: unknown, fallback = "-"): string {
  const nextValue = readOptionalString(value);
  if (!nextValue || isUnsafeBillingText(nextValue)) {
    return fallback;
  }
  return nextValue;
}

export function formatMoney(value: number | null | undefined, currency = DEFAULT_CURRENCY): string {
  const amount = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return `${amount.toLocaleString("pl-PL", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

function formatDateLabel(value: string | null | undefined, fallback = "Brak daty"): string {
  if (!value) {
    return fallback;
  }
  const [datePart, timePart] = value.replace("Z", "").split("T");
  return timePart ? `${datePart} ${timePart.slice(0, 5)}` : datePart || value;
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

function getInvoiceId(invoice: InvoiceRecord): number | null {
  return readNumber(invoice.invoice_id) ?? readNumber(invoice.id) ?? null;
}

function getContractorId(contractor: ContractorRecord | InvoiceRecord): number | null {
  return readNumber("contractor_id" in contractor ? contractor.contractor_id : contractor.contractor_id) ?? null;
}

function getInvoiceAmount(invoice: InvoiceRecord): number {
  return readNumber(invoice.gross_amount) ?? 0;
}

function getInvoiceLabel(invoice: InvoiceRecord): string {
  const invoiceId = getInvoiceId(invoice);
  return readString(invoice.invoice_number || invoice.ksef_number, invoiceId ? `Faktura #${invoiceId}` : "Faktura");
}

function getInvoiceContractorLabel(invoice: InvoiceRecord): string {
  return readString(invoice.contractor_name || invoice.issuer_name, "Kontrahent nieznany");
}

function getContractorLabel(contractor: ContractorRecord): string {
  return readString(contractor.name, `Kontrahent #${contractor.contractor_id}`);
}

function getBalancePayerLabel(balance: BillingBalanceRecord): string {
  return readString(balance.display_name, `Płatnik #${balance.billing_payer_id}`);
}

function findBalanceForContractor(contractor: ContractorRecord, balances: BillingBalanceRecord[]): BillingBalanceRecord | undefined {
  const contractorName = normalizeText(contractor.name);
  if (!contractorName) {
    return undefined;
  }
  return balances.find((balance) => normalizeText(balance.display_name) === contractorName);
}

function isInvoiceAttentionCandidate(invoice: InvoiceRecord): boolean {
  const status = normalizeText(invoice.status);
  const workflow = normalizeText(invoice.workflow_state);
  const duplicate = normalizeText(invoice.duplicate_type);
  return (
    status.includes("weryfik") ||
    workflow.includes("pracy") ||
    workflow.includes("gotowa") ||
    duplicate.includes("podejrzenie") ||
    duplicate.includes("pewn") ||
    Boolean(invoice.flag_reason)
  );
}

function invoiceReason(invoice: InvoiceRecord): string {
  if (invoice.flag_reason) {
    return readString(invoice.flag_reason);
  }
  if (normalizeText(invoice.duplicate_type).includes("podejrzenie")) {
    return "Wymaga sprawdzenia ryzyka duplikatu.";
  }
  if (normalizeText(invoice.status).includes("weryfik")) {
    return "Czeka na weryfikację przed dalszym obiegiem.";
  }
  return "Warto sprawdzić ją przy przeglądzie rozliczeń.";
}

function isBillingRelatedWorkItem(item: WorkItemRecord, invoices: InvoiceRecord[], contractors: ContractorRecord[]): boolean {
  const metadata = isRecord(item.metadata) ? item.metadata : {};
  const invoiceIds = new Set(invoices.map(getInvoiceId).filter((id): id is number => typeof id === "number"));
  const contractorIds = new Set(contractors.map((contractor) => contractor.contractor_id));
  const metadataInvoiceId = readNumber(metadata.invoice_id ?? metadata.linked_invoice_id ?? metadata.invoiceId);
  const metadataContractorId = readNumber(metadata.contractor_id ?? metadata.contractorId);
  if (metadataInvoiceId && invoiceIds.has(metadataInvoiceId)) {
    return true;
  }
  if (metadataContractorId && contractorIds.has(metadataContractorId)) {
    return true;
  }

  const haystack = normalizeText(`${item.title ?? ""} ${item.description ?? ""} ${item.source_type ?? ""}`);
  return ["faktur", "platn", "rozlicz", "saldo", "koszt", "kontrah"].some((keyword) => haystack.includes(keyword));
}

export function readBillingBalances(payload: unknown): BillingBalanceRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_BALANCES_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_BALANCES_ENDPOINT, payload);
    }

    const payerId = readNumber(item.billing_payer_id);
    if (!payerId) {
      throw new ApiContractError(BILLING_BALANCES_ENDPOINT, payload);
    }

    return {
      billing_payer_id: payerId,
      display_name: readOptionalString(item.display_name),
      contact_phone: readOptionalString(item.contact_phone) ?? null,
      payment_identifier: readOptionalString(item.payment_identifier) ?? null,
      email: readOptionalString(item.email) ?? null,
      is_active: readBoolean(item.is_active),
      total_charges: readNumber(item.total_charges) ?? 0,
      total_matches: readNumber(item.total_matches) ?? 0,
      balance_due: readNumber(item.balance_due) ?? 0,
      last_payment_at: readOptionalString(item.last_payment_at) ?? null,
      last_payment_amount: readNumber(item.last_payment_amount) ?? null,
      last_payment_currency: readOptionalString(item.last_payment_currency) ?? null,
      last_payment_title: readOptionalString(item.last_payment_title) ?? null,
      last_payment_reference: readOptionalString(item.last_payment_reference) ?? null,
      matched_payment_count: readNumber(item.matched_payment_count) ?? 0,
    };
  });
}

export function readBillingPayers(payload: unknown): BillingPayerRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_PAYERS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_PAYERS_ENDPOINT, payload);
    }

    const payerId = readNumber(item.billing_payer_id);
    if (!payerId) {
      throw new ApiContractError(BILLING_PAYERS_ENDPOINT, payload);
    }

    return {
      billing_payer_id: payerId,
      display_name: readOptionalString(item.display_name),
      contact_phone: readOptionalString(item.contact_phone) ?? null,
      payment_identifier: readOptionalString(item.payment_identifier) ?? null,
      email: readOptionalString(item.email) ?? null,
      has_large_family_card: readBoolean(item.has_large_family_card),
      notes: readOptionalString(item.notes) ?? null,
      is_active: readBoolean(item.is_active),
      billing_total_charges: readNumber(item.billing_total_charges) ?? 0,
      billing_total_matches: readNumber(item.billing_total_matches) ?? 0,
      billing_balance_due: readNumber(item.billing_balance_due) ?? 0,
      billing_last_payment_at: readOptionalString(item.billing_last_payment_at) ?? null,
      billing_last_payment_amount: readNumber(item.billing_last_payment_amount) ?? null,
      billing_last_payment_currency: readOptionalString(item.billing_last_payment_currency) ?? null,
      billing_last_payment_title: readOptionalString(item.billing_last_payment_title) ?? null,
      billing_matched_payment_count: readNumber(item.billing_matched_payment_count) ?? 0,
      latest_payment_date: readOptionalString(item.latest_payment_date) ?? null,
      latest_payment_amount: readNumber(item.latest_payment_amount) ?? null,
      latest_payment_currency: readOptionalString(item.latest_payment_currency) ?? null,
      latest_payment_title: readOptionalString(item.latest_payment_title) ?? null,
    };
  });
}

export function billingPayerNoteEndpoint(payerId: number | string): string {
  return `${BILLING_PAYERS_ENDPOINT}/${payerId}${BILLING_PAYER_NOTE_ENDPOINT_SUFFIX}`;
}

export function readBillingPayerNotes(payload: unknown): BillingPayerNoteRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(`${BILLING_PAYERS_ENDPOINT}/{id}${BILLING_PAYER_NOTE_ENDPOINT_SUFFIX}`, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(`${BILLING_PAYERS_ENDPOINT}/{id}${BILLING_PAYER_NOTE_ENDPOINT_SUFFIX}`, payload);
    }

    const noteId = readNumber(item.billing_note_id);
    const payerId = readNumber(item.billing_payer_id);
    if (!noteId || !payerId) {
      throw new ApiContractError(`${BILLING_PAYERS_ENDPOINT}/{id}${BILLING_PAYER_NOTE_ENDPOINT_SUFFIX}`, payload);
    }

    return {
      billing_note_id: noteId,
      organization_id: readNumber(item.organization_id),
      billing_payer_id: payerId,
      author_user_id: readNumber(item.author_user_id),
      author_user_name: safeBillingText(item.author_user_name, "") || null,
      author_user_role: safeBillingText(item.author_user_role, "") || null,
      note_type: safeBillingText(item.note_type, "") || null,
      note_text: safeBillingText(item.note_text, "Ukryto techniczną lub wrażliwą treść notatki."),
      created_at: readOptionalString(item.created_at) ?? null,
    };
  });
}


function isBillingPaymentReviewStatusCode(value: unknown): value is BillingPaymentReviewStatusCode {
  return BILLING_PAYMENT_REVIEW_STATUS_OPTIONS.some((option) => option.value === value);
}

function isBillingWorkQueueAction(value: unknown): value is BillingWorkQueueEventAction {
  return value === "handled" || value === "snoozed";
}

function isBillingContactChannel(value: unknown): value is BillingContactChannel {
  return BILLING_CONTACT_CHANNEL_OPTIONS.some((option) => option.value === value);
}

function isBillingContactAction(value: unknown): value is BillingContactAction {
  return BILLING_CONTACT_ACTION_OPTIONS.some((option) => option.value === value);
}

function isBillingNextStepTargetType(value: unknown): value is BillingNextStepTargetType {
  return value === "payer" || value === "payment" || value === "work_queue_issue" || value === "contact" || value === "billing_summary";
}

function isBillingNextStepType(value: unknown): value is BillingNextStepType {
  return BILLING_NEXT_STEP_TYPE_OPTIONS.some((option) => option.value === value);
}

function isBillingNextStepEventAction(value: unknown): value is BillingNextStepEventAction {
  return BILLING_NEXT_STEP_ACTION_OPTIONS.some((option) => option.value === value);
}

function readBillingContactEventRecord(payload: unknown): BillingContactEventRecord {
  if (!isRecord(payload)) {
    throw new ApiContractError(BILLING_CONTACT_EVENTS_ENDPOINT, payload);
  }
  const eventId = readNumber(payload.billing_contact_event_id);
  const payerId = readNumber(payload.billing_payer_id);
  const channel = readOptionalString(payload.channel);
  const action = readOptionalString(payload.contact_action);
  if (!eventId || !payerId || !isBillingContactChannel(channel) || !isBillingContactAction(action)) {
    throw new ApiContractError(BILLING_CONTACT_EVENTS_ENDPOINT, payload);
  }
  return {
    billing_contact_event_id: eventId,
    organization_id: readNumber(payload.organization_id),
    billing_payer_id: payerId,
    payer_display_name: safeBillingText(payload.payer_display_name, "") || null,
    related_payment_id: readNumber(payload.related_payment_id) ?? null,
    related_issue_key: safeBillingText(payload.related_issue_key, "") || null,
    channel,
    contact_action: action,
    message_text:
      readOptionalString(payload.message_text) === undefined
        ? null
        : safeBillingText(payload.message_text, "Ukryto techniczną lub wrażliwą treść wiadomości."),
    note_text:
      readOptionalString(payload.note_text) === undefined
        ? null
        : safeBillingText(payload.note_text, "Ukryto techniczną lub wrażliwą treść notatki."),
    created_by_user_id: readNumber(payload.created_by_user_id),
    created_by_user_name: safeBillingText(payload.created_by_user_name, "") || null,
    created_by_user_role: safeBillingText(payload.created_by_user_role, "") || null,
    created_at: readOptionalString(payload.created_at) ?? null,
  };
}

export function readBillingContactEvents(payload: unknown): BillingContactEventsResponse {
  if (!isRecord(payload) || !Array.isArray(payload.events)) {
    throw new ApiContractError(BILLING_CONTACT_EVENTS_ENDPOINT, payload);
  }
  return {
    organization_id: payload.organization_id === undefined || payload.organization_id === null ? undefined : readNumber(payload.organization_id),
    events: payload.events.map(readBillingContactEventRecord),
  };
}

function readBillingNextStepEventRecord(payload: unknown): BillingNextStepEventRecord {
  if (!isRecord(payload)) {
    throw new ApiContractError(BILLING_NEXT_STEP_EVENTS_ENDPOINT, payload);
  }
  const eventId = readNumber(payload.billing_next_step_event_id);
  const targetType = readOptionalString(payload.target_type);
  const stepType = readOptionalString(payload.step_type);
  const eventAction = readOptionalString(payload.event_action);
  const title = safeBillingText(payload.title, "");
  if (
    !eventId ||
    !isBillingNextStepTargetType(targetType) ||
    !isBillingNextStepType(stepType) ||
    !isBillingNextStepEventAction(eventAction) ||
    !title
  ) {
    throw new ApiContractError(BILLING_NEXT_STEP_EVENTS_ENDPOINT, payload);
  }
  return {
    billing_next_step_event_id: eventId,
    organization_id: readNumber(payload.organization_id),
    target_type: targetType,
    target_id: readNumber(payload.target_id) ?? null,
    related_issue_key: safeBillingText(payload.related_issue_key, "") || null,
    step_type: stepType,
    event_action: eventAction,
    title,
    note_text:
      payload.note_text === null || payload.note_text === undefined
        ? null
        : safeBillingText(payload.note_text, "Ukryto techniczną lub wrażliwą treść notatki."),
    planned_for: readOptionalString(payload.planned_for) ?? null,
    created_by_user_id: readNumber(payload.created_by_user_id),
    created_by_user_name: safeBillingText(payload.created_by_user_name, "") || null,
    created_by_user_role: safeBillingText(payload.created_by_user_role, "") || null,
    created_at: readOptionalString(payload.created_at) ?? null,
  };
}

export function readBillingNextStepEvents(payload: unknown): BillingNextStepEventsResponse {
  if (!isRecord(payload) || !Array.isArray(payload.events)) {
    throw new ApiContractError(BILLING_NEXT_STEP_EVENTS_ENDPOINT, payload);
  }
  return {
    organization_id: payload.organization_id === undefined || payload.organization_id === null ? undefined : readNumber(payload.organization_id),
    events: payload.events.map(readBillingNextStepEventRecord),
  };
}

function isBillingWorkQueueTargetType(value: unknown): value is BillingWorkQueueTargetType {
  return value === "payment" || value === "payer" || value === "debts_overpayments" || value === "billing_summary";
}

function isBillingWorkQueueIssueType(value: unknown): value is BillingWorkQueueIssueType {
  return (
    value === "Wpłata do wyjaśnienia" ||
    value === "Czeka na kontakt" ||
    value === "Czeka na wpłatę" ||
    value === "Nie ruszać automatycznie" ||
    value === "Nadpłata do decyzji" ||
    value === "Zaległość do sprawdzenia" ||
    value === "Sprawdzone"
  );
}

function readBillingPaymentReviewStatusRecord(payload: unknown, endpoint: string): BillingPaymentReviewStatusRecord {
  if (!isRecord(payload)) {
    throw new ApiContractError(endpoint, payload);
  }
  const eventId = readNumber(payload.billing_payment_review_event_id);
  const transactionId = readNumber(payload.billing_transaction_id);
  const status = readOptionalString(payload.status);
  if (!eventId || !transactionId || !isBillingPaymentReviewStatusCode(status)) {
    throw new ApiContractError(endpoint, payload);
  }
  return {
    billing_payment_review_event_id: eventId,
    organization_id: readNumber(payload.organization_id),
    billing_transaction_id: transactionId,
    status,
    note_text: payload.note_text === null || payload.note_text === undefined
      ? null
      : safeBillingText(payload.note_text, "Ukryto techniczna lub wrazliwa tresc notatki."),
    created_by_user_id: readNumber(payload.created_by_user_id),
    created_by_user_name: safeBillingText(payload.created_by_user_name, "") || null,
    created_by_user_role: safeBillingText(payload.created_by_user_role, "") || null,
    created_at: readOptionalString(payload.created_at) ?? null,
  };
}

export function readBillingPaymentReviewStatus(payload: unknown, paymentId: number | string = "{id}"): BillingPaymentReviewStatusResponse {
  const endpoint = billingPaymentReviewStatusEndpoint(paymentId);
  if (!isRecord(payload)) {
    throw new ApiContractError(endpoint, payload);
  }
  const transactionId = readNumber(payload.billing_transaction_id);
  if (!transactionId) {
    throw new ApiContractError(endpoint, payload);
  }
  if (!Array.isArray(payload.history)) {
    throw new ApiContractError(endpoint, payload);
  }
  const history = payload.history.map((item) => readBillingPaymentReviewStatusRecord(item, endpoint));
  const current = payload.current === null || payload.current === undefined
    ? null
    : readBillingPaymentReviewStatusRecord(payload.current, endpoint);
  return {
    billing_transaction_id: transactionId,
    organization_id: readNumber(payload.organization_id),
    current,
    history,
  };
}

export function readBillingPaymentReviewStatuses(payload: unknown): BillingPaymentReviewStatusesResponse {
  const endpoint = BILLING_PAYMENT_REVIEW_STATUSES_ENDPOINT;
  if (!isRecord(payload) || !Array.isArray(payload.statuses)) {
    throw new ApiContractError(endpoint, payload);
  }

  return {
    organization_id: payload.organization_id === undefined || payload.organization_id === null ? undefined : readNumber(payload.organization_id),
    statuses: payload.statuses.map((item) => readBillingPaymentReviewStatusRecord(item, endpoint)),
  };
}

function readBillingWorkQueueEventRecord(payload: unknown): BillingWorkQueueEventRecord {
  const endpoint = BILLING_WORK_QUEUE_EVENTS_ENDPOINT;
  if (!isRecord(payload)) {
    throw new ApiContractError(endpoint, payload);
  }
  const eventId = readNumber(payload.billing_work_queue_event_id);
  const issueKey = readOptionalString(payload.issue_key);
  const issueType = readOptionalString(payload.issue_type);
  const targetType = readOptionalString(payload.target_type);
  const action = readOptionalString(payload.action);
  if (
    !eventId ||
    !issueKey ||
    !isBillingWorkQueueIssueType(issueType) ||
    !isBillingWorkQueueTargetType(targetType) ||
    !isBillingWorkQueueAction(action)
  ) {
    throw new ApiContractError(endpoint, payload);
  }
  return {
    billing_work_queue_event_id: eventId,
    organization_id: readNumber(payload.organization_id),
    issue_key: issueKey,
    issue_type: issueType,
    target_type: targetType,
    target_id: readNumber(payload.target_id) ?? null,
    action,
    note_text: payload.note_text === null || payload.note_text === undefined
      ? null
      : safeBillingText(payload.note_text, "Ukryto techniczna lub wrazliwa tresc notatki."),
    created_by_user_id: readNumber(payload.created_by_user_id),
    created_by_user_name: safeBillingText(payload.created_by_user_name, "") || null,
    created_by_user_role: safeBillingText(payload.created_by_user_role, "") || null,
    created_at: readOptionalString(payload.created_at) ?? null,
  };
}

export function readBillingWorkQueueEvents(payload: unknown): BillingWorkQueueEventsResponse {
  const endpoint = BILLING_WORK_QUEUE_EVENTS_ENDPOINT;
  if (!isRecord(payload) || !Array.isArray(payload.events)) {
    throw new ApiContractError(endpoint, payload);
  }
  return {
    organization_id: payload.organization_id === undefined || payload.organization_id === null ? undefined : readNumber(payload.organization_id),
    events: payload.events.map((item) => readBillingWorkQueueEventRecord(item)),
  };
}

export function readBillingStudents(payload: unknown): BillingStudentRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_STUDENTS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_STUDENTS_ENDPOINT, payload);
    }

    const studentId = readNumber(item.billing_student_id);
    const payerId = readNumber(item.billing_payer_id);
    if (!studentId || !payerId) {
      throw new ApiContractError(BILLING_STUDENTS_ENDPOINT, payload);
    }

    return {
      billing_student_id: studentId,
      organization_id: readNumber(item.organization_id),
      billing_payer_id: payerId,
      billing_school_id: readNumber(item.billing_school_id) ?? null,
      billing_model_id: readNumber(item.billing_model_id) ?? null,
      full_name: readOptionalString(item.full_name) ?? null,
      lesson_day: readOptionalString(item.lesson_day) ?? null,
      family_billing_order: readNumber(item.family_billing_order) ?? 1,
      group_name: readOptionalString(item.group_name) ?? null,
      notes: readOptionalString(item.notes) ?? null,
      is_active: readBoolean(item.is_active),
      payer_label: readOptionalString(item.payer_label) ?? null,
      payer_display_name: readOptionalString(item.payer_display_name) ?? null,
      payer_contact_phone: readOptionalString(item.payer_contact_phone) ?? null,
      payer_payment_identifier: readOptionalString(item.payer_payment_identifier) ?? null,
      payer_is_active: readBoolean(item.payer_is_active),
      school_full_name: readOptionalString(item.school_full_name) ?? null,
      school_short_name: readOptionalString(item.school_short_name) ?? null,
      school_city: readOptionalString(item.school_city) ?? null,
      model_name: readOptionalString(item.model_name) ?? null,
      model_school_year: readOptionalString(item.model_school_year) ?? null,
      model_lesson_day: readOptionalString(item.model_lesson_day) ?? null,
      model_settlement_mode: readOptionalString(item.model_settlement_mode) ?? null,
      family_last_payment_date: readOptionalString(item.family_last_payment_date) ?? null,
      family_last_payment_amount: readNumber(item.family_last_payment_amount) ?? null,
      family_last_payment_currency: readOptionalString(item.family_last_payment_currency) ?? null,
      family_last_payment_title: readOptionalString(item.family_last_payment_title) ?? null,
      family_balance_due: readNumber(item.family_balance_due) ?? null,
    };
  });
}

export function readBillingCharges(payload: unknown): BillingChargeRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_CHARGES_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_CHARGES_ENDPOINT, payload);
    }

    const chargeId = readNumber(item.billing_charge_id);
    const payerId = readNumber(item.billing_payer_id);
    if (!chargeId || !payerId) {
      throw new ApiContractError(BILLING_CHARGES_ENDPOINT, payload);
    }

    return {
      billing_charge_id: chargeId,
      billing_payer_id: payerId,
      billing_student_id: readNumber(item.billing_student_id) ?? null,
      period_label: readOptionalString(item.period_label) ?? null,
      due_date: readOptionalString(item.due_date) ?? null,
      base_amount: readNumber(item.base_amount) ?? 0,
      intro_free_discount_amount: readNumber(item.intro_free_discount_amount) ?? 0,
      sibling_discount_amount: readNumber(item.sibling_discount_amount) ?? 0,
      large_family_discount_amount: readNumber(item.large_family_discount_amount) ?? 0,
      total_amount: readNumber(item.total_amount) ?? 0,
      status: readOptionalString(item.status) ?? null,
      model_name: readOptionalString(item.model_name) ?? null,
      student_full_name: readOptionalString(item.student_full_name) ?? null,
      payer_display_name: readOptionalString(item.payer_display_name) ?? null,
    };
  });
}

export function readBillingPaymentMatches(payload: unknown): BillingPaymentMatchRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_PAYMENT_MATCHES_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_PAYMENT_MATCHES_ENDPOINT, payload);
    }

    const matchId = readNumber(item.billing_payment_match_id);
    const transactionId = readNumber(item.billing_transaction_id);
    const payerId = readNumber(item.billing_payer_id);
    if (!matchId || !transactionId || !payerId) {
      throw new ApiContractError(BILLING_PAYMENT_MATCHES_ENDPOINT, payload);
    }

    return {
      billing_payment_match_id: matchId,
      billing_transaction_id: transactionId,
      billing_payer_id: payerId,
      billing_charge_id: readNumber(item.billing_charge_id) ?? null,
      matched_amount: readNumber(item.matched_amount) ?? 0,
      matched_at: readOptionalString(item.matched_at) ?? null,
      payer_display_name: readOptionalString(item.payer_display_name) ?? null,
      transaction_booking_date: readOptionalString(item.transaction_booking_date) ?? null,
      transaction_amount: readNumber(item.transaction_amount) ?? null,
      transaction_title: readOptionalString(item.transaction_title) ?? null,
      charge_total_amount: readNumber(item.charge_total_amount) ?? null,
    };
  });
}

export function readBillingTransactions(payload: unknown): BillingTransactionRecord[] {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(BILLING_TRANSACTIONS_ENDPOINT, payload);
  }

  return payload.map((item) => {
    if (!isRecord(item)) {
      throw new ApiContractError(BILLING_TRANSACTIONS_ENDPOINT, payload);
    }
    const transactionId = readNumber(item.billing_transaction_id);
    if (transactionId === undefined) {
      throw new ApiContractError(BILLING_TRANSACTIONS_ENDPOINT, payload);
    }

    return {
      billing_transaction_id: transactionId,
      organization_id: readNumber(item.organization_id),
      booking_date: readOptionalString(item.booking_date) ?? null,
      value_date: readOptionalString(item.value_date) ?? null,
      amount: readNumber(item.amount) ?? 0,
      currency: readOptionalString(item.currency) ?? DEFAULT_CURRENCY,
      direction: readOptionalString(item.direction) ?? null,
      counterparty_name: readOptionalString(item.counterparty_name) ?? null,
      title: readOptionalString(item.title) ?? null,
      reference: readOptionalString(item.reference) ?? null,
      matched_status: readOptionalString(item.matched_status) ?? null,
    };
  });
}

export function readBillingInvoices(payload: unknown): InvoiceRecord[] {
  return readInvoiceList(payload);
}

export function getBillingErrorState(error: unknown): BillingErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby zobaczyć rozliczenia.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak dostępu do rozliczeń",
        description: "Twoje konto nie ma uprawnień do odczytu danych rozliczeniowych.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Nie udało się pobrać rozliczeń",
        description: "Wystąpił błąd serwera. Spróbuj odświeżyć widok albo wróć do niego później.",
      };
    }
    return {
      status: "error",
      title: `Błąd odczytu (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format rozliczeń",
      description: "Odpowiedź nie pasuje do kontraktu widoku Rozliczenia.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem",
      description: "Nie udało się połączyć z backendem. Sprawdź, czy aplikacja działa lokalnie i spróbuj ponownie.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się pobrać rozliczeń",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd pobierania rozliczeń.",
  };
}

export function billingBalanceTone(item: BillingBalanceRecord): BillingBalanceViewRow["statusTone"] {
  const balanceDue = item.balance_due ?? 0;
  if (balanceDue > 0) {
    return "warning";
  }
  if (balanceDue < 0) {
    return "info";
  }
  if (item.is_active === false) {
    return "neutral";
  }
  return "ok";
}

export function buildBillingBalanceRows(items: BillingBalanceRecord[]): BillingBalanceViewRow[] {
  return items.map((item) => {
    const balanceDue = item.balance_due ?? 0;
    const currency = item.last_payment_currency || DEFAULT_CURRENCY;
    const lastPaymentAmount = item.last_payment_amount ?? 0;

    return {
      id: String(item.billing_payer_id),
      payerLabel: getBalancePayerLabel(item),
      contactLabel: readString(item.contact_phone || item.email || item.payment_identifier, "Brak kontaktu"),
      statusLabel: balanceDue > 0 ? "Do zapłaty" : balanceDue < 0 ? "Nadpłata" : item.is_active === false ? "Nieaktywny" : "Rozliczony",
      statusTone: billingBalanceTone(item),
      totalChargesLabel: formatMoney(item.total_charges, DEFAULT_CURRENCY),
      totalMatchesLabel: formatMoney(item.total_matches, DEFAULT_CURRENCY),
      balanceDueLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
      lastPaymentLabel: item.last_payment_at
        ? `${formatDateLabel(item.last_payment_at)} · ${formatMoney(lastPaymentAmount, currency)}`
        : "Brak wpłat",
      matchedPaymentCountLabel: String(item.matched_payment_count ?? 0),
    };
  });
}

export function buildBillingKpis(items: BillingBalanceRecord[]): BillingKpis {
  return {
    payerCount: items.length,
    activePayerCount: items.filter((item) => item.is_active !== false).length,
    totalCharges: roundMoney(items.reduce((sum, item) => sum + (item.total_charges ?? 0), 0)),
    totalMatches: roundMoney(items.reduce((sum, item) => sum + (item.total_matches ?? 0), 0)),
    totalBalanceDue: roundMoney(items.reduce((sum, item) => sum + (item.balance_due ?? 0), 0)),
    overdueCount: items.filter((item) => (item.balance_due ?? 0) > 0).length,
    paidOrSettledCount: items.filter((item) => (item.balance_due ?? 0) <= 0).length,
  };
}

export function buildBillingMoneySummary(items: BillingBalanceRecord[], attentionCount = 0): BillingMoneySummary {
  const receivables = roundMoney(items.reduce((sum, item) => sum + Math.max(item.balance_due ?? 0, 0), 0));
  const overpayments = roundMoney(Math.abs(items.reduce((sum, item) => sum + Math.min(item.balance_due ?? 0, 0), 0)));
  const netBalance = roundMoney(items.reduce((sum, item) => sum + (item.balance_due ?? 0), 0));
  const latestPayment = items
    .filter((item) => item.last_payment_at)
    .sort((a, b) => String(b.last_payment_at).localeCompare(String(a.last_payment_at)))[0];

  return {
    receivables,
    overpayments,
    netBalance,
    attentionCount,
    activePayerCount: items.filter((item) => item.is_active !== false).length,
    payerCount: items.length,
    lastPaymentLabel: latestPayment?.last_payment_at
      ? `${formatDateLabel(latestPayment.last_payment_at)} · ${getBalancePayerLabel(latestPayment)}`
      : "Brak ostatniej wpłaty",
    headline: receivables > 0 ? "Są należności do kontroli" : overpayments > 0 ? "Są nadpłaty do wyjaśnienia" : "Rozliczenia wyglądają spokojnie",
    headlineTone: receivables > 0 ? "warning" : overpayments > 0 ? "info" : "ok",
  };
}

export function buildBillingAttentionItems(snapshot: BillingCenterSnapshot, limit = 6): BillingAttentionItem[] {
  const balanceItems = snapshot.balances
    .filter((item) => (item.balance_due ?? 0) > 0)
    .sort((a, b) => (b.balance_due ?? 0) - (a.balance_due ?? 0))
    .slice(0, 2)
    .map((item) => ({
      id: `balance-${item.billing_payer_id}`,
      title: `Saldo do wyjaśnienia: ${getBalancePayerLabel(item)}`,
      reason: `Do rozliczenia pozostaje ${formatMoney(item.balance_due, DEFAULT_CURRENCY)}.`,
      category: "Rozliczenia" as const,
      tone: "warning" as const,
      href: billingPayerDetailPath(item.billing_payer_id),
    }));

  const invoiceItems = snapshot.invoices
    .filter(isInvoiceAttentionCandidate)
    .sort((a, b) => getInvoiceAmount(b) - getInvoiceAmount(a))
    .slice(0, 2)
    .map((invoice) => {
      const invoiceId = getInvoiceId(invoice);
      return {
        id: `invoice-${invoiceId ?? getInvoiceLabel(invoice)}`,
        title: getInvoiceLabel(invoice),
        reason: invoiceReason(invoice),
        category: "Faktury" as const,
        tone: normalizeText(invoice.duplicate_type).includes("pewn") ? ("danger" as const) : ("warning" as const),
        href: invoiceId ? `/faktury/${invoiceId}` : "/faktury",
      };
    });

  const workItemItems = snapshot.workItems
    .filter((item) => !item.is_closed && isBillingRelatedWorkItem(item, snapshot.invoices, snapshot.contractors))
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
    .slice(0, 2)
    .map((item) => ({
      id: `work-item-${item.work_item_id}`,
      title: readString(item.title, `Sprawa #${item.work_item_id}`),
      reason: item.is_sla_overdue || item.is_due_overdue ? "Termin wymaga uwagi przy rozliczeniach." : "Sprawa może wpływać na płatność lub fakturę.",
      category: "Sprawy" as const,
      tone: item.is_sla_overdue || item.is_due_overdue ? ("danger" as const) : ("info" as const),
      href: `/work-items/${item.work_item_id}`,
    }));

  const contractorItems = snapshot.contractors
    .filter((contractor) => (contractor.invoice_count ?? 0) > 0 && !contractor.email && !contractor.phone)
    .slice(0, 1)
    .map((contractor) => ({
      id: `contractor-${contractor.contractor_id}`,
      title: getContractorLabel(contractor),
      reason: "Kontrahent ma faktury, ale brakuje kontaktu do szybkiego wyjaśnienia płatności.",
      category: "Kontrahenci" as const,
      tone: "info" as const,
      href: `/crm/${contractor.contractor_id}`,
    }));

  return [...balanceItems, ...invoiceItems, ...workItemItems, ...contractorItems].slice(0, limit);
}

export function buildBillingInvoiceRows(invoices: InvoiceRecord[], limit = 8): BillingInvoicePaymentRow[] {
  return invoices
    .slice()
    .sort((a, b) => {
      const attentionDiff = Number(isInvoiceAttentionCandidate(b)) - Number(isInvoiceAttentionCandidate(a));
      if (attentionDiff) {
        return attentionDiff;
      }
      return String(b.incoming_date || b.issue_date || "").localeCompare(String(a.incoming_date || a.issue_date || ""));
    })
    .slice(0, limit)
    .map((invoice, index) => {
      const invoiceId = getInvoiceId(invoice);
      return {
        id: String(invoiceId ?? index),
        href: invoiceId ? `/faktury/${invoiceId}` : "/faktury",
        invoiceLabel: getInvoiceLabel(invoice),
        contractorLabel: getInvoiceContractorLabel(invoice),
        statusLabel: readString(invoice.status || invoice.workflow_state, "Status nieznany"),
        amountLabel: formatMoney(getInvoiceAmount(invoice), invoice.currency || DEFAULT_CURRENCY),
        dateLabel: formatDateLabel(invoice.incoming_date || invoice.issue_date, "Brak daty"),
        reasonLabel: invoiceReason(invoice),
      };
    });
}

export function buildBillingContractorRows(
  contractors: ContractorRecord[],
  balances: BillingBalanceRecord[],
  limit = 8,
): BillingContractorSettlementRow[] {
  return contractors
    .slice()
    .sort((a, b) => (b.invoice_count ?? 0) - (a.invoice_count ?? 0))
    .slice(0, limit)
    .map((contractor) => {
      const balance = findBalanceForContractor(contractor, balances);
      const balanceDue = balance?.balance_due ?? 0;
      return {
        id: String(contractor.contractor_id),
        href: `/crm/${contractor.contractor_id}`,
        contractorLabel: getContractorLabel(contractor),
        contactLabel: readString(contractor.email || contractor.phone, "Brak kontaktu"),
        balanceLabel: balance ? formatMoney(balanceDue, DEFAULT_CURRENCY) : "Brak salda w rozliczeniach",
        invoiceCountLabel: `${contractor.invoice_count ?? 0}`,
        reasonLabel: balanceDue > 0 ? "Ma saldo do wyjaśnienia." : (contractor.invoice_count ?? 0) > 0 ? "Ma historię faktur w systemie." : "W katalogu kontrahentów.",
      };
    });
}

export function buildBillingFamilyFoundationRows(
  payers: BillingPayerRecord[],
  students: BillingStudentRecord[],
  balances: BillingBalanceRecord[],
  limit = 8,
): BillingFamilyFoundationRow[] {
  const studentsByPayer = new Map<number, BillingStudentRecord[]>();
  students.forEach((student) => {
    const current = studentsByPayer.get(student.billing_payer_id) ?? [];
    current.push(student);
    studentsByPayer.set(student.billing_payer_id, current);
  });

  return payers
    .slice()
    .sort((a, b) => {
      const balanceDiff = Math.abs(b.billing_balance_due ?? 0) - Math.abs(a.billing_balance_due ?? 0);
      if (balanceDiff) {
        return balanceDiff;
      }
      return getBalancePayerLabel({ billing_payer_id: a.billing_payer_id, display_name: a.display_name }).localeCompare(
        getBalancePayerLabel({ billing_payer_id: b.billing_payer_id, display_name: b.display_name }),
        "pl",
      );
    })
    .slice(0, limit)
    .map((payer) => {
      const payerStudents = (studentsByPayer.get(payer.billing_payer_id) ?? [])
        .slice()
        .sort((a, b) => (a.family_billing_order ?? 1) - (b.family_billing_order ?? 1));
      const studentNames = payerStudents.map((student) => readString(student.full_name, "Uczeń bez nazwy"));
      const balance = balances.find((item) => item.billing_payer_id === payer.billing_payer_id);
      const balanceDue = payer.billing_balance_due ?? balance?.balance_due ?? 0;
      const lastPaymentDate = payer.billing_last_payment_at ?? payer.latest_payment_date ?? balance?.last_payment_at;
      const lastPaymentAmount = payer.billing_last_payment_amount ?? payer.latest_payment_amount ?? balance?.last_payment_amount;
      const lastPaymentCurrency = payer.billing_last_payment_currency ?? payer.latest_payment_currency ?? balance?.last_payment_currency ?? DEFAULT_CURRENCY;
      const payerLabel = readString(payer.display_name, `Płatnik #${payer.billing_payer_id}`);
      const studentCount = payerStudents.length;
      const isActive = payer.is_active !== false;

      return {
        id: String(payer.billing_payer_id),
        href: billingPayerDetailPath(payer.billing_payer_id),
        familyLabel: payerLabel,
        payerLabel,
        contactLabel: readString(payer.contact_phone || payer.email || payer.payment_identifier, "Brak kontaktu"),
        studentsLabel: studentNames.length ? studentNames.join(", ") : "Brak uczniów w tym koncie",
        studentSummaryLabel:
          studentCount === 0 ? "Brak przypisanych uczniów" : studentCount === 1 ? "1 uczeń" : `${studentCount} uczniów`,
        siblingLabel: studentCount > 1 ? `Rodzeństwo: ${studentCount} uczniów` : "Bez rodzeństwa w danych rozliczeń",
        statusLabel: isActive ? "Aktywne" : "Nieaktywne",
        statusTone: isActive ? (balanceDue > 0 ? "warning" : "ok") : "neutral",
        balanceLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
        lastPaymentLabel: lastPaymentDate
          ? `${formatDateLabel(lastPaymentDate)} · ${formatMoney(lastPaymentAmount, lastPaymentCurrency)}`
          : "Brak ostatniej wpłaty",
        contextLabel:
          studentCount > 1
            ? "Rodzinne konto rozliczeniowe z kilkorgiem uczniów."
            : studentCount === 1
              ? "Rodzinne konto rozliczeniowe z jednym uczniem."
              : "Płatnik bez przypisanego ucznia w obecnych danych.",
      };
    });
}

export function buildBillingCompanyClientRows(
  contractors: ContractorRecord[],
  balances: BillingBalanceRecord[],
  payers: BillingPayerRecord[],
  limit = 5,
): BillingCompanyClientRow[] {
  const payerNames = new Set(payers.map((payer) => normalizeText(payer.display_name)));

  return contractors
    .filter((contractor) => {
      const contractorName = normalizeText(contractor.name);
      return contractorName && !payerNames.has(contractorName) && !contractorName.startsWith("rodzina");
    })
    .slice()
    .sort((a, b) => (b.invoice_count ?? 0) - (a.invoice_count ?? 0))
    .slice(0, limit)
    .map((contractor) => {
      const balance = findBalanceForContractor(contractor, balances);
      return {
        id: String(contractor.contractor_id),
        href: `/crm/${contractor.contractor_id}`,
        companyLabel: getContractorLabel(contractor),
        contactLabel: readString(contractor.email || contractor.phone, "Brak kontaktu"),
        invoiceCountLabel: `${contractor.invoice_count ?? 0}`,
        balanceLabel: balance ? formatMoney(balance.balance_due, DEFAULT_CURRENCY) : "Brak salda rodzinnego",
        contextLabel:
          (contractor.invoice_count ?? 0) > 0
            ? "Klient firmowy z historią faktur, oddzielony od rodzin i uczniów."
            : "Klient firmowy w CRM, bez rodzinnego konta ucznia.",
        statusLabel: contractor.is_new ? "Nowy kontrahent" : "Kontrahent",
      };
    });
}

export function buildBillingBalanceExplanationRows(
  balances: BillingBalanceRecord[],
  payers: BillingPayerRecord[],
  students: BillingStudentRecord[],
  charges: BillingChargeRecord[],
  limit = 6,
): BillingBalanceExplanationRow[] {
  const studentsByPayer = new Map<number, BillingStudentRecord[]>();
  students.forEach((student) => {
    const current = studentsByPayer.get(student.billing_payer_id) ?? [];
    current.push(student);
    studentsByPayer.set(student.billing_payer_id, current);
  });
  const chargesByPayer = new Map<number, BillingChargeRecord[]>();
  charges.forEach((charge) => {
    const current = chargesByPayer.get(charge.billing_payer_id) ?? [];
    current.push(charge);
    chargesByPayer.set(charge.billing_payer_id, current);
  });
  const payersById = new Map(payers.map((payer) => [payer.billing_payer_id, payer]));

  const balanceRows: BillingBalanceExplanationRow[] = balances.map((balance) => {
    const payer = payersById.get(balance.billing_payer_id);
    const payerStudents = studentsByPayer.get(balance.billing_payer_id) ?? [];
    const payerCharges = (chargesByPayer.get(balance.billing_payer_id) ?? [])
      .slice()
      .sort((a, b) => String(b.due_date ?? "").localeCompare(String(a.due_date ?? "")))
      .slice(0, 3);
    const totalCharges = balance.total_charges ?? payer?.billing_total_charges ?? 0;
    const totalMatches = balance.total_matches ?? payer?.billing_total_matches ?? 0;
    const balanceDue = balance.balance_due ?? payer?.billing_balance_due ?? 0;
    const lastPaymentDate = balance.last_payment_at ?? payer?.billing_last_payment_at ?? payer?.latest_payment_date;
    const lastPaymentAmount = balance.last_payment_amount ?? payer?.billing_last_payment_amount ?? payer?.latest_payment_amount;
    const lastPaymentCurrency = balance.last_payment_currency ?? payer?.billing_last_payment_currency ?? payer?.latest_payment_currency ?? DEFAULT_CURRENCY;
    const studentCount = payerStudents.length;
    const payerLabel = getBalancePayerLabel(balance);
    const topItemsLabel = payerCharges.length
      ? payerCharges
          .map((charge) => {
            const studentLabel = readString(charge.student_full_name, "uczeń");
            const periodLabel = readString(charge.period_label, "okres bez nazwy");
            return `${formatMoney(charge.total_amount, DEFAULT_CURRENCY)} za ${studentLabel}, ${periodLabel}`;
          })
          .join("; ")
      : "Brakuje szczegółowych naliczeń dla tego salda.";

    return {
      id: `balance-explanation-${balance.billing_payer_id}`,
      payerLabel,
      familyTypeLabel:
        studentCount > 1
          ? `Rodzina z rodzeństwem: ${studentCount} uczniów`
          : studentCount === 1
            ? "Rodzina z jednym uczniem"
            : "Płatnik bez przypisanych uczniów",
      chargedLabel: formatMoney(totalCharges, DEFAULT_CURRENCY),
      paidLabel: formatMoney(totalMatches, DEFAULT_CURRENCY),
      balanceLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
      balanceMeaningLabel:
        balanceDue > 0 ? `Do dopłaty pozostaje ${formatMoney(balanceDue, DEFAULT_CURRENCY)}`
        : balanceDue < 0 ? `Nadpłata wynosi ${formatMoney(Math.abs(balanceDue), DEFAULT_CURRENCY)}`
        : "Saldo jest rozliczone",
      lastPaymentLabel: lastPaymentDate
        ? `${formatDateLabel(lastPaymentDate)} · ${formatMoney(lastPaymentAmount, lastPaymentCurrency)}`
        : "Brak ostatniej wpłaty",
      topItemsLabel,
      explanationLabel:
        payerCharges.length > 0
          ? `Saldo wynika z naliczonych kwot pomniejszonych o wplaty widoczne w ledgerze. To wyjasnienie read-only, bez operacji finansowych i bez dopasowywania przelewow.`
          : `Brakuje danych, żeby szczegółowo wyjaśnić saldo. Widoczna jest tylko suma naliczeń, wpłat i różnica.`,
      statusTone: balanceDue > 0 ? "warning" : balanceDue < 0 ? "info" : "ok",
    };
  });

  const payerOnlyRows = payers
    .filter((payer) => !balances.some((balance) => balance.billing_payer_id === payer.billing_payer_id))
    .map((payer) => {
      const payerStudents = studentsByPayer.get(payer.billing_payer_id) ?? [];
      return {
        id: `balance-explanation-payer-${payer.billing_payer_id}`,
        payerLabel: readString(payer.display_name, `Płatnik #${payer.billing_payer_id}`),
        familyTypeLabel:
          payerStudents.length > 1
            ? `Rodzina z rodzeństwem: ${payerStudents.length} uczniów`
            : payerStudents.length === 1
              ? "Rodzina z jednym uczniem"
              : "Płatnik bez przypisanych uczniów",
        chargedLabel: formatMoney(payer.billing_total_charges, DEFAULT_CURRENCY),
        paidLabel: formatMoney(payer.billing_total_matches, DEFAULT_CURRENCY),
        balanceLabel: formatMoney(payer.billing_balance_due, DEFAULT_CURRENCY),
        balanceMeaningLabel: "Brakuje pełnego ledgeru dla szczegółowego wyjaśnienia.",
        lastPaymentLabel: payer.latest_payment_date
          ? `${formatDateLabel(payer.latest_payment_date)} · ${formatMoney(payer.latest_payment_amount, payer.latest_payment_currency ?? DEFAULT_CURRENCY)}`
          : "Brak ostatniej wpłaty",
        topItemsLabel: "Brakuje szczegółowych naliczeń dla tego płatnika.",
        explanationLabel: "Widoczny jest tylko skrót danych płatnika. Pełniejsze wyjaśnienie wymaga danych naliczeń albo ledgeru.",
        statusTone: "neutral" as const,
      };
    });

  return [...balanceRows, ...payerOnlyRows].slice(0, limit);
}

function getPayerLabel(payer: BillingPayerRecord): string {
  return readString(payer.display_name, `Płatnik #${payer.billing_payer_id}`);
}

function getPayerBalanceValues(
  payer: BillingPayerRecord,
  balance: BillingBalanceRecord | undefined,
): {
  totalCharges: number;
  totalMatches: number;
  balanceDue: number;
  lastPaymentDate: string | null | undefined;
  lastPaymentAmount: number | null | undefined;
  lastPaymentCurrency: string | null | undefined;
  lastPaymentTitle: string | null | undefined;
} {
  return {
    totalCharges: balance?.total_charges ?? payer.billing_total_charges ?? 0,
    totalMatches: balance?.total_matches ?? payer.billing_total_matches ?? 0,
    balanceDue: balance?.balance_due ?? payer.billing_balance_due ?? 0,
    lastPaymentDate: balance?.last_payment_at ?? payer.billing_last_payment_at ?? payer.latest_payment_date,
    lastPaymentAmount: balance?.last_payment_amount ?? payer.billing_last_payment_amount ?? payer.latest_payment_amount,
    lastPaymentCurrency: balance?.last_payment_currency ?? payer.billing_last_payment_currency ?? payer.latest_payment_currency ?? DEFAULT_CURRENCY,
    lastPaymentTitle: balance?.last_payment_title ?? payer.billing_last_payment_title ?? payer.latest_payment_title,
  };
}

function getPayerTypeLabel(students: BillingStudentRecord[]): string {
  if (students.length > 1) {
    return `Płatnik rodzinny · rodzeństwo (${students.length} uczniów)`;
  }
  if (students.length === 1) {
    return "Płatnik rodzinny · 1 uczeń";
  }
  return "Płatnik bez przypisanych osób w obecnych danych";
}

function balanceMeaningLabel(balanceDue: number): string {
  if (balanceDue > 0) {
    return `Do dopłaty pozostaje ${formatMoney(balanceDue, DEFAULT_CURRENCY)}`;
  }
  if (balanceDue < 0) {
    return `Nadpłata wynosi ${formatMoney(Math.abs(balanceDue), DEFAULT_CURRENCY)}`;
  }
  return "Saldo jest rozliczone";
}

function buildPayerPersonRows(students: BillingStudentRecord[]): BillingPayerPersonRow[] {
  return students
    .slice()
    .sort((a, b) => (a.family_billing_order ?? 1) - (b.family_billing_order ?? 1))
    .map((student) => ({
      id: String(student.billing_student_id),
      personLabel: readString(student.full_name, "Osoba bez nazwy"),
      serviceLabel: readString(student.model_name || student.school_short_name, "Brak przypisanej usługi"),
      groupLabel: readString(student.group_name || student.lesson_day || student.model_lesson_day, "Brak grupy w danych"),
      statusLabel: student.is_active === false ? "Nieaktywny" : "Aktywny",
      contextLabel: student.family_billing_order && student.family_billing_order > 1 ? "Kolejna osoba w rozliczeniu rodzinnym." : "Osoba objęta tym rozliczeniem.",
    }));
}

function inferServiceTypeLabel(parts: Array<unknown>, fallback = "zajęcia cykliczne"): string {
  const text = normalizeText(parts.filter(Boolean).join(" "));
  if (text.includes("abonament") || text.includes("casi") || text.includes("wdrozen") || text.includes("hosting")) {
    return "usługa firmowa";
  }
  if (text.includes("polkolon") || text.includes("turnus") || text.includes("wakacyj")) {
    return "półkolonie";
  }
  if (text.includes("warsztat") || text.includes("pakiet startowy") || text.includes("startowy")) {
    return "warsztat";
  }
  if (text.includes("indywidual")) {
    return "inne";
  }
  if (text.includes("semestr") || text.includes("miesiecz") || text.includes("poniedzialek") || text.includes("wtorek") || text.includes("sroda") || text.includes("piatek")) {
    return "zajęcia cykliczne";
  }
  return fallback;
}

function serviceStatusLabel(isActive: boolean, chargeStatuses: Set<string>, periods: Set<string>): string {
  if (!isActive) {
    return "Zapis nieaktywny";
  }
  const statuses = Array.from(chargeStatuses).map(normalizeText);
  if (statuses.some((status) => status.includes("open") || status.includes("oczek") || status.includes("now"))) {
    return "Aktywny zapis";
  }
  if (periods.size > 0) {
    return "Widoczny w naliczeniach";
  }
  return "Status wywnioskowany";
}

function summarizePeople(people: Set<string>): string {
  const names = Array.from(people).filter(Boolean);
  if (names.length === 0) {
    return "Klient firmowy bez uczniów";
  }
  if (names.length === 1) {
    return names[0];
  }
  if (names.length === 2) {
    return names.join(", ");
  }
  return `rodzeństwo — ${names.length} osoby objęte rozliczeniem`;
}

function summarizePeriods(periods: Set<string>): string {
  const values = Array.from(periods).filter(Boolean);
  if (values.length === 0) {
    return "Okres wywnioskowany z danych";
  }
  if (values.length <= 3) {
    return values.join(", ");
  }
  return `${values.slice(0, 3).join(", ")} i ${values.length - 3} więcej`;
}

function buildPayerServiceRows(charges: BillingChargeRecord[], students: BillingStudentRecord[]): BillingPayerServiceRow[] {
  const studentsById = new Map(students.map((student) => [student.billing_student_id, student]));
  const groups = new Map<
    string,
    {
      serviceLabel: string;
      serviceTypeLabel: string;
      people: Set<string>;
      periods: Set<string>;
      statuses: Set<string>;
      amount: number;
      chargeCount: number;
      isActive: boolean;
    }
  >();

  charges.forEach((charge) => {
    const student = charge.billing_student_id ? studentsById.get(charge.billing_student_id) : undefined;
    const serviceLabel = readString(charge.model_name || student?.model_name, "Usługa bez nazwy");
    const current =
      groups.get(serviceLabel) ??
      {
        serviceLabel,
        serviceTypeLabel: inferServiceTypeLabel([charge.model_name, charge.period_label, student?.group_name, student?.model_settlement_mode]),
        people: new Set<string>(),
        periods: new Set<string>(),
        statuses: new Set<string>(),
        amount: 0,
        chargeCount: 0,
        isActive: student?.is_active !== false,
      };
    current.people.add(
      charge.billing_student_id ? readString(charge.student_full_name || student?.full_name, "Osoba bez nazwy") : "Klient firmowy bez uczniów",
    );
    current.periods.add(readString(charge.period_label, "Okres bez nazwy"));
    current.statuses.add(readString(charge.status, "status nieznany"));
    current.amount = roundMoney(current.amount + (charge.total_amount ?? 0));
    current.chargeCount += 1;
    if (student?.is_active === false) {
      current.isActive = false;
    }
    groups.set(serviceLabel, current);
  });

  return Array.from(groups.values()).map((group, index) => ({
    id: `service-${index}-${group.serviceLabel}`,
    serviceLabel: group.serviceLabel,
    serviceTypeLabel: group.serviceTypeLabel,
    peopleLabel: summarizePeople(group.people),
    periodsLabel: summarizePeriods(group.periods),
    statusLabel: serviceStatusLabel(group.isActive, group.statuses, group.periods),
    amountLabel: formatMoney(group.amount, DEFAULT_CURRENCY),
    chargeCountLabel: group.chargeCount === 1 ? "1 naliczenie" : `${group.chargeCount} naliczeń`,
    sourceLabel: "Wywnioskowane z naliczeń",
    contextLabel: "Usługa jest odczytana z modelu i naliczeń. To nie jest jeszcze pełny zapis ani cennik.",
  }));
}

export function buildBillingServiceEnrollmentRows(
  snapshot: BillingCenterSnapshot,
  limit = 10,
): BillingServiceEnrollmentRow[] {
  const payersById = new Map(snapshot.payers.map((payer) => [payer.billing_payer_id, payer]));
  const studentsById = new Map(snapshot.students.map((student) => [student.billing_student_id, student]));
  const payerNames = new Set(snapshot.payers.map((payer) => normalizeText(payer.display_name)));
  const groups = new Map<
    string,
    {
      payerId: number;
      payerLabel: string;
      serviceLabel: string;
      serviceTypeLabel: string;
      people: Set<string>;
      periods: Set<string>;
      statuses: Set<string>;
      amount: number;
      chargeCount: number;
      isActive: boolean;
    }
  >();

  snapshot.charges.forEach((charge) => {
    const payer = payersById.get(charge.billing_payer_id);
    const student = charge.billing_student_id ? studentsById.get(charge.billing_student_id) : undefined;
    const serviceLabel = readString(charge.model_name || student?.model_name, "Usługa bez nazwy");
    const payerLabel = payer ? getPayerLabel(payer) : readString(charge.payer_display_name, `Płatnik #${charge.billing_payer_id}`);
    const key = `payer-${charge.billing_payer_id}-${serviceLabel}`;
    const current =
      groups.get(key) ??
      {
        payerId: charge.billing_payer_id,
        payerLabel,
        serviceLabel,
        serviceTypeLabel: inferServiceTypeLabel([charge.model_name, charge.period_label, student?.group_name, student?.model_settlement_mode]),
        people: new Set<string>(),
        periods: new Set<string>(),
        statuses: new Set<string>(),
        amount: 0,
        chargeCount: 0,
        isActive: payer?.is_active !== false && student?.is_active !== false,
      };
    current.people.add(
      charge.billing_student_id ? readString(charge.student_full_name || student?.full_name, "Osoba bez nazwy") : "Klient firmowy bez uczniów",
    );
    current.periods.add(readString(charge.period_label, "Okres bez nazwy"));
    current.statuses.add(readString(charge.status, "status nieznany"));
    current.amount = roundMoney(current.amount + (charge.total_amount ?? 0));
    current.chargeCount += 1;
    if (payer?.is_active === false || student?.is_active === false) {
      current.isActive = false;
    }
    groups.set(key, current);
  });

  const familyRows = Array.from(groups.values()).map((group) => ({
    id: `billing-service-${group.payerId}-${group.serviceLabel}`,
    href: billingPayerDetailPath(group.payerId),
    serviceLabel: group.serviceLabel,
    serviceTypeLabel: group.serviceTypeLabel,
    payerLabel: group.payerLabel,
    personLabel: summarizePeople(group.people),
    periodLabel: summarizePeriods(group.periods),
    statusLabel: serviceStatusLabel(group.isActive, group.statuses, group.periods),
    amountLabel: formatMoney(group.amount, DEFAULT_CURRENCY),
    chargeCountLabel: group.chargeCount === 1 ? "1 naliczenie" : `${group.chargeCount} naliczeń`,
    sourceLabel: "Wywnioskowane z naliczeń",
    contextLabel: "Usługa widoczna przez obecne naliczenia i model rozliczeniowy.",
  }));

  const companyRows = snapshot.contractors
    .filter((contractor) => {
      const name = normalizeText(contractor.name);
      return name && !payerNames.has(name) && !name.startsWith("rodzina") && (contractor.invoice_count ?? 0) > 0;
    })
    .slice(0, 4)
    .map((contractor) => {
      const contractorInvoices = snapshot.invoices.filter((invoice) => getContractorId(invoice) === contractor.contractor_id);
      const amount = roundMoney(contractorInvoices.reduce((sum, invoice) => sum + getInvoiceAmount(invoice), 0));
      const periods = new Set(contractorInvoices.map((invoice) => formatDateLabel(invoice.incoming_date || invoice.issue_date || invoice.created_at, "Okres z faktury")));
      return {
        id: `billing-service-company-${contractor.contractor_id}`,
        href: `/crm/${contractor.contractor_id}`,
        serviceLabel: normalizeText(contractor.name).includes("casi") ? "Abonament CASI" : "Usługa firmowa",
        serviceTypeLabel: "usługa firmowa",
        payerLabel: getContractorLabel(contractor),
        personLabel: "Klient firmowy bez uczniów",
        periodLabel: summarizePeriods(periods),
        statusLabel: "Widoczna przez faktury",
        amountLabel: amount > 0 ? formatMoney(amount, DEFAULT_CURRENCY) : "Kwota z faktur",
        chargeCountLabel: contractorInvoices.length === 1 ? "1 faktura" : `${contractorInvoices.length || contractor.invoice_count || 0} faktur`,
        sourceLabel: "Wywnioskowane z faktur",
        contextLabel: "Klient firmowy jest pokazany osobno od rodzin i uczniów.",
      };
    });

  return [...familyRows, ...companyRows]
    .sort((a, b) => a.payerLabel.localeCompare(b.payerLabel, "pl") || a.serviceLabel.localeCompare(b.serviceLabel, "pl"))
    .slice(0, limit);
}

type BillingPeriodPayerAggregate = {
  payerId: number;
  payerLabel: string;
  people: Set<string>;
  services: Set<string>;
  charged: number;
  paid: number;
};

type BillingPeriodServiceAggregate = {
  serviceLabel: string;
  serviceTypeLabel: string;
  payers: Set<number>;
  people: Set<string>;
  charged: number;
};

type BillingPeriodAggregate = {
  id: string;
  label: string;
  charges: BillingChargeRecord[];
  charged: number;
  paid: number;
  payers: Map<number, BillingPeriodPayerAggregate>;
  services: Map<string, BillingPeriodServiceAggregate>;
};

function billingPeriodStatus(balance: number): { label: string; tone: BillingPeriodOptionRow["statusTone"] } {
  if (balance > 0) {
    return { label: "Do dopłaty", tone: "warning" };
  }
  if (balance < 0) {
    return { label: "Nadpłata", tone: "info" };
  }
  return { label: "Rozliczone", tone: "ok" };
}

function billingPeriodSortKey(label: string): string {
  const normalized = normalizeText(label);
  const monthOrder = [
    "styczen",
    "luty",
    "marzec",
    "kwiecien",
    "maj",
    "czerwiec",
    "lipiec",
    "sierpien",
    "wrzesien",
    "pazdziernik",
    "listopad",
    "grudzien",
  ];
  const monthIndex = monthOrder.findIndex((month) => normalized.includes(month));
  const yearMatch = normalized.match(/20\d{2}/);
  const year = yearMatch ? yearMatch[0] : "9999";
  if (monthIndex >= 0) {
    return `${year}-${String(monthIndex + 1).padStart(2, "0")}-${label}`;
  }
  if (normalized.includes("zimowy")) {
    return `${year}-01-${label}`;
  }
  if (normalized.includes("letni")) {
    return `${year}-06-${label}`;
  }
  return `${year}-99-${label}`;
}

function getChargePeriodLabel(charge: BillingChargeRecord): string {
  return readString(charge.period_label, "Okres wywnioskowany z naliczeń");
}

function getPeriodPaymentMap(matches: BillingPaymentMatchRecord[]): Map<number, number> {
  const values = new Map<number, number>();
  matches.forEach((match) => {
    if (!match.billing_charge_id) {
      return;
    }
    values.set(match.billing_charge_id, roundMoney((values.get(match.billing_charge_id) ?? 0) + (match.matched_amount ?? 0)));
  });
  return values;
}

function buildBillingPeriodAggregates(snapshot: BillingCenterSnapshot): BillingPeriodAggregate[] {
  const payersById = new Map(snapshot.payers.map((payer) => [payer.billing_payer_id, payer]));
  const studentsById = new Map(snapshot.students.map((student) => [student.billing_student_id, student]));
  const paidByChargeId = getPeriodPaymentMap(snapshot.paymentMatches ?? []);
  const periods = new Map<string, BillingPeriodAggregate>();

  snapshot.charges.forEach((charge) => {
    const label = getChargePeriodLabel(charge);
    const period =
      periods.get(label) ??
      {
        id: `period-${normalizeText(label).replace(/[^a-z0-9]+/g, "-") || "unknown"}`,
        label,
        charges: [],
        charged: 0,
        paid: 0,
        payers: new Map<number, BillingPeriodPayerAggregate>(),
        services: new Map<string, BillingPeriodServiceAggregate>(),
      };
    const charged = charge.total_amount ?? 0;
    const paid = paidByChargeId.get(charge.billing_charge_id) ?? 0;
    const payer = payersById.get(charge.billing_payer_id);
    const student = charge.billing_student_id ? studentsById.get(charge.billing_student_id) : undefined;
    const payerLabel = payer ? getPayerLabel(payer) : readString(charge.payer_display_name, `Płatnik #${charge.billing_payer_id}`);
    const personLabel = charge.billing_student_id
      ? readString(charge.student_full_name || student?.full_name, "Osoba bez nazwy")
      : "Klient firmowy bez uczniów";
    const serviceLabel = readString(charge.model_name || student?.model_name, "Usługa bez nazwy");
    const payerAggregate =
      period.payers.get(charge.billing_payer_id) ??
      {
        payerId: charge.billing_payer_id,
        payerLabel,
        people: new Set<string>(),
        services: new Set<string>(),
        charged: 0,
        paid: 0,
      };
    const serviceAggregate =
      period.services.get(serviceLabel) ??
      {
        serviceLabel,
        serviceTypeLabel: inferServiceTypeLabel([serviceLabel, label, student?.group_name, student?.model_settlement_mode]),
        payers: new Set<number>(),
        people: new Set<string>(),
        charged: 0,
      };

    period.charges.push(charge);
    period.charged = roundMoney(period.charged + charged);
    period.paid = roundMoney(period.paid + paid);
    payerAggregate.people.add(personLabel);
    payerAggregate.services.add(serviceLabel);
    payerAggregate.charged = roundMoney(payerAggregate.charged + charged);
    payerAggregate.paid = roundMoney(payerAggregate.paid + paid);
    serviceAggregate.payers.add(charge.billing_payer_id);
    serviceAggregate.people.add(personLabel);
    serviceAggregate.charged = roundMoney(serviceAggregate.charged + charged);
    period.payers.set(charge.billing_payer_id, payerAggregate);
    period.services.set(serviceLabel, serviceAggregate);
    periods.set(label, period);
  });

  return Array.from(periods.values()).sort((a, b) => billingPeriodSortKey(a.label).localeCompare(billingPeriodSortKey(b.label), "pl"));
}

export function buildBillingPeriodView(snapshot: BillingCenterSnapshot, selectedPeriodId?: string | null): BillingPeriodView | null {
  const periods = buildBillingPeriodAggregates(snapshot);
  if (!periods.length) {
    return null;
  }

  const selectedPeriod = periods.find((period) => period.id === selectedPeriodId) ?? periods[0];
  const periodBalance = roundMoney(selectedPeriod.charged - selectedPeriod.paid);
  const payerRows = Array.from(selectedPeriod.payers.values())
    .map((payer) => {
      const balance = roundMoney(payer.charged - payer.paid);
      const status = billingPeriodStatus(balance);
      return {
        id: String(payer.payerId),
        href: billingPayerDetailPath(payer.payerId),
        payerLabel: payer.payerLabel,
        peopleLabel: summarizePeople(payer.people),
        servicesLabel: summarizePeriods(payer.services),
        chargedLabel: formatMoney(payer.charged, DEFAULT_CURRENCY),
        paidLabel: formatMoney(payer.paid, DEFAULT_CURRENCY),
        balanceLabel: formatMoney(balance, DEFAULT_CURRENCY),
        statusLabel: status.label,
        statusTone: status.tone,
      };
    })
    .sort((a, b) => {
      const aWeight = a.statusLabel === "Do dopłaty" ? 0 : a.statusLabel === "Nadpłata" ? 1 : 2;
      const bWeight = b.statusLabel === "Do dopłaty" ? 0 : b.statusLabel === "Nadpłata" ? 1 : 2;
      if (aWeight !== bWeight) {
        return aWeight - bWeight;
      }
      return a.payerLabel.localeCompare(b.payerLabel, "pl");
    });
  const serviceRows = Array.from(selectedPeriod.services.values())
    .map((service) => ({
      id: service.serviceLabel,
      serviceLabel: service.serviceLabel,
      serviceTypeLabel: service.serviceTypeLabel,
      payerCountLabel: `${service.payers.size}`,
      personCountLabel: `${service.people.size}`,
      chargedLabel: formatMoney(service.charged, DEFAULT_CURRENCY),
      sourceLabel: "Wywnioskowane z naliczeń tego okresu",
    }))
    .sort((a, b) => b.chargedLabel.localeCompare(a.chargedLabel, "pl"));
  const status = billingPeriodStatus(periodBalance);
  const dueRows = payerRows.filter((row) => row.statusLabel === "Do dopłaty");
  const overpaidRows = payerRows.filter((row) => row.statusLabel === "Nadpłata");
  const settledRows = payerRows.filter((row) => row.statusLabel === "Rozliczone");
  const attentionRows: BillingPeriodAttentionRow[] = [
    ...dueRows.slice(0, 3).map((row) => ({
      id: `due-${row.id}`,
      titleLabel: row.payerLabel,
      reasonLabel: `Do dopłaty w tym okresie: ${row.balanceLabel}.`,
      tone: "warning" as const,
      href: row.href,
    })),
    ...payerRows
      .filter((row) => row.paidLabel === formatMoney(0, DEFAULT_CURRENCY) && row.statusLabel === "Do dopłaty")
      .slice(0, 2)
      .map((row) => ({
        id: `no-payment-${row.id}`,
        titleLabel: row.payerLabel,
        reasonLabel: "Brak widocznej wpłaty dopasowanej do naliczeń tego okresu.",
        tone: "danger" as const,
        href: row.href,
      })),
    ...overpaidRows.slice(0, 2).map((row) => ({
      id: `overpaid-${row.id}`,
      titleLabel: row.payerLabel,
      reasonLabel: `Nadpłata w tym okresie: ${row.balanceLabel.replace("-", "")}.`,
      tone: "info" as const,
      href: row.href,
    })),
  ].slice(0, 6);

  return {
    selectedPeriodId: selectedPeriod.id,
    selectedPeriodLabel: selectedPeriod.label,
    selectedPeriodHint: "Okres wywnioskowany z etykiet naliczeń. Ten widok pokazuje tylko wpłaty, które można bezpiecznie powiązać z naliczeniami tego okresu.",
    options: periods.map((period) => {
      const balance = roundMoney(period.charged - period.paid);
      const optionStatus = billingPeriodStatus(balance);
      return {
        id: period.id,
        label: period.label,
        hintLabel: "Wywnioskowany z naliczeń",
        chargedLabel: formatMoney(period.charged, DEFAULT_CURRENCY),
        paidLabel: formatMoney(period.paid, DEFAULT_CURRENCY),
        balanceLabel: formatMoney(balance, DEFAULT_CURRENCY),
        statusLabel: optionStatus.label,
        statusTone: optionStatus.tone,
      };
    }),
    summary: {
      chargedLabel: formatMoney(selectedPeriod.charged, DEFAULT_CURRENCY),
      paidLabel: formatMoney(selectedPeriod.paid, DEFAULT_CURRENCY),
      balanceLabel: formatMoney(periodBalance, DEFAULT_CURRENCY),
      payerCountLabel: String(selectedPeriod.payers.size),
      personCountLabel: String(new Set(selectedPeriod.charges.map((charge) => charge.billing_student_id).filter(Boolean)).size),
      serviceCountLabel: String(selectedPeriod.services.size),
      dueCountLabel: String(dueRows.length),
      overpaidCountLabel: String(overpaidRows.length),
      settledCountLabel: String(settledRows.length),
      sourceLabel: `${status.label}. Kwoty są liczone z naliczeń i dopasowanych wpłat widocznych w obecnych danych.`,
    },
    payerRows,
    serviceRows,
    attentionRows,
    contextItems: [
      {
        label: "Co mówi widok",
        value: "Pokazuje, jak wygląda rozliczenie jednego okresu: komu naliczono, kto zapłacił i gdzie zostaje różnica.",
      },
      {
        label: "Czego nie robi",
        value: "Widok nie dodaje wpłat i nie wykonuje operacji finansowych.",
      },
      {
        label: "Źródło",
        value: "Część wpłat może być widoczna przy płatniku, ale nie jest przypisana do konkretnego okresu. Ten widok pokazuje tylko wpłaty, które można bezpiecznie powiązać z naliczeniami; pełne przypisywanie wpłat do okresów będzie osobnym etapem.",
      },
    ],
  };
}

function isIncomingBillingTransaction(transaction: BillingTransactionRecord): boolean {
  const direction = String(transaction.direction || "").trim().toLowerCase();
  return !direction || direction === "uznanie" || direction === "inflow" || direction === "credit";
}

function getMatchAmount(match: BillingPaymentMatchRecord, transaction?: BillingTransactionRecord): number {
  return roundMoney(match.matched_amount ?? transaction?.amount ?? match.transaction_amount ?? 0);
}

function getTransactionAmount(transaction: BillingTransactionRecord): number {
  return roundMoney(Math.max(transaction.amount ?? 0, 0));
}

function getPaymentDateLabel(match: BillingPaymentMatchRecord, transaction?: BillingTransactionRecord): string {
  return formatDateLabel(match.transaction_booking_date ?? transaction?.booking_date ?? match.matched_at, "Brak daty");
}

function getPaymentDescriptionLabel(match: BillingPaymentMatchRecord, transaction?: BillingTransactionRecord): string {
  return safeBillingText(match.transaction_title ?? transaction?.title ?? transaction?.reference, "Wpłata bez opisu");
}

function getTransactionDescriptionLabel(transaction: BillingTransactionRecord): string {
  return safeBillingText(transaction.title ?? transaction.reference ?? transaction.counterparty_name, "Wpłata bez opisu");
}

function getChargeAssignmentLabel(charge?: BillingChargeRecord): string {
  if (!charge) {
    return "Naliczenie bez szczegółów";
  }
  const service = readString(charge.model_name, "Usługa bez nazwy");
  const person = charge.billing_student_id ? readString(charge.student_full_name, "Osoba bez nazwy") : "Klient firmowy";
  return `${service} · ${person}`;
}

export function buildBillingPaymentsAllocationView(snapshot: BillingCenterSnapshot): BillingPaymentsAllocationView {
  const transactions = (snapshot.transactions ?? []).filter(isIncomingBillingTransaction);
  const matches = snapshot.paymentMatches ?? [];
  const payersById = new Map(snapshot.payers.map((payer) => [payer.billing_payer_id, payer]));
  const chargesById = new Map(snapshot.charges.map((charge) => [charge.billing_charge_id, charge]));
  const transactionsById = new Map(transactions.map((transaction) => [transaction.billing_transaction_id, transaction]));
  const matchedAmountByTransaction = new Map<number, number>();

  matches.forEach((match) => {
    const transaction = transactionsById.get(match.billing_transaction_id);
    const amount = getMatchAmount(match, transaction);
    matchedAmountByTransaction.set(match.billing_transaction_id, roundMoney((matchedAmountByTransaction.get(match.billing_transaction_id) ?? 0) + amount));
  });

  const chargeAssignedRows: BillingPaymentAssignmentRow[] = matches
    .filter((match) => match.billing_charge_id)
    .map((match): BillingPaymentAssignmentRow => {
      const transaction = transactionsById.get(match.billing_transaction_id);
      const charge = match.billing_charge_id ? chargesById.get(match.billing_charge_id) : undefined;
      const payer = payersById.get(match.billing_payer_id);
      return {
        id: `charge-match-${match.billing_payment_match_id}`,
        paymentHref: billingPaymentDetailPath(match.billing_transaction_id),
        dateLabel: getPaymentDateLabel(match, transaction),
        amountLabel: formatMoney(getMatchAmount(match, transaction), transaction?.currency ?? DEFAULT_CURRENCY),
        payerLabel: readString(match.payer_display_name ?? payer?.display_name, "Płatnik bez nazwy"),
        payerHref: billingPayerDetailPath(match.billing_payer_id),
        descriptionLabel: getPaymentDescriptionLabel(match, transaction),
        assignmentLabel: getChargeAssignmentLabel(charge),
        periodLabel: charge ? getChargePeriodLabel(charge) : "Okres z naliczenia",
        periodHref: BILLING_PERIODS_ROUTE,
        statusLabel: "Przypisana do naliczenia",
        statusTone: "ok" as const,
        contextLabel: "Ta wpłata ma relację z naliczeniem, więc można ją bezpiecznie pokazać w okresie.",
      };
    })
    .sort((a, b) => b.dateLabel.localeCompare(a.dateLabel, "pl"));

  const payerOnlyRows: BillingPaymentAssignmentRow[] = matches
    .filter((match) => !match.billing_charge_id)
    .map((match): BillingPaymentAssignmentRow => {
      const transaction = transactionsById.get(match.billing_transaction_id);
      const payer = payersById.get(match.billing_payer_id);
      return {
        id: `payer-match-${match.billing_payment_match_id}`,
        paymentHref: billingPaymentDetailPath(match.billing_transaction_id),
        dateLabel: getPaymentDateLabel(match, transaction),
        amountLabel: formatMoney(getMatchAmount(match, transaction), transaction?.currency ?? DEFAULT_CURRENCY),
        payerLabel: readString(match.payer_display_name ?? payer?.display_name, "Płatnik bez nazwy"),
        payerHref: billingPayerDetailPath(match.billing_payer_id),
        descriptionLabel: getPaymentDescriptionLabel(match, transaction),
        assignmentLabel: "Przypisana tylko do płatnika",
        periodLabel: "Nie przypisano do okresu",
        statusLabel: "Do wyjaśnienia później",
        statusTone: "warning" as const,
        contextLabel: "Wpłata jest widoczna przy płatniku, ale nie jest jeszcze przypisana do konkretnego naliczenia.",
      };
    })
    .sort((a, b) => b.dateLabel.localeCompare(a.dateLabel, "pl"));

  const unexplainedRows: BillingPaymentAssignmentRow[] = transactions
    .map((transaction): BillingPaymentAssignmentRow | null => {
      const matchedAmount = matchedAmountByTransaction.get(transaction.billing_transaction_id) ?? 0;
      const remainingAmount = roundMoney(getTransactionAmount(transaction) - matchedAmount);
      if (remainingAmount <= 0.009) {
        return null;
      }
      return {
        id: `unexplained-${transaction.billing_transaction_id}`,
        paymentHref: billingPaymentDetailPath(transaction.billing_transaction_id),
        dateLabel: formatDateLabel(transaction.booking_date, "Brak daty"),
        amountLabel: formatMoney(remainingAmount, transaction.currency ?? DEFAULT_CURRENCY),
        payerLabel: "Nieustalony płatnik",
        descriptionLabel: readString(transaction.title ?? transaction.reference, "Wpłata bez opisu"),
        assignmentLabel: matchedAmount > 0 ? "Częściowo przypisana" : "Brak jasnego przypisania",
        periodLabel: "Nie przypisano do okresu",
        statusLabel: "Do wyjaśnienia",
        statusTone: "warning" as const,
        contextLabel:
          matchedAmount > 0
            ? "Część wpłaty ma przypisanie, ale pozostała kwota wymaga późniejszego wyjaśnienia."
            : "Brak osobnego przypisania do płatnika albo naliczenia w obecnych danych.",
      };
    })
    .filter((row): row is BillingPaymentAssignmentRow => row !== null)
    .sort((a, b) => b.dateLabel.localeCompare(a.dateLabel, "pl"));

  const totalVisibleAmount = roundMoney(transactions.reduce((sum, transaction) => sum + getTransactionAmount(transaction), 0));
  const chargeAssignedAmount = roundMoney(
    matches
      .filter((match) => match.billing_charge_id)
      .reduce((sum, match) => sum + getMatchAmount(match, transactionsById.get(match.billing_transaction_id)), 0),
  );
  const payerOnlyAmount = roundMoney(
    matches
      .filter((match) => !match.billing_charge_id)
      .reduce((sum, match) => sum + getMatchAmount(match, transactionsById.get(match.billing_transaction_id)), 0),
  );
  const unexplainedAmount = roundMoney(
    transactions.reduce((sum, transaction) => {
      const matchedAmount = matchedAmountByTransaction.get(transaction.billing_transaction_id) ?? 0;
      const remainingAmount = roundMoney(getTransactionAmount(transaction) - matchedAmount);
      return remainingAmount > 0.009 ? sum + remainingAmount : sum;
    }, 0),
  );

  return {
    summary: {
      totalVisibleAmountLabel: formatMoney(totalVisibleAmount, DEFAULT_CURRENCY),
      paymentCountLabel: String(transactions.length),
      chargeAssignedCountLabel: String(chargeAssignedRows.length),
      payerOnlyCountLabel: String(payerOnlyRows.length),
      unexplainedCountLabel: String(unexplainedRows.length),
      chargeAssignedAmountLabel: formatMoney(chargeAssignedAmount, DEFAULT_CURRENCY),
      needsExplanationAmountLabel: formatMoney(roundMoney(payerOnlyAmount + unexplainedAmount), DEFAULT_CURRENCY),
    },
    chargeAssignedRows,
    payerOnlyRows,
    unexplainedRows,
    contextItems: [
      {
        label: "Co mówi widok",
        value: "Pokazuje widoczne wpłaty i to, czy są przypisane do naliczenia, tylko do płatnika albo wymagają późniejszego wyjaśnienia.",
      },
      {
        label: "Czego nie robi",
        value: "Widok nie dodaje wpłat i nie wykonuje operacji finansowych.",
      },
      {
        label: "Okresy",
        value: "Wpłata trafia do okresu tylko wtedy, gdy ma bezpieczną relację z konkretnym naliczeniem. Pełne przypisywanie wpłat do naliczeń będzie osobnym etapem.",
      },
    ],
  };
}

export function buildBillingPaymentDetailView(snapshot: BillingCenterSnapshot, paymentId: number): BillingPaymentDetailView | null {
  const transaction = (snapshot.transactions ?? []).find(
    (item) => item.billing_transaction_id === paymentId && isIncomingBillingTransaction(item),
  );
  if (!transaction) {
    return null;
  }

  const matches = (snapshot.paymentMatches ?? []).filter((match) => match.billing_transaction_id === paymentId);
  const payersById = new Map(snapshot.payers.map((payer) => [payer.billing_payer_id, payer]));
  const chargesById = new Map(snapshot.charges.map((charge) => [charge.billing_charge_id, charge]));
  const studentsById = new Map(snapshot.students.map((student) => [student.billing_student_id, student]));
  const assignedAmount = roundMoney(matches.reduce((sum, match) => sum + getMatchAmount(match, transaction), 0));
  const totalAmount = getTransactionAmount(transaction);
  const remainingAmount = roundMoney(totalAmount - assignedAmount);
  const hasChargeAssignment = matches.some((match) => Boolean(match.billing_charge_id));
  const hasPayerAssignment = matches.length > 0;
  const firstPayerId = matches[0]?.billing_payer_id;
  const firstPayer = firstPayerId ? payersById.get(firstPayerId) : undefined;
  const payerLabel = firstPayerId
    ? readString(matches[0]?.payer_display_name ?? firstPayer?.display_name, "Płatnik bez nazwy")
    : "Nieustalony płatnik";
  const currency = transaction.currency ?? DEFAULT_CURRENCY;

  const assignmentRows: BillingPaymentDetailAssignmentRow[] = matches.length
    ? matches.map((match) => {
        const charge = match.billing_charge_id ? chargesById.get(match.billing_charge_id) : undefined;
        const payer = payersById.get(match.billing_payer_id);
        const student = charge?.billing_student_id ? studentsById.get(charge.billing_student_id) : undefined;
        const isChargeAssigned = Boolean(match.billing_charge_id);
        return {
          id: String(match.billing_payment_match_id),
          payerLabel: readString(match.payer_display_name ?? payer?.display_name, "Płatnik bez nazwy"),
          payerHref: billingPayerDetailPath(match.billing_payer_id),
          personLabel: charge?.billing_student_id
            ? readString(charge.student_full_name ?? student?.full_name, "Osoba bez nazwy")
            : isChargeAssigned
              ? "Klient firmowy"
              : "Nie przypisano do osoby",
          serviceLabel: isChargeAssigned ? readString(charge?.model_name, "Usługa bez nazwy") : "Nie przypisano do usługi",
          periodLabel: isChargeAssigned && charge ? getChargePeriodLabel(charge) : "Nie przypisano do okresu",
          periodHref: isChargeAssigned ? BILLING_PERIODS_ROUTE : undefined,
          amountLabel: formatMoney(getMatchAmount(match, transaction), currency),
          statusLabel: isChargeAssigned ? "Przypisana do naliczenia" : "Przypisana tylko do płatnika",
          contextLabel: isChargeAssigned
            ? "Ta część wpłaty ma bezpieczne powiązanie z naliczeniem i okresem."
            : "Wpłata jest widoczna przy płatniku, ale nie jest jeszcze przypisana do konkretnego naliczenia.",
        };
      })
    : [
        {
          id: `unexplained-${transaction.billing_transaction_id}`,
          payerLabel: "Nieustalony płatnik",
          personLabel: "Nie ustalono",
          serviceLabel: "Nie ustalono",
          periodLabel: "Nie przypisano do okresu",
          amountLabel: formatMoney(totalAmount, currency),
          statusLabel: "Do wyjaśnienia",
          contextLabel: "Ta wpłata wymaga późniejszego wyjaśnienia. Widok nie zgaduje płatnika ani okresu.",
        },
      ];

  const chargeRows: BillingPaymentDetailChargeRow[] = matches
    .map((match) => (match.billing_charge_id ? chargesById.get(match.billing_charge_id) : undefined))
    .filter((charge): charge is BillingChargeRecord => Boolean(charge))
    .map((charge) => ({
      id: String(charge.billing_charge_id),
      periodLabel: getChargePeriodLabel(charge),
      personLabel: charge.billing_student_id ? readString(charge.student_full_name, "Osoba bez nazwy") : "Klient firmowy",
      serviceLabel: readString(charge.model_name, "Usługa bez nazwy"),
      amountLabel: formatMoney(charge.total_amount, currency),
      statusLabel: readString(charge.status, "Status nieznany"),
    }));

  const statusLabel = hasChargeAssignment
    ? "Przypisana do naliczenia"
    : hasPayerAssignment
      ? "Przypisana tylko do płatnika"
      : "Do wyjaśnienia";
  const statusTone = hasChargeAssignment ? "ok" : "warning";
  const assignmentSummaryLabel = hasChargeAssignment
    ? "Wpłata ma powiązanie z konkretnym naliczeniem, więc można pokazać okres i usługę."
    : hasPayerAssignment
      ? "Wpłata jest widoczna przy płatniku, ale nie jest jeszcze przypisana do konkretnego naliczenia."
      : "Ta wpłata wymaga późniejszego wyjaśnienia. Widok nie zgaduje płatnika ani okresu.";

  return {
    id: String(transaction.billing_transaction_id),
    title: "Szczegół wpłaty",
    amountLabel: formatMoney(totalAmount, currency),
    dateLabel: formatDateLabel(transaction.booking_date ?? transaction.value_date, "Brak daty"),
    descriptionLabel: getTransactionDescriptionLabel(transaction),
    payerLabel,
    payerHref: firstPayerId ? billingPayerDetailPath(firstPayerId) : undefined,
    statusLabel,
    statusTone,
    assignmentSummaryLabel,
    assignedAmountLabel: formatMoney(assignedAmount, currency),
    remainingAmountLabel: formatMoney(Math.max(remainingAmount, 0), currency),
    assignmentRows,
    chargeRows,
    contextItems: [
      {
        label: "Co mówi ekran",
        value: "Pokazuje widoczną wpłatę i jej obecne przypisanie w danych rozliczeń.",
      },
      {
        label: "Czego nie robi",
        value: "Nie dopasowuje wplat, nie zmienia salda i nie zmienia przypisania.",
      },
      {
        label: "Zakres",
        value:
          "Okres i naliczenie są pokazywane tylko wtedy, gdy istnieje bezpieczne powiązanie z naliczeniem. Pełne przypisywanie wpłat będzie osobnym etapem.",
      },
    ],
  };
}

function summarizeChargeItems(charges: BillingChargeRecord[], limit = 3): string {
  if (!charges.length) {
    return "Brak szczegółowych naliczeń w danych";
  }
  return charges
    .slice()
    .sort((a, b) => String(b.due_date ?? b.period_label ?? "").localeCompare(String(a.due_date ?? a.period_label ?? "")))
    .slice(0, limit)
    .map((charge) => {
      const person = charge.billing_student_id ? readString(charge.student_full_name, "Osoba bez nazwy") : "Klient firmowy";
      return `${getChargePeriodLabel(charge)} · ${readString(charge.model_name, "Usługa bez nazwy")} · ${person} · ${formatMoney(charge.total_amount, DEFAULT_CURRENCY)}`;
    })
    .join("; ");
}

function summarizeChargePeriods(charges: BillingChargeRecord[]): string {
  const periods = new Set(charges.map((charge) => getChargePeriodLabel(charge)).filter(Boolean));
  return periods.size ? summarizePeriods(periods) : "Brak okresu w danych";
}

function summarizeChargeServices(charges: BillingChargeRecord[]): string {
  const services = new Set(charges.map((charge) => readString(charge.model_name, "")).filter(Boolean));
  return services.size ? summarizePeriods(services) : "Brak usługi w danych";
}

function latestPayerNote(notes: BillingPayerNoteRecord[], payerId: number): string {
  const note = notes
    .filter((item) => item.billing_payer_id === payerId)
    .slice()
    .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")) || b.billing_note_id - a.billing_note_id)[0];
  if (!note) {
    return "Brak notatki rozliczeniowej";
  }
  const text = safeBillingText(note.note_text, "Ukryto techniczną lub wrażliwą treść notatki.");
  return text.length > 120 ? `${text.slice(0, 117)}...` : text;
}

function noteSuggestsExplanation(notes: BillingPayerNoteRecord[], payerId: number): boolean {
  const text = notes
    .filter((item) => item.billing_payer_id === payerId)
    .map((item) => normalizeText(item.note_text))
    .join(" ");
  return ["wyjasn", "sprawd", "kontakt", "saldo", "doplat", "nadplat", "przelew"].some((term) => text.includes(term));
}

function paymentLabelForPayer(values: ReturnType<typeof getPayerBalanceValues>): string {
  if (!values.lastPaymentDate) {
    return "Brak ostatniej wpłaty";
  }
  return `${formatDateLabel(values.lastPaymentDate)} · ${formatMoney(values.lastPaymentAmount, values.lastPaymentCurrency ?? DEFAULT_CURRENCY)}`;
}

function debtAttentionStatus(
  amount: number,
  payerOnlyPayments: number,
  hasLastPayment: boolean,
  hasNoteSignal: boolean,
): Pick<BillingDebtDecisionRow, "attentionStatusLabel" | "attentionTone" | "reasonLabel" | "nextStepLabel"> {
  if (payerOnlyPayments > 0) {
    return {
      attentionStatusLabel: "Do sprawdzenia wpłat",
      attentionTone: "warning",
      reasonLabel: "Zaległość istnieje mimo wpłat widocznych tylko przy płatniku.",
      nextStepLabel: "Sprawdź wpłaty tego płatnika",
    };
  }
  if (amount >= 300 && !hasLastPayment) {
    return {
      attentionStatusLabel: "Do kontaktu",
      attentionTone: "danger",
      reasonLabel: "Wysoka zaległość bez widocznej ostatniej wpłaty.",
      nextStepLabel: "Wejdź w szczegół płatnika",
    };
  }
  if (hasNoteSignal) {
    return {
      attentionStatusLabel: "Do wyjaśnienia z płatnikiem",
      attentionTone: "warning",
      reasonLabel: "Ostatnie notatki rozliczeniowe sugerują wyjaśnienie salda.",
      nextStepLabel: "Wejdź w szczegół płatnika",
    };
  }
  if (amount < 100) {
    return {
      attentionStatusLabel: "Niska zaległość",
      attentionTone: "info",
      reasonLabel: "Kwota zaległości jest niska w obecnych danych.",
      nextStepLabel: "Zweryfikuj naliczenia z okresu",
    };
  }
  return {
    attentionStatusLabel: "Brak pilnej akcji",
    attentionTone: "neutral",
    reasonLabel: "Zaległość jest widoczna, ale dane nie wskazują dodatkowego sygnału pilności.",
    nextStepLabel: "Wejdź w szczegół płatnika",
  };
}

export function buildBillingDebtsOverpaymentsView(snapshot: BillingCenterSnapshot): BillingDebtsOverpaymentsView {
  const balancesByPayerId = new Map(snapshot.balances.map((balance) => [balance.billing_payer_id, balance]));
  const studentsByPayerId = new Map<number, BillingStudentRecord[]>();
  const chargesByPayerId = new Map<number, BillingChargeRecord[]>();
  const matchesByPayerId = new Map<number, BillingPaymentMatchRecord[]>();
  const transactions = (snapshot.transactions ?? []).filter(isIncomingBillingTransaction);
  const transactionById = new Map(transactions.map((transaction) => [transaction.billing_transaction_id, transaction]));
  const matchedAmountByTransaction = new Map<number, number>();
  const payerNotes = snapshot.payerNotes ?? [];

  snapshot.students.forEach((student) => {
    studentsByPayerId.set(student.billing_payer_id, [...(studentsByPayerId.get(student.billing_payer_id) ?? []), student]);
  });
  snapshot.charges.forEach((charge) => {
    chargesByPayerId.set(charge.billing_payer_id, [...(chargesByPayerId.get(charge.billing_payer_id) ?? []), charge]);
  });
  (snapshot.paymentMatches ?? []).forEach((match) => {
    matchesByPayerId.set(match.billing_payer_id, [...(matchesByPayerId.get(match.billing_payer_id) ?? []), match]);
    matchedAmountByTransaction.set(
      match.billing_transaction_id,
      roundMoney((matchedAmountByTransaction.get(match.billing_transaction_id) ?? 0) + getMatchAmount(match, transactionById.get(match.billing_transaction_id))),
    );
  });

  const debtRows: BillingDebtDecisionRow[] = [];
  const overpaymentRows: BillingOverpaymentDecisionRow[] = [];
  const explanationRows: BillingExplanationDecisionRow[] = [];

  const payerIds = new Set<number>([
    ...snapshot.payers.map((payer) => payer.billing_payer_id),
    ...snapshot.balances.map((balance) => balance.billing_payer_id),
  ]);
  const payersById = new Map(snapshot.payers.map((payer) => [payer.billing_payer_id, payer]));

  Array.from(payerIds).forEach((payerId) => {
    const payerBalance = balancesByPayerId.get(payerId);
    const payer =
      payersById.get(payerId) ??
      ({
        billing_payer_id: payerId,
        display_name: payerBalance?.display_name,
        contact_phone: payerBalance?.contact_phone,
        payment_identifier: payerBalance?.payment_identifier,
        email: payerBalance?.email,
        is_active: payerBalance?.is_active,
        billing_total_charges: payerBalance?.total_charges,
        billing_total_matches: payerBalance?.total_matches,
        billing_balance_due: payerBalance?.balance_due,
        billing_last_payment_at: payerBalance?.last_payment_at,
        billing_last_payment_amount: payerBalance?.last_payment_amount,
        billing_last_payment_currency: payerBalance?.last_payment_currency,
        billing_last_payment_title: payerBalance?.last_payment_title,
        billing_matched_payment_count: payerBalance?.matched_payment_count,
      } satisfies BillingPayerRecord);
    const values = getPayerBalanceValues(payer, payerBalance);
    const balanceDue = roundMoney(values.balanceDue);
    const payerStudents = studentsByPayerId.get(payer.billing_payer_id) ?? [];
    const payerCharges = chargesByPayerId.get(payer.billing_payer_id) ?? [];
    const payerMatches = matchesByPayerId.get(payer.billing_payer_id) ?? [];
    const payerOnlyMatches = payerMatches.filter((match) => !match.billing_charge_id);
    const hasChargeMatches = payerMatches.some((match) => Boolean(match.billing_charge_id));
    const peopleLabel = summarizePeople(new Set(payerStudents.map((student) => readString(student.full_name, "")).filter(Boolean)));
    const payerHref = billingPayerDetailPath(payer.billing_payer_id);
    const periodsLabel = summarizeChargePeriods(payerCharges);
    const servicesLabel = summarizeChargeServices(payerCharges);
    const lastPaymentLabel = paymentLabelForPayer(values);
    const latestNoteLabel = latestPayerNote(payerNotes, payer.billing_payer_id);
    const hasNoteSignal = noteSuggestsExplanation(payerNotes, payer.billing_payer_id);

    if (balanceDue > 0) {
      const status = debtAttentionStatus(balanceDue, payerOnlyMatches.length, Boolean(values.lastPaymentDate), hasNoteSignal);
      debtRows.push({
        id: String(payer.billing_payer_id),
        payerLabel: getPayerLabel(payer),
        payerHref,
        amount: balanceDue,
        amountLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
        peopleLabel,
        chargesLabel: summarizeChargeItems(payerCharges),
        periodsLabel,
        servicesLabel,
        lastPaymentLabel,
        payerOnlyPaymentLabel: payerOnlyMatches.length
          ? `${payerOnlyMatches.length} wpłat widocznych tylko przy płatniku`
          : "Brak wpłat wyłącznie przy płatniku",
        latestNoteLabel,
        paymentsHref: BILLING_PAYMENTS_ROUTE,
        periodsHref: payerCharges.length ? BILLING_PERIODS_ROUTE : undefined,
        ...status,
      });
    }

    if (balanceDue < 0) {
      overpaymentRows.push({
        id: String(payer.billing_payer_id),
        payerLabel: getPayerLabel(payer),
        payerHref,
        amount: Math.abs(balanceDue),
        amountLabel: formatMoney(Math.abs(balanceDue), DEFAULT_CURRENCY),
        peopleLabel,
        lastPaymentLabel,
        possibleSourceLabel: payerOnlyMatches.length
          ? "Część wpłat jest widoczna tylko przy płatniku, więc nadpłata wymaga decyzji poza tym widokiem."
          : hasChargeMatches
            ? "Nadpłata wynika z obecnego salda płatnika i widocznych przypisań."
            : "Źródło nadpłaty nie wynika jednoznacznie z obecnych naliczeń.",
        statusLabel: "Nadpłata nie została automatycznie rozliczona ani przeniesiona.",
        paymentsHref: BILLING_PAYMENTS_ROUTE,
      });
    }

    if (balanceDue > 0 && payerOnlyMatches.length) {
      explanationRows.push({
        id: `debt-payer-only-${payer.billing_payer_id}`,
        payerLabel: getPayerLabel(payer),
        payerHref,
        problemLabel: "Wpłaty do sprawdzenia",
        amountLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
        reasonLabel: "Wpłata widoczna przy płatniku, ale bez przypisania do naliczenia.",
        nextHref: BILLING_PAYMENTS_ROUTE,
        tone: "warning",
      });
    }
    if (balanceDue < 0) {
      explanationRows.push({
        id: `overpayment-${payer.billing_payer_id}`,
        payerLabel: getPayerLabel(payer),
        payerHref,
        problemLabel: "Nadpłata wymaga decyzji",
        amountLabel: formatMoney(Math.abs(balanceDue), DEFAULT_CURRENCY),
        reasonLabel: "Nadpłata jest widoczna, ale ten widok jej nie rozlicza ani nie przenosi.",
        nextHref: payerHref,
        tone: "info",
      });
    }
    if (balanceDue >= 300 && !values.lastPaymentDate) {
      explanationRows.push({
        id: `debt-no-payment-${payer.billing_payer_id}`,
        payerLabel: getPayerLabel(payer),
        payerHref,
        problemLabel: "Brak ostatniej wpłaty",
        amountLabel: formatMoney(balanceDue, DEFAULT_CURRENCY),
        reasonLabel: "Brak wpłat przy aktywnych naliczeniach albo wysokiej zaległości.",
        nextHref: payerHref,
        tone: "danger",
      });
    }
    if (payerCharges.length && !payerMatches.length) {
      explanationRows.push({
        id: `charges-no-payment-${payer.billing_payer_id}`,
        payerLabel: getPayerLabel(payer),
        payerHref,
        problemLabel: "Naliczenia bez wpłat",
        amountLabel: formatMoney(Math.max(balanceDue, 0), DEFAULT_CURRENCY),
        reasonLabel: "Są naliczenia, ale brak widocznych wpłat przy tym płatniku.",
        nextHref: payerHref,
        tone: "warning",
      });
    }
    if (hasNoteSignal) {
      explanationRows.push({
        id: `note-signal-${payer.billing_payer_id}`,
        payerLabel: getPayerLabel(payer),
        payerHref,
        problemLabel: "Notatka rozliczeniowa",
        amountLabel: balanceDue === 0 ? "Bez kwoty" : formatMoney(Math.abs(balanceDue), DEFAULT_CURRENCY),
        reasonLabel: latestNoteLabel,
        nextHref: payerHref,
        tone: "info",
      });
    }
  });

  transactions.forEach((transaction) => {
    const matchedAmount = matchedAmountByTransaction.get(transaction.billing_transaction_id) ?? 0;
    const remainingAmount = roundMoney(getTransactionAmount(transaction) - matchedAmount);
    if (remainingAmount > 0.009) {
      explanationRows.push({
        id: `unexplained-payment-${transaction.billing_transaction_id}`,
        payerLabel: "Nieustalony płatnik",
        problemLabel: "Wpłata bez jasnego przypisania",
        amountLabel: formatMoney(remainingAmount, transaction.currency ?? DEFAULT_CURRENCY),
        reasonLabel: "Są wpłaty, ale brak przypisania do naliczeń albo płatnika w obecnych danych.",
        nextHref: BILLING_PAYMENTS_ROUTE,
        tone: "warning",
      });
    }
  });

  debtRows.sort((a, b) => {
    const aPayerOnly = a.payerOnlyPaymentLabel.startsWith("Brak") ? 0 : 1;
    const bPayerOnly = b.payerOnlyPaymentLabel.startsWith("Brak") ? 0 : 1;
    return b.amount - a.amount || bPayerOnly - aPayerOnly || a.payerLabel.localeCompare(b.payerLabel, "pl");
  });
  overpaymentRows.sort((a, b) => b.amount - a.amount || a.payerLabel.localeCompare(b.payerLabel, "pl"));

  const uniqueExplanationRows = Array.from(new Map(explanationRows.map((row) => [row.id, row])).values()).slice(0, 12);
  const urgentRows: BillingUrgentDecisionRow[] = [
    ...debtRows.slice(0, 4).map((row) => ({
      id: `urgent-debt-${row.id}`,
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.reasonLabel,
      nextStepLabel: row.nextStepLabel,
      payerHref: row.payerHref,
      paymentsHref: row.paymentsHref,
      tone: row.attentionTone,
    })),
    ...overpaymentRows.slice(0, 2).map((row) => ({
      id: `urgent-overpayment-${row.id}`,
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.possibleSourceLabel,
      nextStepLabel: "Wejdź w szczegół płatnika",
      payerHref: row.payerHref,
      paymentsHref: row.paymentsHref,
      tone: "info" as const,
    })),
  ].slice(0, 6);

  const debtTotal = roundMoney(debtRows.reduce((sum, row) => sum + row.amount, 0));
  const overpaymentTotal = roundMoney(overpaymentRows.reduce((sum, row) => sum + row.amount, 0));
  const settledPayerCount = snapshot.payers.filter((payer) => {
    const values = getPayerBalanceValues(payer, balancesByPayerId.get(payer.billing_payer_id));
    return Math.abs(roundMoney(values.balanceDue)) <= 0.009;
  }).length;
  const payerOnlyPaymentCount = (snapshot.paymentMatches ?? []).filter((match) => !match.billing_charge_id).length;

  return {
    summary: {
      debtTotal,
      debtTotalLabel: formatMoney(debtTotal, DEFAULT_CURRENCY),
      debtPayerCount: debtRows.length,
      overpaymentTotal,
      overpaymentTotalLabel: formatMoney(overpaymentTotal, DEFAULT_CURRENCY),
      overpaymentPayerCount: overpaymentRows.length,
      settledPayerCount,
      explanationCount: uniqueExplanationRows.length,
      payerOnlyPaymentCount,
      limitationLabel:
        payerOnlyPaymentCount > 0
          ? "Część wpłat jest widoczna tylko przy płatniku. Widok nie przypisuje ich automatycznie do naliczeń ani okresów."
          : "Widok pokazuje wyłącznie stan wynikający z obecnych sald, naliczeń i widocznych przypisań.",
    },
    urgentRows,
    debtRows,
    overpaymentRows,
    explanationRows: uniqueExplanationRows,
    contextItems: [
      {
        label: "Co pokazuje",
        value: "Agreguje płatników z zaległościami, nadpłatami i sygnałami do wyjaśnienia.",
      },
      {
        label: "Czego nie robi",
        value: "Nie wysyła przypomnień, nie zmienia sald, nie rozlicza nadpłat i nie dopasowuje wpłat.",
      },
      {
        label: "Zakres danych",
        value: "Okresy, osoby i usługi są pokazane tylko wtedy, gdy wynikają z naliczeń albo bezpiecznych przypisań.",
      },
    ],
  };
}

function paymentReviewStatusLabel(status: BillingPaymentReviewStatusCode): string {
  return BILLING_PAYMENT_REVIEW_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
}

function workQueuePriorityRank(priority: BillingWorkQueuePriority): number {
  if (priority === "Wysoki") {
    return 3;
  }
  if (priority === "Średni") {
    return 2;
  }
  return 1;
}

function createWorkQueueIssue(input: Omit<BillingWorkQueueIssue, "id"> & { id: string }): BillingWorkQueueIssue {
  return input;
}

function lastPathNumber(path: string | undefined): number | undefined {
  if (!path) {
    return undefined;
  }
  const match = path.match(/\/(\d+)(?:$|\?)/);
  return match ? Number(match[1]) : undefined;
}

function workQueueIssueKey(
  issueType: BillingWorkQueueIssueType,
  targetType: BillingWorkQueueTargetType,
  targetId: number | undefined,
  reasonCode: string,
): string {
  return `${targetType}:${targetId ?? "summary"}:${reasonCode}:${normalizeText(issueType).replace(/\s+/g, "-")}`;
}

function latestWorkQueueEventByIssueKey(events: BillingWorkQueueEventRecord[] | undefined): Map<string, BillingWorkQueueEventRecord> {
  const latest = new Map<string, BillingWorkQueueEventRecord>();
  (events ?? []).forEach((event) => {
    const current = latest.get(event.issue_key);
    if (
      !current ||
      String(event.created_at ?? "").localeCompare(String(current.created_at ?? "")) > 0 ||
      ((event.created_at ?? "") === (current.created_at ?? "") &&
        event.billing_work_queue_event_id > current.billing_work_queue_event_id)
    ) {
      latest.set(event.issue_key, event);
    }
  });
  return latest;
}

export function buildBillingWorkQueueView(snapshot: BillingCenterSnapshot): BillingWorkQueueView {
  const debtsView = buildBillingDebtsOverpaymentsView(snapshot);
  const paymentsView = buildBillingPaymentsAllocationView(snapshot);
  const payersById = new Map(snapshot.payers.map((payer) => [payer.billing_payer_id, payer]));
  const matchesByTransactionId = new Map<number, BillingPaymentMatchRecord[]>();
  const latestStatusByTransactionId = new Map<number, BillingPaymentReviewStatusRecord>();
  const latestDecisionByIssueKey = latestWorkQueueEventByIssueKey(snapshot.workQueueEvents);

  (snapshot.paymentMatches ?? []).forEach((match) => {
    matchesByTransactionId.set(match.billing_transaction_id, [...(matchesByTransactionId.get(match.billing_transaction_id) ?? []), match]);
  });
  (snapshot.paymentReviewStatuses ?? []).forEach((status) => {
    const current = latestStatusByTransactionId.get(status.billing_transaction_id);
    if (
      !current ||
      String(status.created_at ?? "").localeCompare(String(current.created_at ?? "")) > 0 ||
      ((status.created_at ?? "") === (current.created_at ?? "") &&
        status.billing_payment_review_event_id > current.billing_payment_review_event_id)
    ) {
      latestStatusByTransactionId.set(status.billing_transaction_id, status);
    }
  });

  const issues: BillingWorkQueueIssue[] = [];

  paymentsView.payerOnlyRows.forEach((row) => {
    const targetId = lastPathNumber(row.paymentHref);
    const issueType = "Wpłata do wyjaśnienia" as const;
    issues.push(
      createWorkQueueIssue({
        id: `payer-only-${row.id}`,
        issueKey: workQueueIssueKey(issueType, "payment", targetId, "payer-only"),
        type: issueType,
        targetType: "payment",
        targetId,
        priority: "Średni",
        tone: "warning",
        payerLabel: row.payerLabel,
        payerHref: row.payerHref,
        paymentHref: row.paymentHref,
        amountLabel: row.amountLabel,
        reason: "Wpłata jest widoczna przy płatniku, ale nie ma przypisania do konkretnego naliczenia.",
        nextStep: "Otwórz szczegół wpłaty i sprawdź opis.",
        href: row.paymentHref ?? row.payerHref ?? BILLING_PAYMENTS_ROUTE,
      }),
    );
  });

  paymentsView.unexplainedRows.forEach((row) => {
    const targetId = lastPathNumber(row.paymentHref);
    const issueType = "Wpłata do wyjaśnienia" as const;
    issues.push(
      createWorkQueueIssue({
        id: `unexplained-${row.id}`,
        issueKey: workQueueIssueKey(issueType, "payment", targetId, "unexplained"),
        type: issueType,
        targetType: "payment",
        targetId,
        priority: "Wysoki",
        tone: "danger",
        payerLabel: row.payerLabel,
        payerHref: row.payerHref,
        paymentHref: row.paymentHref,
        amountLabel: row.amountLabel,
        reason: "Wpłata nie ma jasnego płatnika ani powiązania z naliczeniem.",
        nextStep: "Otwórz szczegół wpłaty i sprawdź opis.",
        href: row.paymentHref ?? BILLING_PAYMENTS_ROUTE,
      }),
    );
  });

  (snapshot.paymentReviewStatuses ?? []).forEach((status) => {
    const transaction = (snapshot.transactions ?? []).find((item) => item.billing_transaction_id === status.billing_transaction_id);
    const matches = matchesByTransactionId.get(status.billing_transaction_id) ?? [];
    const payerId = matches[0]?.billing_payer_id;
    const payer = payerId ? payersById.get(payerId) : undefined;
    const payerLabel = payer ? getPayerLabel(payer) : readString(transaction?.counterparty_name, "Nieustalony płatnik");
    const payerHref = payerId ? billingPayerDetailPath(payerId) : undefined;
    const paymentHref = billingPaymentDetailPath(status.billing_transaction_id);
    const amountLabel = formatMoney(transaction?.amount, transaction?.currency ?? DEFAULT_CURRENCY);
    const label = paymentReviewStatusLabel(status.status);
    const common = {
      payerLabel,
      payerHref,
      paymentHref,
      amountLabel,
      href: paymentHref,
      createdAt: status.created_at,
    };

    if (status.status === "needs_review") {
      const issueType = "Wpłata do wyjaśnienia" as const;
      issues.push(
        createWorkQueueIssue({
          ...common,
          id: `status-needs-review-${status.billing_payment_review_event_id}`,
          issueKey: workQueueIssueKey(issueType, "payment", status.billing_transaction_id, "status-needs-review"),
          type: issueType,
          targetType: "payment",
          targetId: status.billing_transaction_id,
          priority: "Wysoki",
          tone: "danger",
          reason: `Status operacyjny wpłaty: ${label}.`,
          nextStep: "Otwórz szczegół wpłaty i sprawdź opis.",
        }),
      );
    }
    if (status.status === "waiting_for_contact") {
      const issueType = "Czeka na kontakt" as const;
      issues.push(
        createWorkQueueIssue({
          ...common,
          id: `status-contact-${status.billing_payment_review_event_id}`,
          issueKey: workQueueIssueKey(issueType, "payment", status.billing_transaction_id, "status-contact"),
          type: issueType,
          targetType: "payment",
          targetId: status.billing_transaction_id,
          priority: "Wysoki",
          tone: "danger",
          reason: "Status operacyjny wskazuje, że trzeba skontaktować się z płatnikiem.",
          nextStep: payerHref ? "Wejdź w płatnika i sprawdź notatki." : "Otwórz szczegół wpłaty i sprawdź opis.",
        }),
      );
    }
    if (status.status === "waiting_for_payment") {
      const issueType = "Czeka na wpłatę" as const;
      issues.push(
        createWorkQueueIssue({
          ...common,
          id: `status-payment-${status.billing_payment_review_event_id}`,
          issueKey: workQueueIssueKey(issueType, "payment", status.billing_transaction_id, "status-payment"),
          type: issueType,
          targetType: "payment",
          targetId: status.billing_transaction_id,
          priority: "Średni",
          tone: "warning",
          reason: "Status operacyjny wskazuje oczekiwanie na wpłatę.",
          nextStep: payerHref ? "Sprawdź zaległość i ostatnią wpłatę." : "Otwórz szczegół wpłaty.",
        }),
      );
    }
    if (status.status === "do_not_auto_match") {
      const issueType = "Nie ruszać automatycznie" as const;
      issues.push(
        createWorkQueueIssue({
          ...common,
          id: `status-do-not-auto-${status.billing_payment_review_event_id}`,
          issueKey: workQueueIssueKey(issueType, "payment", status.billing_transaction_id, "status-do-not-auto"),
          type: issueType,
          targetType: "payment",
          targetId: status.billing_transaction_id,
          priority: "Wysoki",
          tone: "danger",
          reason: "Status operacyjny blokuje automatyczne ruszanie tej wpłaty.",
          nextStep: "Otwórz szczegół wpłaty i sprawdź kontekst.",
        }),
      );
    }
  });

  debtsView.debtRows.forEach((row) => {
    const high = row.amount >= 300 && row.lastPaymentLabel === "Brak ostatniej wpłaty";
    const issueType = high ? ("Czeka na wpłatę" as const) : ("Zaległość do sprawdzenia" as const);
    const targetId = lastPathNumber(row.payerHref);
    issues.push(
      createWorkQueueIssue({
        id: `debt-${row.id}`,
        issueKey: workQueueIssueKey(issueType, "payer", targetId, high ? "debt-waiting-payment" : "debt-check"),
        type: issueType,
        targetType: "payer",
        targetId,
        priority: high ? "Wysoki" : row.amount < 100 ? "Niski" : "Średni",
        tone: high ? "danger" : row.amount < 100 ? "info" : "warning",
        payerLabel: row.payerLabel,
        payerHref: row.payerHref,
        amountLabel: row.amountLabel,
        reason: row.reasonLabel,
        nextStep: high ? "Sprawdź zaległość i ostatnią wpłatę." : row.nextStepLabel,
        href: row.payerHref,
      }),
    );
  });

  debtsView.overpaymentRows.forEach((row) => {
    const issueType = "Nadpłata do decyzji" as const;
    const targetId = lastPathNumber(row.payerHref);
    issues.push(
      createWorkQueueIssue({
        id: `overpayment-${row.id}`,
        issueKey: workQueueIssueKey(issueType, "payer", targetId, "overpayment"),
        type: issueType,
        targetType: "payer",
        targetId,
        priority: "Średni",
        tone: "info",
        payerLabel: row.payerLabel,
        payerHref: row.payerHref,
        amountLabel: row.amountLabel,
        reason: row.possibleSourceLabel,
        nextStep: "Zweryfikuj, czy nadpłata wymaga decyzji.",
        href: row.payerHref,
      }),
    );
  });

  const checkedRows = (snapshot.paymentReviewStatuses ?? [])
    .filter((status) => status.status === "checked")
    .slice()
    .sort(
      (a, b) =>
        String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")) ||
        b.billing_payment_review_event_id - a.billing_payment_review_event_id,
    )
    .slice(0, 8)
    .map((status) => {
      const transaction = (snapshot.transactions ?? []).find((item) => item.billing_transaction_id === status.billing_transaction_id);
      const matches = matchesByTransactionId.get(status.billing_transaction_id) ?? [];
      const payerId = matches[0]?.billing_payer_id;
      const payer = payerId ? payersById.get(payerId) : undefined;
      return createWorkQueueIssue({
        id: `checked-${status.billing_payment_review_event_id}`,
        issueKey: workQueueIssueKey("Sprawdzone", "payment", status.billing_transaction_id, "status-checked"),
        type: "Sprawdzone",
        targetType: "payment",
        targetId: status.billing_transaction_id,
        priority: "Niski",
        tone: "ok",
        payerLabel: payer ? getPayerLabel(payer) : readString(transaction?.counterparty_name, "Nieustalony płatnik"),
        payerHref: payerId ? billingPayerDetailPath(payerId) : undefined,
        paymentHref: billingPaymentDetailPath(status.billing_transaction_id),
        amountLabel: formatMoney(transaction?.amount, transaction?.currency ?? DEFAULT_CURRENCY),
        reason: "Wpłata została oznaczona jako sprawdzona.",
        nextStep: "W razie potrzeby wróć do szczegółu wpłaty.",
        href: billingPaymentDetailPath(status.billing_transaction_id),
        createdAt: status.created_at,
      });
    });

  const actionableIssues = Array.from(new Map(issues.map((issue) => [issue.id, issue])).values())
    .filter((issue) => issue.type !== "Sprawdzone")
    .sort(
      (a, b) =>
        workQueuePriorityRank(b.priority) - workQueuePriorityRank(a.priority) ||
        String(b.createdAt ?? "").localeCompare(String(a.createdAt ?? "")) ||
        a.payerLabel.localeCompare(b.payerLabel, "pl"),
    );

  const activeIssues = actionableIssues.filter((issue) => {
    const decision = latestDecisionByIssueKey.get(issue.issueKey);
    return decision?.action !== "handled" && decision?.action !== "snoozed";
  });
  const snoozedRows = actionableIssues.filter((issue) => latestDecisionByIssueKey.get(issue.issueKey)?.action === "snoozed").slice(0, 12);
  const handledRows = actionableIssues.filter((issue) => latestDecisionByIssueKey.get(issue.issueKey)?.action === "handled").slice(0, 12);

  const paymentRows = activeIssues.filter((issue) =>
    ["Wpłata do wyjaśnienia", "Nie ruszać automatycznie"].includes(issue.type),
  );
  const contactRows = activeIssues.filter((issue) => ["Czeka na kontakt", "Czeka na wpłatę", "Zaległość do sprawdzenia"].includes(issue.type));
  const overpaymentRows = activeIssues.filter((issue) => issue.type === "Nadpłata do decyzji");

  return {
    summary: {
      highPriorityCount: activeIssues.filter((issue) => issue.priority === "Wysoki").length,
      needsReviewCount: paymentRows.length,
      contactCount: contactRows.length,
      overpaymentCount: overpaymentRows.length,
      debtCount: activeIssues.filter((issue) => issue.type === "Zaległość do sprawdzenia" || issue.type === "Czeka na wpłatę").length,
      checkedCount: checkedRows.length,
      snoozedCount: snoozedRows.length,
      handledCount: handledRows.length,
    },
    firstRows: activeIssues.slice(0, 8),
    paymentRows,
    contactRows,
    overpaymentRows,
    checkedRows,
    snoozedRows,
    handledRows,
    contextItems: [
      {
        label: "Co pokazuje",
        value: "Łączy zaległości, nadpłaty, wpłaty do wyjaśnienia, statusy operacyjne i notatki rozliczeniowe w jedną listę pracy.",
      },
      {
        label: "Czego nie robi",
        value: "Nie zmienia sald, wpłat, naliczeń ani przypisań. Nie wysyła przypomnień i nie tworzy zadań.",
      },
      {
        label: "Jak z tego korzystać",
        value: "Kliknij w szczegół wpłaty, płatnika, wpłaty albo zaległości i podejmij decyzję poza tym widokiem.",
      },
    ],
  };
}

function buildPayerChargeRows(charges: BillingChargeRecord[]): BillingPayerChargeRow[] {
  return charges
    .slice()
    .sort((a, b) => String(b.due_date ?? b.period_label ?? "").localeCompare(String(a.due_date ?? a.period_label ?? "")))
    .map((charge) => ({
      id: String(charge.billing_charge_id),
      periodLabel: readString(charge.period_label, "Okres bez nazwy"),
      personLabel: readString(charge.student_full_name, "Osoba bez nazwy"),
      serviceLabel: readString(charge.model_name, "Usługa bez nazwy"),
      amountLabel: formatMoney(charge.total_amount, DEFAULT_CURRENCY),
      statusLabel: readString(charge.status, "Status nieznany"),
    }));
}

function buildPayerPaymentRows(
  payer: BillingPayerRecord,
  balance: BillingBalanceRecord | undefined,
): BillingPayerPaymentRow[] {
  const values = getPayerBalanceValues(payer, balance);
  if (!values.lastPaymentDate) {
    return [];
  }

  return [
    {
      id: `last-payment-${payer.billing_payer_id}`,
      dateLabel: formatDateLabel(values.lastPaymentDate),
      amountLabel: formatMoney(values.lastPaymentAmount, values.lastPaymentCurrency ?? DEFAULT_CURRENCY),
      titleLabel: readString(values.lastPaymentTitle, "Ostatnia widoczna wpłata"),
      contextLabel: "To ostatnia wpłata dostępna w obecnym read-only widoku rozliczeń.",
    },
  ];
}

function buildPayerNoteRows(notes: BillingPayerNoteRecord[], payerId: number): BillingPayerNoteRow[] {
  return notes
    .filter((note) => note.billing_payer_id === payerId)
    .slice()
    .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")) || b.billing_note_id - a.billing_note_id)
    .map((note) => ({
      id: String(note.billing_note_id),
      authorLabel: safeBillingText(note.author_user_name, note.author_user_id ? `Użytkownik #${note.author_user_id}` : "Operator"),
      dateLabel: formatDateLabel(note.created_at, "Brak daty"),
      typeLabel: note.note_type === "operator_note" || !note.note_type ? "Notatka operatora" : safeBillingText(note.note_type, "Notatka"),
      noteText: safeBillingText(note.note_text, "Ukryto techniczną lub wrażliwą treść notatki."),
    }));
}

export function getBillingContactChannelLabel(channel: BillingContactChannel): string {
  return BILLING_CONTACT_CHANNEL_OPTIONS.find((option) => option.value === channel)?.label ?? "Inny kanał";
}

export function getBillingContactActionLabel(action: BillingContactAction): string {
  return BILLING_CONTACT_ACTION_OPTIONS.find((option) => option.value === action)?.label ?? "Kontakt";
}

function buildBillingContactEventRows(events: BillingContactEventRecord[], payerId: number): BillingContactEventRow[] {
  return events
    .filter((event) => event.billing_payer_id === payerId)
    .slice()
    .sort(
      (a, b) =>
        String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")) ||
        b.billing_contact_event_id - a.billing_contact_event_id,
    )
    .map((event) => ({
      id: String(event.billing_contact_event_id),
      channelLabel: getBillingContactChannelLabel(event.channel),
      actionLabel: getBillingContactActionLabel(event.contact_action),
      authorLabel: safeBillingText(event.created_by_user_name, event.created_by_user_id ? `Użytkownik #${event.created_by_user_id}` : "Operator"),
      dateLabel: formatDateLabel(event.created_at, "Brak daty"),
      messageText: event.message_text ? safeBillingText(event.message_text, "Ukryto techniczną lub wrażliwą treść wiadomości.") : undefined,
      noteText: event.note_text ? safeBillingText(event.note_text, "Ukryto techniczną lub wrażliwą treść notatki.") : undefined,
      contextLabel: event.related_payment_id
        ? `Powiązane z wpłatą #${event.related_payment_id}`
        : event.related_issue_key
          ? "Powiązane ze sprawą rozliczeniową"
          : "Kontakt zapisany przy płatniku",
    }));
}

export function getBillingNextStepTypeLabel(stepType: BillingNextStepType): string {
  return BILLING_NEXT_STEP_TYPE_OPTIONS.find((option) => option.value === stepType)?.label ?? "Inny krok";
}

export function getBillingNextStepActionLabel(action: BillingNextStepEventAction): string {
  return BILLING_NEXT_STEP_ACTION_OPTIONS.find((option) => option.value === action)?.label ?? "Krok";
}

function nextStepTargetHref(event: BillingNextStepEventRecord): string | undefined {
  if (event.target_type === "payer" && event.target_id) {
    return billingPayerDetailPath(event.target_id);
  }
  if (event.target_type === "payment" && event.target_id) {
    return billingPaymentDetailPath(event.target_id);
  }
  if (event.target_type === "work_queue_issue") {
    return BILLING_WORK_QUEUE_ROUTE;
  }
  return undefined;
}

function nextStepTargetLabel(event: BillingNextStepEventRecord): string {
  if (event.target_type === "payer") {
    return event.target_id ? `Płatnik #${event.target_id}` : "Płatnik";
  }
  if (event.target_type === "payment") {
    return event.target_id ? `Wpłata #${event.target_id}` : "Wpłata";
  }
  if (event.target_type === "work_queue_issue") {
    return "Sprawa rozliczeniowa";
  }
  if (event.target_type === "contact") {
    return event.target_id ? `Kontakt #${event.target_id}` : "Kontakt rozliczeniowy";
  }
  return "Rozliczenia";
}

export function buildBillingNextStepRows(
  events: BillingNextStepEventRecord[],
  options: {
    action?: BillingNextStepEventAction;
    targetType?: BillingNextStepTargetType;
    targetId?: number;
    relatedIssueKey?: string;
    limit?: number;
  } = {},
): BillingNextStepRow[] {
  const normalizedIssueKey = options.relatedIssueKey?.trim();
  return events
    .filter((event) => (options.action ? event.event_action === options.action : true))
    .filter((event) => (options.targetType ? event.target_type === options.targetType : true))
    .filter((event) => (options.targetId ? event.target_id === options.targetId : true))
    .filter((event) => (normalizedIssueKey ? event.related_issue_key === normalizedIssueKey : true))
    .slice()
    .sort(
      (a, b) =>
        String(b.created_at ?? b.planned_for ?? "").localeCompare(String(a.created_at ?? a.planned_for ?? "")) ||
        b.billing_next_step_event_id - a.billing_next_step_event_id,
    )
    .slice(0, options.limit ?? 8)
    .map((event) => ({
      id: String(event.billing_next_step_event_id),
      title: safeBillingText(event.title, "Następny krok"),
      stepTypeLabel: getBillingNextStepTypeLabel(event.step_type),
      eventActionLabel: getBillingNextStepActionLabel(event.event_action),
      targetLabel: nextStepTargetLabel(event),
      targetHref: nextStepTargetHref(event),
      dateLabel: event.planned_for ? `Na ${formatDateLabel(event.planned_for)}` : formatDateLabel(event.created_at, "Bez daty"),
      noteText: event.note_text ? safeBillingText(event.note_text, "Ukryto techniczną lub wrażliwą treść notatki.") : undefined,
      relatedIssueKey: event.related_issue_key ?? undefined,
    }));
}

function contactTextExcerpt(value: string | null | undefined, fallback = "Brak treści w danych"): string {
  const text = safeBillingText(value, "").trim();
  if (!text) {
    return fallback;
  }
  return text.length > 160 ? `${text.slice(0, 157).trim()}...` : text;
}

function buildBillingContactCenterRows(events: BillingContactEventRecord[]): BillingContactCenterRow[] {
  return events
    .slice()
    .sort(
      (a, b) =>
        String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")) ||
        b.billing_contact_event_id - a.billing_contact_event_id,
    )
    .map((event) => {
      const isDraft = event.contact_action === "draft_prepared";
      const isPromisedPayment = event.contact_action === "promised_payment";
      const isNoAnswer = event.contact_action === "no_answer";
      const needsFollowup = event.contact_action === "needs_followup";
      const payerLabel = safeBillingText(event.payer_display_name, "Płatnik");
      return {
        id: String(event.billing_contact_event_id),
        payerLabel,
        payerHref: `${BILLING_PAYER_DETAIL_ROUTE}/${event.billing_payer_id}`,
        paymentHref: event.related_payment_id ? `${BILLING_PAYMENTS_ROUTE}/${event.related_payment_id}` : undefined,
        workQueueHref: BILLING_WORK_QUEUE_ROUTE,
        channelLabel: getBillingContactChannelLabel(event.channel),
        actionLabel: getBillingContactActionLabel(event.contact_action),
        dateLabel: formatDateLabel(event.created_at, "Brak daty"),
        messageExcerpt: event.message_text ? contactTextExcerpt(event.message_text, "Brak treści wiadomości") : undefined,
        noteExcerpt: event.note_text ? contactTextExcerpt(event.note_text, "Brak notatki") : undefined,
        contextLabel: event.related_payment_id
          ? "Kontakt powiązany z wpłatą"
          : event.related_issue_key
            ? "Kontakt powiązany ze sprawą rozliczeniową"
            : "Kontakt zapisany przy płatniku",
        attentionReason: isNoAnswer
          ? "Brak odpowiedzi może wymagać ponownego kontaktu."
          : needsFollowup
            ? "Wpis oznaczono jako wymagający ponowienia kontaktu."
            : isPromisedPayment
              ? "Deklaracja płatności wymaga późniejszego sprawdzenia wpłaty."
              : isDraft
                ? "Przygotowano treść, ale CASI Workspace jej nie wysłał."
                : "Kontakt zapisany w historii płatnika.",
        isDraft,
        isPromisedPayment,
        isNoAnswer,
        needsFollowup,
      };
    });
}

export function buildBillingContactCenterView(
  events: BillingContactEventRecord[],
  filters: BillingContactCenterFilters = {},
): BillingContactCenterView {
  const allRows = buildBillingContactCenterRows(events);
  const normalizedQuery = normalizeText(filters.payerQuery ?? "");
  const filteredRows = allRows.filter((row) => {
    const event = events.find((item) => String(item.billing_contact_event_id) === row.id);
    if (!event) {
      return false;
    }
    if (filters.channel && filters.channel !== "all" && event.channel !== filters.channel) {
      return false;
    }
    if (filters.action && filters.action !== "all" && event.contact_action !== filters.action) {
      return false;
    }
    if (normalizedQuery && !normalizeText(row.payerLabel).includes(normalizedQuery)) {
      return false;
    }
    return true;
  });
  const draftRows = allRows.filter((row) => row.isDraft);
  const promisedPaymentRows = allRows.filter((row) => row.isPromisedPayment);
  const followupRows = allRows.filter((row) => row.isNoAnswer || row.needsFollowup);
  const attentionRows = allRows.filter((row) => row.isNoAnswer || row.needsFollowup || row.isPromisedPayment || row.isDraft).slice(0, 10);

  return {
    summary: {
      totalCount: allRows.length,
      draftCount: draftRows.length,
      promisedPaymentCount: promisedPaymentRows.length,
      noAnswerCount: allRows.filter((row) => row.isNoAnswer).length,
      needsFollowupCount: allRows.filter((row) => row.needsFollowup).length,
      recentCount: allRows.slice(0, 7).length,
    },
    allRows,
    filteredRows,
    attentionRows,
    draftRows,
    promisedPaymentRows,
    followupRows,
    contextItems: [
      {
        label: "Zakres",
        value: "Ten ekran zbiera historię kontaktów rozliczeniowych z płatnikami w wybranej organizacji.",
      },
      {
        label: "Brak wysyłki",
        value: "CASI Workspace nie wysyła wiadomości z tego widoku i nie tworzy automatycznych przypomnień.",
      },
      {
        label: "Finanse",
        value: "Kontakt, draft albo deklaracja płatności nie zmienia sald, wpłat, naliczeń ani przypisań.",
      },
    ],
  };
}

function uniqueOperationalItems(items: BillingOperationalReportImportantItem[], limit = 10): BillingOperationalReportImportantItem[] {
  return Array.from(new Map(items.map((item) => [item.id, item])).values()).slice(0, limit);
}

function buildOperationalReportText({
  organizationName,
  summary,
  importantRows,
  limitations,
}: {
  organizationName: string;
  summary: BillingOperationalReportSummary;
  importantRows: BillingOperationalReportImportantItem[];
  limitations: string[];
}): string {
  const lines = [
    `Raport rozliczeniowy — ${organizationName}`,
    "",
    "1. Podsumowanie",
    `- Suma zaległości: ${summary.debtTotalLabel}`,
    `- Płatnicy z zaległością: ${summary.debtPayerCount}`,
    `- Suma nadpłat: ${summary.overpaymentTotalLabel}`,
    `- Wpłaty do wyjaśnienia: ${summary.payerOnlyPaymentCount + summary.unexplainedPaymentCount}`,
    `- Aktywne sprawy: ${summary.activeIssueCount}`,
    `- Kontakty wymagające działania: ${summary.contactActionRequiredCount}`,
    "",
    "2. Najważniejsze do sprawdzenia",
    ...(importantRows.length
      ? importantRows.map((item) => {
          const amount = item.amountLabel ? ` · ${item.amountLabel}` : "";
          return `- ${item.typeLabel}: ${item.payerLabel}${amount}. ${item.reasonLabel} Następny krok: ${item.nextStepLabel}`;
        })
      : ["- Brak oczywistych spraw do sprawdzenia w aktualnych danych."]),
    "",
    "3. Ograniczenia",
    ...limitations.map((item) => `- ${item}`),
  ];

  return lines.join("\n");
}

export function buildBillingOperationalReport(
  snapshot: BillingCenterSnapshot,
  organizationName = "Wybrana organizacja",
): BillingOperationalReportView {
  const debtsView = buildBillingDebtsOverpaymentsView(snapshot);
  const paymentsView = buildBillingPaymentsAllocationView(snapshot);
  const workQueueView = buildBillingWorkQueueView(snapshot);
  const contactView = buildBillingContactCenterView(snapshot.contactEvents ?? []);
  const activeWorkQueueRows = Array.from(
    new Map(
      [...workQueueView.firstRows, ...workQueueView.paymentRows, ...workQueueView.contactRows, ...workQueueView.overpaymentRows].map((row) => [
        row.id,
        row,
      ]),
    ).values(),
  );
  const paymentOperationalCount = snapshot.paymentReviewStatuses?.length ?? 0;
  const paymentNeedsExplanationCount = paymentsView.payerOnlyRows.length + paymentsView.unexplainedRows.length;
  const contactActionRequiredCount = contactView.attentionRows.length;

  const summary: BillingOperationalReportSummary = {
    debtTotalLabel: debtsView.summary.debtTotalLabel,
    debtPayerCount: debtsView.summary.debtPayerCount,
    overpaymentTotalLabel: debtsView.summary.overpaymentTotalLabel,
    overpaymentPayerCount: debtsView.summary.overpaymentPayerCount,
    settledPayerCount: debtsView.summary.settledPayerCount,
    chargeAssignedPaymentCount: paymentsView.chargeAssignedRows.length,
    payerOnlyPaymentCount: paymentsView.payerOnlyRows.length,
    unexplainedPaymentCount: paymentsView.unexplainedRows.length,
    activeIssueCount: activeWorkQueueRows.length,
    snoozedIssueCount: workQueueView.snoozedRows.length,
    handledIssueCount: workQueueView.handledRows.length,
    contactCount: contactView.summary.totalCount,
    contactActionRequiredCount,
  };

  const importantRows = uniqueOperationalItems([
    ...debtsView.debtRows.slice(0, 3).map((row): BillingOperationalReportImportantItem => ({
      id: `debt-${row.id}`,
      typeLabel: "Zaległość",
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.reasonLabel,
      nextStepLabel: row.nextStepLabel,
      href: row.payerHref,
    })),
    ...paymentsView.unexplainedRows.slice(0, 3).map((row): BillingOperationalReportImportantItem => ({
      id: `unexplained-payment-${row.id}`,
      typeLabel: "Wpłata do wyjaśnienia",
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.contextLabel,
      nextStepLabel: "Otwórz szczegół wpłaty i sprawdź opis.",
      href: row.paymentHref ?? BILLING_PAYMENTS_ROUTE,
    })),
    ...paymentsView.payerOnlyRows.slice(0, 3).map((row): BillingOperationalReportImportantItem => ({
      id: `payer-only-payment-${row.id}`,
      typeLabel: "Wpłata tylko przy płatniku",
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.contextLabel,
      nextStepLabel: "Sprawdź płatnika albo szczegół wpłaty.",
      href: row.paymentHref ?? row.payerHref ?? BILLING_PAYMENTS_ROUTE,
    })),
    ...workQueueView.firstRows.slice(0, 4).map((row): BillingOperationalReportImportantItem => ({
      id: `work-${row.id}`,
      typeLabel: row.type,
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.reason,
      nextStepLabel: row.nextStep,
      href: row.href,
    })),
    ...contactView.followupRows.slice(0, 3).map((row): BillingOperationalReportImportantItem => ({
      id: `contact-${row.id}`,
      typeLabel: "Kontakt wymagający działania",
      payerLabel: row.payerLabel,
      reasonLabel: row.attentionReason,
      nextStepLabel: "Otwórz centrum kontaktów i sprawdź historię.",
      href: BILLING_CONTACT_CENTER_ROUTE,
    })),
    ...debtsView.overpaymentRows.slice(0, 2).map((row): BillingOperationalReportImportantItem => ({
      id: `overpayment-${row.id}`,
      typeLabel: "Nadpłata do decyzji",
      payerLabel: row.payerLabel,
      amountLabel: row.amountLabel,
      reasonLabel: row.possibleSourceLabel,
      nextStepLabel: "Otwórz szczegół płatnika i sprawdź kontekst.",
      href: row.payerHref,
    })),
  ]);

  const limitations = [
    "Raport pokazuje aktualny stan danych i nie jest dokumentem księgowym.",
    "Raport nie zmienia danych, sald, naliczeń, wpłat ani przypisań.",
    "CASI Workspace nie wysyła tego raportu i nie tworzy z niego pliku.",
    "Widok nie przypisuje wpłat do naliczeń ani nie rozstrzyga nadpłat.",
    "Filtrowanie po okresie będzie osobnym etapem, jeśli dane okresów będą wystarczająco kompletne.",
  ];

  return {
    summary,
    summaryCards: [
      {
        id: "debt-total",
        label: "Suma zaległości",
        value: summary.debtTotalLabel,
        description: "Widoczna suma dopłat w aktualnych danych organizacji.",
      },
      {
        id: "debt-payers",
        label: "Płatnicy z zaległością",
        value: String(summary.debtPayerCount),
        description: "Płatnicy, u których saldo wskazuje dopłatę.",
      },
      {
        id: "overpayment-total",
        label: "Suma nadpłat",
        value: summary.overpaymentTotalLabel,
        description: "Widoczne nadpłaty bez automatycznej decyzji.",
      },
      {
        id: "payments-explanation",
        label: "Wpłaty do wyjaśnienia",
        value: String(paymentNeedsExplanationCount),
        description: "Wpłaty bez pełnego powiązania z naliczeniem albo płatnikiem.",
      },
      {
        id: "active-issues",
        label: "Aktywne sprawy",
        value: String(summary.activeIssueCount),
        description: "Sprawy rozliczeniowe widoczne do sprawdzenia.",
      },
      {
        id: "contacts-action",
        label: "Kontakty wymagające działania",
        value: String(summary.contactActionRequiredCount),
        description: "Kontakty bez odpowiedzi albo wymagające ponowienia.",
      },
    ],
    importantRows,
    paymentRows: [...paymentsView.unexplainedRows, ...paymentsView.payerOnlyRows, ...paymentsView.chargeAssignedRows].slice(0, 8),
    debtRows: debtsView.debtRows.slice(0, 8),
    overpaymentRows: debtsView.overpaymentRows.slice(0, 8),
    workQueueRows: activeWorkQueueRows.slice(0, 8),
    contactRows: contactView.attentionRows.slice(0, 8),
    reportText: buildOperationalReportText({
      organizationName,
      summary,
      importantRows,
      limitations,
    }),
    limitations,
    contextItems: [
      {
        label: "Zakres raportu",
        value: "Raport obejmuje aktualnie widoczne dane wybranej organizacji.",
      },
      {
        label: "Wpłaty operacyjne",
        value: `${paymentOperationalCount} wpisów statusu operacyjnego wpłat w aktualnym zbiorze danych.`,
      },
      {
        label: "Okresy",
        value: "Okresy są pokazywane jako kontekst, ale raport nie filtruje jeszcze danych po okresie.",
      },
    ],
  };
}

function buildPayerRelatedInvoiceRows(
  payer: BillingPayerRecord,
  students: BillingStudentRecord[],
  invoices: InvoiceRecord[],
): BillingPayerRelatedInvoiceRow[] {
  const names = new Set([getPayerLabel(payer), ...students.map((student) => readString(student.full_name, ""))].map(normalizeText).filter(Boolean));
  return invoices
    .filter((invoice) => {
      const contractorLabel = normalizeText(getInvoiceContractorLabel(invoice));
      return contractorLabel && names.has(contractorLabel);
    })
    .slice(0, 8)
    .map((invoice, index) => {
      const invoiceId = getInvoiceId(invoice);
      return {
        id: String(invoiceId ?? index),
        href: invoiceId ? `/faktury/${invoiceId}` : "/faktury",
        invoiceLabel: getInvoiceLabel(invoice),
        contractorLabel: getInvoiceContractorLabel(invoice),
        amountLabel: formatMoney(getInvoiceAmount(invoice), invoice.currency || DEFAULT_CURRENCY),
        statusLabel: readString(invoice.status || invoice.workflow_state, "Status nieznany"),
      };
    });
}

function buildPayerRelatedWorkItemRows(
  payer: BillingPayerRecord,
  students: BillingStudentRecord[],
  workItems: WorkItemRecord[],
): BillingRelatedWorkItemRow[] {
  const searchTerms = [
    getPayerLabel(payer),
    payer.contact_phone,
    payer.payment_identifier,
    payer.email,
    ...students.map((student) => student.full_name),
  ]
    .map(normalizeText)
    .filter(Boolean);

  return workItems
    .filter((item) => {
      if (item.is_closed) {
        return false;
      }
      const metadata = isRecord(item.metadata) ? item.metadata : {};
      const metadataPayerId = readNumber(metadata.billing_payer_id ?? metadata.payer_id ?? metadata.billingPayerId);
      if (metadataPayerId === payer.billing_payer_id) {
        return true;
      }
      const haystack = normalizeText(`${item.title ?? ""} ${item.description ?? ""} ${item.source_type ?? ""}`);
      return searchTerms.some((term) => term.length >= 3 && haystack.includes(term));
    })
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
    .slice(0, 8)
    .map((item) => ({
      id: String(item.work_item_id),
      href: `/work-items/${item.work_item_id}`,
      titleLabel: readString(item.title, `Sprawa #${item.work_item_id}`),
      statusLabel: readString(item.status, "Status nieznany"),
      priorityLabel: readString(item.priority_level, "Priorytet nieznany"),
      reasonLabel: item.is_sla_overdue || item.is_due_overdue ? "Termin sprawy wymaga uwagi." : "Sprawa może dotyczyć tego płatnika lub osób objętych rozliczeniem.",
    }));
}

export function buildBillingPayerDetailView(snapshot: BillingCenterSnapshot, payerId: number): BillingPayerDetailView | null {
  const payer = snapshot.payers.find((item) => item.billing_payer_id === payerId);
  if (!payer) {
    return null;
  }

  const payerStudents = snapshot.students.filter((student) => student.billing_payer_id === payer.billing_payer_id);
  const payerCharges = snapshot.charges.filter((charge) => charge.billing_payer_id === payer.billing_payer_id);
  const payerBalance = snapshot.balances.find((balance) => balance.billing_payer_id === payer.billing_payer_id);
  const values = getPayerBalanceValues(payer, payerBalance);
  const title = getPayerLabel(payer);
  const balanceRecord: BillingBalanceRecord = {
    billing_payer_id: payer.billing_payer_id,
    display_name: payer.display_name,
    contact_phone: payer.contact_phone,
    payment_identifier: payer.payment_identifier,
    email: payer.email,
    is_active: payer.is_active,
    total_charges: values.totalCharges,
    total_matches: values.totalMatches,
    balance_due: values.balanceDue,
    last_payment_at: values.lastPaymentDate ?? null,
    last_payment_amount: values.lastPaymentAmount ?? null,
    last_payment_currency: values.lastPaymentCurrency ?? DEFAULT_CURRENCY,
    last_payment_title: values.lastPaymentTitle ?? null,
    matched_payment_count: payer.billing_matched_payment_count ?? payerBalance?.matched_payment_count ?? 0,
  };

  return {
    id: String(payer.billing_payer_id),
    title,
    statusLabel: payer.is_active === false ? "Nieaktywny" : values.balanceDue > 0 ? "Do dopłaty" : values.balanceDue < 0 ? "Nadpłata" : "Rozliczony",
    statusTone: payer.is_active === false ? "neutral" : values.balanceDue > 0 ? "warning" : values.balanceDue < 0 ? "info" : "ok",
    payerTypeLabel: getPayerTypeLabel(payerStudents),
    contactLabel: readString(payer.contact_phone || payer.email, "Brak kontaktu w danych"),
    paymentIdentifierLabel: readString(payer.payment_identifier, "Brak identyfikatora płatności"),
    balanceMeaningLabel: balanceMeaningLabel(values.balanceDue),
    chargedLabel: formatMoney(values.totalCharges, DEFAULT_CURRENCY),
    paidLabel: formatMoney(values.totalMatches, DEFAULT_CURRENCY),
    balanceLabel: formatMoney(values.balanceDue, DEFAULT_CURRENCY),
    lastPaymentLabel: values.lastPaymentDate
      ? `${formatDateLabel(values.lastPaymentDate)} · ${formatMoney(values.lastPaymentAmount, values.lastPaymentCurrency ?? DEFAULT_CURRENCY)}`
      : "Brak ostatniej wpłaty",
    peopleRows: buildPayerPersonRows(payerStudents),
    serviceRows: buildPayerServiceRows(payerCharges, payerStudents),
    balanceExplanationRows: buildBillingBalanceExplanationRows([balanceRecord], [payer], payerStudents, payerCharges, 1),
    chargeRows: buildPayerChargeRows(payerCharges),
    paymentRows: buildPayerPaymentRows(payer, payerBalance),
    noteRows: buildPayerNoteRows(snapshot.payerNotes ?? [], payer.billing_payer_id),
    contactEventRows: buildBillingContactEventRows(snapshot.contactEvents ?? [], payer.billing_payer_id),
    invoiceRows: buildPayerRelatedInvoiceRows(payer, payerStudents, snapshot.invoices),
    workItemRows: buildPayerRelatedWorkItemRows(payer, payerStudents, snapshot.workItems),
    contextItems: [
      {
        label: "Zakres",
        value: "Szczegół płatnika łączy osoby objęte rozliczeniem, usługi, naliczenia i widoczne wpłaty.",
      },
      {
        label: "Tryb",
        value: "Widok jest tylko do odczytu. Nie dodaje platnosci, nie nalicza oplat i nie zmienia sald.",
      },
      {
        label: "Płatnik a rodzina",
        value:
          payerStudents.length > 1
            ? "Ten płatnik obejmuje kilka osób, więc rodzina jest szczególnym przypadkiem płatnika."
            : "Płatnik jest główną jednostką rozliczenia; rodzina jest tylko jednym z możliwych typów płatnika.",
      },
    ],
  };
}

export function buildBillingRelatedWorkItemRows(
  workItems: WorkItemRecord[],
  invoices: InvoiceRecord[],
  contractors: ContractorRecord[],
  limit = 8,
): BillingRelatedWorkItemRow[] {
  return workItems
    .filter((item) => !item.is_closed && isBillingRelatedWorkItem(item, invoices, contractors))
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
    .slice(0, limit)
    .map((item) => ({
      id: String(item.work_item_id),
      href: `/work-items/${item.work_item_id}`,
      titleLabel: readString(item.title, `Sprawa #${item.work_item_id}`),
      statusLabel: readString(item.status, "Status nieznany"),
      priorityLabel: readString(item.priority_level, "Priorytet nieznany"),
      reasonLabel: item.description || "Sprawa powiązana z fakturą, płatnością albo kontrahentem.",
    }));
}

export function buildBillingRecentPaymentRows(items: BillingBalanceRecord[], limit = 5): BillingRecentPaymentRow[] {
  return items
    .filter((item) => item.last_payment_at)
    .sort((a, b) => String(b.last_payment_at).localeCompare(String(a.last_payment_at)))
    .slice(0, limit)
    .map((item) => ({
      id: String(item.billing_payer_id),
      payerLabel: getBalancePayerLabel(item),
      amountLabel: formatMoney(item.last_payment_amount, item.last_payment_currency || DEFAULT_CURRENCY),
      dateLabel: formatDateLabel(item.last_payment_at),
      titleLabel: readString(item.last_payment_title, "Ostatnia wpłata"),
    }));
}

export function hasBillingData(status: BillingStatus, items: BillingBalanceRecord[] | null): boolean {
  return status === "ready" && Boolean(items?.length);
}

export function hasBillingCenterData(status: BillingStatus, snapshot: BillingCenterSnapshot | null): boolean {
  return (
    status === "ready" &&
    Boolean(
      snapshot &&
        (snapshot.balances.length ||
          snapshot.payers.length ||
          snapshot.students.length ||
          snapshot.charges.length ||
          snapshot.invoices.length ||
          snapshot.contractors.length ||
          snapshot.workItems.length),
    )
  );
}

export function buildBillingPayerNoteRequest(
  noteText: string,
  organizationId: string | number | null | undefined,
): BillingPayerNoteValidationResult {
  if (!canUseBillingOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE,
    };
  }

  const trimmedNote = noteText.trim();
  if (!trimmedNote) {
    return {
      ok: false,
      message: "Notatka rozliczeniowa nie może być pusta.",
    };
  }

  if (trimmedNote.length > BILLING_PAYER_NOTE_MAX_LENGTH) {
    return {
      ok: false,
      message: `Notatka rozliczeniowa może mieć maksymalnie ${BILLING_PAYER_NOTE_MAX_LENGTH} znaków.`,
    };
  }

  return {
    ok: true,
    payload: {
      note_text: trimmedNote,
    },
  };
}

export function buildBillingContactEventRequest({
  payerId,
  channel,
  contactAction,
  messageText,
  noteText,
  organizationId,
  relatedPaymentId,
  relatedIssueKey,
}: {
  payerId: number;
  channel: BillingContactChannel;
  contactAction: BillingContactAction;
  messageText: string;
  noteText: string;
  organizationId: string | number | null | undefined;
  relatedPaymentId?: number;
  relatedIssueKey?: string;
}): BillingContactEventValidationResult {
  if (!canUseBillingOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: BILLING_PAYER_DETAIL_ORGANIZATION_REQUIRED_TITLE,
    };
  }

  if (!payerId || !Number.isFinite(payerId)) {
    return {
      ok: false,
      message: "Nie można zapisać kontaktu bez płatnika.",
    };
  }

  if (!isBillingContactChannel(channel)) {
    return {
      ok: false,
      message: "Wybierz poprawny kanał kontaktu.",
    };
  }

  if (!isBillingContactAction(contactAction)) {
    return {
      ok: false,
      message: "Wybierz poprawny typ wpisu kontaktowego.",
    };
  }

  const trimmedMessage = messageText.trim();
  const trimmedNote = noteText.trim();
  if (!trimmedMessage && !trimmedNote) {
    return {
      ok: false,
      message: "Dodaj treść roboczą albo krótką notatkę z kontaktu.",
    };
  }

  if (contactAction === "draft_prepared" && !trimmedMessage) {
    return {
      ok: false,
      message: "Przygotowanie treści wymaga wiadomości do skopiowania.",
    };
  }

  if (trimmedMessage.length > BILLING_CONTACT_MESSAGE_MAX_LENGTH) {
    return {
      ok: false,
      message: `Treść wiadomości może mieć maksymalnie ${BILLING_CONTACT_MESSAGE_MAX_LENGTH} znaków.`,
    };
  }

  if (trimmedNote.length > BILLING_CONTACT_NOTE_MAX_LENGTH) {
    return {
      ok: false,
      message: `Notatka kontaktowa może mieć maksymalnie ${BILLING_CONTACT_NOTE_MAX_LENGTH} znaków.`,
    };
  }

  const payload: {
    payer_id: number;
    related_payment_id?: number;
    related_issue_key?: string;
    channel: BillingContactChannel;
    contact_action: BillingContactAction;
    message_text?: string;
    note_text?: string;
  } = {
    payer_id: payerId,
    channel,
    contact_action: contactAction,
  };
  if (relatedPaymentId) {
    payload.related_payment_id = relatedPaymentId;
  }
  const trimmedIssueKey = relatedIssueKey?.trim();
  if (trimmedIssueKey) {
    payload.related_issue_key = trimmedIssueKey;
  }
  if (trimmedMessage) {
    payload.message_text = trimmedMessage;
  }
  if (trimmedNote) {
    payload.note_text = trimmedNote;
  }

  return {
    ok: true,
    payload,
  };
}

export function buildBillingNextStepRequest({
  targetType,
  targetId,
  relatedIssueKey,
  stepType,
  eventAction = "planned",
  title,
  noteText,
  plannedFor,
  organizationId,
}: {
  targetType: BillingNextStepTargetType;
  targetId?: number;
  relatedIssueKey?: string;
  stepType: BillingNextStepType;
  eventAction?: BillingNextStepEventAction;
  title: string;
  noteText: string;
  plannedFor?: string;
  organizationId: string | number | null | undefined;
}): BillingNextStepValidationResult {
  if (!canUseBillingOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: BILLING_ORGANIZATION_REQUIRED_TITLE,
    };
  }

  if (!isBillingNextStepTargetType(targetType)) {
    return {
      ok: false,
      message: "Wybierz poprawny typ miejsca, którego dotyczy krok.",
    };
  }

  if (!isBillingNextStepType(stepType)) {
    return {
      ok: false,
      message: "Wybierz poprawny typ kroku.",
    };
  }

  if (!isBillingNextStepEventAction(eventAction)) {
    return {
      ok: false,
      message: "Wybierz poprawny stan kroku.",
    };
  }

  if (["payer", "payment", "contact"].includes(targetType) && (!targetId || !Number.isFinite(targetId))) {
    return {
      ok: false,
      message: "Ten typ kroku wymaga poprawnego powiązanego rekordu.",
    };
  }

  const trimmedIssueKey = relatedIssueKey?.trim();
  if (targetType === "work_queue_issue" && !trimmedIssueKey) {
    return {
      ok: false,
      message: "Krok przy sprawie wymaga wskazania sprawy rozliczeniowej.",
    };
  }

  const trimmedTitle = title.trim();
  if (!trimmedTitle) {
    return {
      ok: false,
      message: "Tytuł następnego kroku nie może być pusty.",
    };
  }
  if (trimmedTitle.length > BILLING_NEXT_STEP_TITLE_MAX_LENGTH) {
    return {
      ok: false,
      message: `Tytuł następnego kroku może mieć maksymalnie ${BILLING_NEXT_STEP_TITLE_MAX_LENGTH} znaków.`,
    };
  }

  const trimmedNote = noteText.trim();
  if (trimmedNote.length > BILLING_NEXT_STEP_NOTE_MAX_LENGTH) {
    return {
      ok: false,
      message: `Notatka kroku może mieć maksymalnie ${BILLING_NEXT_STEP_NOTE_MAX_LENGTH} znaków.`,
    };
  }

  const trimmedPlannedFor = plannedFor?.trim();
  if (trimmedPlannedFor && !/^\d{4}-\d{2}-\d{2}$/.test(trimmedPlannedFor)) {
    return {
      ok: false,
      message: "Data kroku powinna mieć format RRRR-MM-DD.",
    };
  }

  return {
    ok: true,
    payload: {
      target_type: targetType,
      ...(targetId ? { target_id: targetId } : {}),
      ...(trimmedIssueKey ? { related_issue_key: trimmedIssueKey } : {}),
      step_type: stepType,
      event_action: eventAction,
      title: trimmedTitle,
      ...(trimmedNote ? { note_text: trimmedNote } : {}),
      ...(trimmedPlannedFor ? { planned_for: trimmedPlannedFor } : {}),
    },
  };
}

export function buildBillingPaymentReviewStatusRequest(
  status: string,
  noteText: string,
  organizationId: string | number | null | undefined,
): BillingPaymentReviewStatusValidationResult {
  if (!canUseBillingOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: BILLING_PAYMENT_DETAIL_ORGANIZATION_REQUIRED_TITLE,
    };
  }

  const normalizedStatus = status.trim();
  if (!isBillingPaymentReviewStatusCode(normalizedStatus)) {
    return {
      ok: false,
      message: "Wybierz poprawny status operacyjny wpłaty.",
    };
  }

  const trimmedNote = noteText.trim();
  if (trimmedNote.length > BILLING_PAYMENT_REVIEW_STATUS_MAX_NOTE_LENGTH) {
    return {
      ok: false,
      message: `Notatka statusu może mieć maksymalnie ${BILLING_PAYMENT_REVIEW_STATUS_MAX_NOTE_LENGTH} znaków.`,
    };
  }

  return {
    ok: true,
    payload: trimmedNote ? { status: normalizedStatus, note_text: trimmedNote } : { status: normalizedStatus },
  };
}

export function buildBillingWorkQueueDecisionRequest(
  issue: BillingWorkQueueIssue | null | undefined,
  action: BillingWorkQueueEventAction,
  noteText: string,
  organizationId: string | number | null | undefined,
): BillingWorkQueueDecisionValidationResult {
  if (!canUseBillingOrganizationScope(organizationId)) {
    return {
      ok: false,
      message: BILLING_ORGANIZATION_REQUIRED_TITLE,
    };
  }
  if (!issue) {
    return {
      ok: false,
      message: "Wybierz sprawę rozliczeniową przed zapisem decyzji.",
    };
  }
  if (!isBillingWorkQueueAction(action)) {
    return {
      ok: false,
      message: "Wybierz poprawną decyzję sprawy rozliczeniowej.",
    };
  }

  const trimmedNote = noteText.trim();
  if (trimmedNote.length > BILLING_WORK_QUEUE_DECISION_MAX_NOTE_LENGTH) {
    return {
      ok: false,
      message: `Notatka decyzji może mieć maksymalnie ${BILLING_WORK_QUEUE_DECISION_MAX_NOTE_LENGTH} znaków.`,
    };
  }

  return {
    ok: true,
    payload: {
      issue_key: issue.issueKey,
      issue_type: issue.type,
      target_type: issue.targetType,
      ...(issue.targetId ? { target_id: issue.targetId } : {}),
      action,
      ...(trimmedNote ? { note_text: trimmedNote } : {}),
    },
  };
}

export function getBillingPaymentReviewStatusErrorState(error: unknown): BillingPaymentReviewStatusErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby zapisać status operacyjny wpłaty.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnień do statusu",
        description: "Twoje konto nie ma uprawnień do oznaczania wpłat w tej organizacji.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono wpłaty",
        description: "Status nie został zapisany, bo backend nie znalazł wpłaty w wybranej organizacji.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zapisał statusu",
        description: "Wystąpił błąd serwera. Status nie jest traktowany jako zapisany bez potwierdzenia backendu.",
      };
    }
    return {
      status: "error",
      title: `Błąd API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format statusu",
      description: "Backend odpowiedział, ale status operacyjny nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem z API",
      description: "Nie udało się połączyć z backendem. Status nie został potwierdzony.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się zapisać statusu",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd zapisu statusu operacyjnego.",
  };
}

export function getBillingPayerNoteErrorState(error: unknown): BillingPayerNoteErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby dodać notatkę rozliczeniową.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnień do notatki",
        description: "Twoje konto nie ma uprawnień do dodawania notatek rozliczeniowych.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono płatnika",
        description: "Notatka nie została zapisana, bo backend nie znalazł płatnika w wybranej organizacji.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zapisał notatki",
        description: "Wystąpił błąd serwera. Notatka nie jest traktowana jako zapisana bez potwierdzenia backendu.",
      };
    }
    return {
      status: "error",
      title: `Błąd API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format notatki",
      description: "Backend odpowiedział, ale zapisana notatka nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem z API",
      description: "Nie udało się połączyć z backendem. Notatka nie została potwierdzona.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się dodać notatki",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd dodawania notatki rozliczeniowej.",
  };
}

export function getBillingContactEventErrorState(error: unknown): BillingContactEventErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby zapisać kontakt rozliczeniowy.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnień do kontaktu",
        description: "Twoje konto nie ma uprawnień do zapisywania kontaktów rozliczeniowych.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono płatnika",
        description: "Kontakt nie został zapisany, bo backend nie znalazł płatnika albo wpłaty w wybranej organizacji.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zapisał kontaktu",
        description: "Wystąpił błąd serwera. Kontakt nie jest traktowany jako zapisany bez potwierdzenia backendu.",
      };
    }
    return {
      status: "error",
      title: `Błąd API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format kontaktu",
      description: "Backend odpowiedział, ale zapisany kontakt nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem z API",
      description: "Nie udało się połączyć z backendem. Kontakt nie został potwierdzony.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się zapisać kontaktu",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd zapisu kontaktu rozliczeniowego.",
  };
}

export function getBillingNextStepErrorState(error: unknown): BillingNextStepErrorState {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return {
        status: "unauthenticated",
        title: "Sesja wygasła",
        description: "Zaloguj się ponownie, aby zapisać następny krok.",
      };
    }
    if (error.status === 403) {
      return {
        status: "forbidden",
        title: "Brak uprawnień do kroku",
        description: "Twoje konto nie ma uprawnień do zapisywania kroków w tej organizacji.",
      };
    }
    if (error.status === 404) {
      return {
        status: "error",
        title: "Nie znaleziono powiązanego rekordu",
        description: "Krok nie został zapisany, bo backend nie znalazł powiązanego płatnika, wpłaty albo kontaktu w wybranej organizacji.",
      };
    }
    if (error.status >= 500) {
      return {
        status: "server-error",
        title: "Backend nie zapisał kroku",
        description: "Wystąpił błąd serwera. Krok nie jest traktowany jako zapisany bez potwierdzenia backendu.",
      };
    }
    return {
      status: "error",
      title: `Błąd API (${error.status})`,
      description: error.message,
    };
  }

  if (error instanceof ApiContractError) {
    return {
      status: "error",
      title: "Niepoprawny format kroku",
      description: "Backend odpowiedział, ale zapisany krok nie pasuje do oczekiwanego kontraktu.",
    };
  }

  if (error instanceof TypeError) {
    return {
      status: "error",
      title: "Problem z połączeniem z API",
      description: "Nie udało się połączyć z backendem. Krok nie został potwierdzony.",
    };
  }

  return {
    status: "error",
    title: "Nie udało się zapisać kroku",
    description: error instanceof Error ? error.message : "Wystąpił nieznany błąd zapisu następnego kroku.",
  };
}

export function createBillingPayerNoteSubmitter(deps: BillingPayerNoteSubmitterDeps) {
  let inFlight = false;

  return async function submitBillingPayerNote(
    validation: BillingPayerNoteValidationResult,
  ): Promise<BillingPayerNoteSubmitResult> {
    if (!validation.ok) {
      return {
        status: "blocked",
        message: validation.message,
      };
    }

    if (inFlight) {
      return { status: "ignored" };
    }

    inFlight = true;
    deps.setSubmitting(true);

    try {
      await deps.submitNote(validation.payload);
      await deps.refreshDetail();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getBillingPayerNoteErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmitting(false);
    }
  };
}

export function createBillingContactEventSubmitter(deps: BillingContactEventSubmitterDeps) {
  let inFlight = false;

  return async function submitBillingContactEvent(
    validation: BillingContactEventValidationResult,
  ): Promise<BillingContactEventSubmitResult> {
    if (!validation.ok) {
      return {
        status: "blocked",
        message: validation.message,
      };
    }

    if (inFlight) {
      return { status: "ignored" };
    }

    inFlight = true;
    deps.setSubmitting(true);

    try {
      await deps.submitContact(validation.payload);
      await deps.refreshDetail();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getBillingContactEventErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmitting(false);
    }
  };
}

export function createBillingNextStepSubmitter(deps: BillingNextStepSubmitterDeps) {
  let inFlight = false;

  return async function submitBillingNextStep(
    validation: BillingNextStepValidationResult,
  ): Promise<BillingNextStepSubmitResult> {
    if (!validation.ok) {
      return {
        status: "blocked",
        message: validation.message,
      };
    }

    if (inFlight) {
      return { status: "ignored" };
    }

    inFlight = true;
    deps.setSubmitting(true);

    try {
      await deps.submitNextStep(validation.payload);
      await deps.refreshDetail();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getBillingNextStepErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmitting(false);
    }
  };
}

export function createBillingPaymentReviewStatusSubmitter(deps: BillingPaymentReviewStatusSubmitterDeps) {
  let inFlight = false;

  return async function submitBillingPaymentReviewStatus(
    validation: BillingPaymentReviewStatusValidationResult,
  ): Promise<BillingPaymentReviewStatusSubmitResult> {
    if (!validation.ok) {
      return {
        status: "blocked",
        message: validation.message,
      };
    }

    if (inFlight) {
      return { status: "ignored" };
    }

    inFlight = true;
    deps.setSubmitting(true);

    try {
      await deps.submitStatus(validation.payload);
      await deps.refreshStatus();
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorState: getBillingPaymentReviewStatusErrorState(error),
      };
    } finally {
      inFlight = false;
      deps.setSubmitting(false);
    }
  };
}

export function isBillingEmpty(status: BillingStatus, items: BillingBalanceRecord[] | null): boolean {
  return status === "ready" && Array.isArray(items) && items.length === 0;
}

export function isBillingCenterEmpty(status: BillingStatus, snapshot: BillingCenterSnapshot | null): boolean {
  if (status !== "ready" || !snapshot) {
    return false;
  }

  return (
    snapshot.balances.length === 0 &&
    snapshot.payers.length === 0 &&
    snapshot.students.length === 0 &&
    snapshot.charges.length === 0 &&
    snapshot.invoices.length === 0 &&
    snapshot.contractors.length === 0 &&
    snapshot.workItems.length === 0
  );
}

export function canUseBillingOrganizationScope(organizationId: string | number | null | undefined): boolean {
  return organizationId !== null && organizationId !== undefined && String(organizationId).trim().length > 0;
}

export function billingScreenHasForbiddenTechnicalText(values: string[]): boolean {
  const normalized = values.map(normalizeText).join(" ");
  return ["storage_key", "data/magazyn", "c:\\users", "token", "secret", "connection string", "raw json", "payload"].some((term) =>
    normalized.includes(term),
  );
}

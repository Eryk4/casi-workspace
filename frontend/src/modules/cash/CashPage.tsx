import { BillingLedgerOverview } from "@/modules/billing/BillingLedgerOverview";

export function CashPage() {
  return (
    <BillingLedgerOverview
      description="Read-only podglad sald, dopasowanych wplat i ostatnich platnosci z istniejacego ledgeru billingowego."
      eyebrow="Kasa"
      title="Kasa"
    />
  );
}

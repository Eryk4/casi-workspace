import { notFound } from "next/navigation";

import { BillingPaymentDetailPage } from "@/modules/billing/BillingPaymentDetailPage";

type BillingPaymentRouteProps = {
  params: Promise<{
    paymentId: string;
  }>;
};

export default async function Page({ params }: BillingPaymentRouteProps) {
  const { paymentId } = await params;
  const parsedPaymentId = Number(paymentId);

  if (!Number.isInteger(parsedPaymentId) || parsedPaymentId <= 0) {
    notFound();
  }

  return <BillingPaymentDetailPage paymentId={parsedPaymentId} />;
}

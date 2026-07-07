import { notFound } from "next/navigation";

import { BillingPayerDetailPage } from "@/modules/billing/BillingPayerDetailPage";

type BillingPayerRouteProps = {
  params: Promise<{
    payerId: string;
  }>;
};

export default async function Page({ params }: BillingPayerRouteProps) {
  const { payerId } = await params;
  const parsedPayerId = Number(payerId);

  if (!Number.isInteger(parsedPayerId) || parsedPayerId <= 0) {
    notFound();
  }

  return <BillingPayerDetailPage payerId={parsedPayerId} />;
}

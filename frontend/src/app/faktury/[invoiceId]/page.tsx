import { notFound } from "next/navigation";

import { InvoiceDetailPage } from "@/modules/invoices/InvoiceDetailPage";

type InvoiceRouteProps = {
  params: Promise<{
    invoiceId: string;
  }>;
};

export default async function Page({ params }: InvoiceRouteProps) {
  const { invoiceId } = await params;
  const parsedInvoiceId = Number(invoiceId);

  if (!Number.isInteger(parsedInvoiceId) || parsedInvoiceId <= 0) {
    notFound();
  }

  return <InvoiceDetailPage invoiceId={parsedInvoiceId} />;
}

import { notFound } from "next/navigation";

import { AutomationOperationDetailPage } from "@/modules/automations/AutomationOperationDetailPage";

type Props = { params: Promise<{ automationKey: string }> };

export default async function AutomationOperationDetailRoute({ params }: Props) {
  const { automationKey } = await params;
  if (!automationKey || automationKey.length > 120) notFound();
  return <AutomationOperationDetailPage automationKey={automationKey} />;
}

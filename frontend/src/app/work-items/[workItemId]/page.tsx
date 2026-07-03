import { notFound } from "next/navigation";

import { WorkItemDetailPage } from "@/modules/work-items/WorkItemDetailPage";

type WorkItemRouteProps = {
  params: Promise<{
    workItemId: string;
  }>;
};

export default async function Page({ params }: WorkItemRouteProps) {
  const { workItemId } = await params;
  const parsedWorkItemId = Number(workItemId);

  if (!Number.isInteger(parsedWorkItemId) || parsedWorkItemId <= 0) {
    notFound();
  }

  return <WorkItemDetailPage workItemId={parsedWorkItemId} />;
}

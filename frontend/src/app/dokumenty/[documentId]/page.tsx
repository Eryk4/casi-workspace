import { notFound } from "next/navigation";

import { DocumentDetailPage } from "@/modules/documents/DocumentDetailPage";

type DocumentRouteProps = {
  params: Promise<{
    documentId: string;
  }>;
};

export default async function Page({ params }: DocumentRouteProps) {
  const { documentId } = await params;
  const parsedDocumentId = Number(documentId);

  if (!Number.isInteger(parsedDocumentId) || parsedDocumentId <= 0) {
    notFound();
  }

  return <DocumentDetailPage documentId={parsedDocumentId} />;
}

import { notFound } from "next/navigation";

import { ContractorDetailPage } from "@/modules/crm/ContractorDetailPage";

type ContractorRouteProps = {
  params: Promise<{
    contractorId: string;
  }>;
};

export default async function Page({ params }: ContractorRouteProps) {
  const { contractorId } = await params;
  const parsedContractorId = Number(contractorId);

  if (!Number.isInteger(parsedContractorId) || parsedContractorId <= 0) {
    notFound();
  }

  return <ContractorDetailPage contractorId={parsedContractorId} />;
}

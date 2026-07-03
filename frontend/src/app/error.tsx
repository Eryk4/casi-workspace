"use client";

import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return (
    <div className="app-state-page">
      <ErrorState
        description={error.message || "Wystapil blad renderowania widoku. Sprobuj odswiezyc modul."}
        title="Nie udalo sie wyswietlic modulu"
      />
      <div className="app-state-page__actions">
        <Button icon={<RefreshCw size={15} />} onClick={reset} variant="primary">
          Sprobuj ponownie
        </Button>
      </div>
    </div>
  );
}

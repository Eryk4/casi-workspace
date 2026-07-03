"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import { Lock, Mail } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError, api } from "@/lib/api";
import { LOGIN_FORM_ACTION, LOGIN_FORM_METHOD, resolveLoginRedirect } from "./authModel";

export function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [login, setLogin] = useState("antoni@casi24.com");
  const [password, setPassword] = useState("casi24");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = useMemo(() => {
    const requested = searchParams.get("next");
    return resolveLoginRedirect(requested);
  }, [searchParams]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await api.login(login, password);
      router.replace(nextPath);
      router.refresh();
    } catch (nextError) {
      if (nextError instanceof ApiError) {
        setError(nextError.message);
      } else if (nextError instanceof Error) {
        setError(nextError.message);
      } else {
        setError("Nie udalo sie zalogowac. Sprawdz dane i sprobuj ponownie.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page" aria-label="Logowanie do CASI Workspace">
      <section className="login-card">
        <div className="login-card__brand">
          <span className="login-card__mark">C</span>
          <div>
            <strong>CASI Workspace</strong>
            <span>Panel operacyjny</span>
          </div>
        </div>
        <div className="login-card__copy">
          <p className="login-card__eyebrow">Dostep do aplikacji</p>
          <h1>Zaloguj sie do workspace</h1>
          <p>Po zalogowaniu frontend Next pobierze dane z backendu przez skonfigurowane API.</p>
        </div>

        <form action={LOGIN_FORM_ACTION} className="login-form" method={LOGIN_FORM_METHOD} onSubmit={handleSubmit}>
          <Input
            autoComplete="username"
            icon={<Mail aria-hidden="true" size={16} />}
            label="Login lub e-mail"
            name="login"
            onChange={(event) => setLogin(event.target.value)}
            required
            type="text"
            value={login}
          />
          <Input
            autoComplete="current-password"
            icon={<Lock aria-hidden="true" size={16} />}
            label="Haslo"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          {error ? (
            <div className="login-form__error" role="alert">
              {error}
            </div>
          ) : null}
          <Button disabled={isSubmitting} size="lg" type="submit" variant="primary">
            {isSubmitting ? "Logowanie..." : "Zaloguj"}
          </Button>
        </form>
      </section>
    </main>
  );
}

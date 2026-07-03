import type { Metadata } from "next";

import { AppShell } from "@/layouts/AppShell";

import "./globals.css";

export const metadata: Metadata = {
  title: "CASI Workspace",
  description: "Produkcyjny frontend CASI oparty o Next.js i wspolny AppShell.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body>
        <a className="skip-link" href="#main-content">
          Przejdz do tresci
        </a>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

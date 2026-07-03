"use client";

import type { ReactNode } from "react";

import { Button } from "./Button";

type ModalProps = {
  children: ReactNode;
  footer?: ReactNode;
  open: boolean;
  title: string;
  onClose: () => void;
};

export function Modal({ children, footer, onClose, open, title }: ModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="ui-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="ui-modal__backdrop" onClick={onClose} />
      <section className="ui-modal__panel">
        <header className="ui-modal__header">
          <h2 id="modal-title">{title}</h2>
          <Button aria-label="Zamknij modal" onClick={onClose} size="sm" variant="ghost">
            Zamknij
          </Button>
        </header>
        <div className="ui-modal__body">{children}</div>
        {footer ? <footer className="ui-modal__footer">{footer}</footer> : null}
      </section>
    </div>
  );
}

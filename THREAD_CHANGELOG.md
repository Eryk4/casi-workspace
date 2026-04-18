# THREAD_CHANGELOG

Wspolny dziennik zmian miedzy watkami.

## Zasady

- Najswiezszy wpis dodawaj na gore.
- Kazdy wpis powinien miec:
  - date i czas (Europe/Warsaw)
  - zakres watku
  - zmienione pliki
  - co zmieniono
  - ryzyko/skutki uboczne
  - co sprawdzic lokalnie
  - co sprawdzic na Railway (jesli deploy byl zlecony)

---

## 2026-04-18 18:45 (Europe/Warsaw) - Inicjalizacja governance watkow

- Zakres watku:
  - uporzadkowanie zasad miedzy watkami

- Zmienione pliki:
  - STARTER_WATKOW.md
  - THREAD_STATE.md
  - THREAD_CHANGELOG.md

- Co zmieniono:
  - Dodano centralny starter dla watkow.
  - Dodano snapshot aktualnych zasad.
  - Dodano wspolny dziennik zmian.

- Ryzyko/skutki uboczne:
  - Watki, ktore nie dostana polecenia odczytu plikow, moga pracowac po starych zalozeniach.

- Co sprawdzic lokalnie:
  - czy nowe watki zaczynaja od odczytu trzech plikow i potwierdzaja zasady.

- Co sprawdzic na Railway:
  - brak (nie zlecono deployu).

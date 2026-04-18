# STARTER WATKOW (CASI Workspace)

To jest plik startowy dla nowych i aktualnych watkow wspoltworzacych aplikacje.

## Zasady nadrzedne

1. Repozytorium robocze:
- pracujemy tylko w `C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace`

2. Deploy:
- domyslnie pracujemy lokalnie
- na Railway wdrazamy tylko po wyraznej komendzie uzytkownika: `wdroz na Railway`
- bez takiej komendy: brak deployu, brak zmian produkcyjnych

3. Baza danych:
- docelowo (produkcja): PostgreSQL
- lokalny szybki dev/testy: SQLite jest dopuszczony
- nie usuwac obslugi SQLite dla lokalnych testow bez jawnej decyzji

4. Synchronizacja watkow:
- przed praca przeczytaj `THREAD_STATE.md` i ostatnie wpisy z `THREAD_CHANGELOG.md`
- po wiekszej zmianie dopisz wpis do `THREAD_CHANGELOG.md`

5. Raport po zmianie:
- zmienione pliki
- co zrobiono
- ryzyko/skutki uboczne
- co sprawdzic lokalnie
- co sprawdzic na Railway (tylko jesli byl zlecony deploy)

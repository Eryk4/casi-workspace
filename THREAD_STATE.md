# THREAD_STATE

Aktualny stan zasad pracy (snapshot) dla CASI Workspace.

## Obowiazujace teraz

1. Pracujemy w repo:
- `C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace`

2. Tryb pracy:
- domyslnie: tylko lokalne repo
- deploy Railway: tylko po wyraznym poleceniu uzytkownika

3. Baza:
- PostgreSQL: docelowy runtime produkcyjny
- SQLite: dopuszczony dla szybkich lokalnych testow/developingu

4. Spojnosc local vs Railway:
- po zleconym deployu wykonac parity-check:
- `python compare_environment_parity.py --remote-base https://<url-railway>`

5. Dziennik zmian:
- kazdy duzy task dopisuje wpis do `THREAD_CHANGELOG.md`

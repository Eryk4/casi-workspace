Folder zawiera gotowe pliki do klikania.

Najczęściej używane:

1. `01 - Uruchom lokalnie.bat`
   Start aplikacji tylko na tym komputerze.

2. `02 - Uruchom w sieci lokalnej.bat`
   Start aplikacji tak, aby inne komputery w tej samej sieci mogły wejść po adresie IP tego komputera.

3. `03 - Reset danych demo.bat`
   Kasuje obecną bazę i odtwarza dane demonstracyjne.

4. `04 - Uruchom testy.bat`
   Sprawdza, czy aplikacja działa poprawnie po zmianach.

5. `05 - Pokaż pomoc migracji do PostgreSQL.bat`
   Pokazuje opis migracji z lokalnej SQLite do docelowej bazy.

6. `06 - Migracja z SQLite do PostgreSQL.bat`
   Uruchamia migrację danych do skonfigurowanej bazy docelowej.
   Wymaga ustawionego `INVOICE_DATABASE_URL` albo `DATABASE_URL`.

7. `07 - Uruchom na PostgreSQL.bat`
   Uruchamia aplikację na skonfigurowanej bazie PostgreSQL.
   Wymaga ustawionego `INVOICE_DATABASE_URL` albo `DATABASE_URL`.

Ważne:

- jeśli plik `.bat` kończy pracę od razu, przeczytaj komunikat w tym samym oknie
- nie zamykaj okna serwera, jeśli aplikacja ma działać
- do migracji na PostgreSQL trzeba jeszcze skopiować magazyn plików dokumentów i OCR

Folder zawiera gotowe pliki do klikania.

Najczesciej uzywane:

1. `01 - Uruchom lokalnie.bat`
   Start aplikacji tylko na tym komputerze.

2. `02 - Uruchom w sieci lokalnej.bat`
   Start aplikacji tak, aby inne komputery w tej samej sieci mogly wejsc po adresie IP tego komputera.

3. `03 - Reset danych demo.bat`
   Kasuje obecna baze i odtwarza dane demonstracyjne.

4. `04 - Uruchom testy.bat`
   Sprawdza, czy aplikacja dziala poprawnie po zmianach.

5. `05 - Pokaz pomoc migracji do PostgreSQL.bat`
   Pokazuje opis migracji z lokalnej SQLite do docelowej bazy.

6. `06 - Migracja z SQLite do PostgreSQL.bat`
   Uruchamia migracje danych do skonfigurowanej bazy docelowej.
   Wymaga ustawionego `INVOICE_DATABASE_URL` albo `DATABASE_URL`.

7. `07 - Uruchom na PostgreSQL.bat`
   Uruchamia aplikacje na skonfigurowanej bazie PostgreSQL.
   Korzysta z `INVOICE_DATABASE_URL` / `DATABASE_URL` albo z wpisu w `.env.local`.

Wazne:

- jesli plik `.bat` konczy prace od razu, przeczytaj komunikat w tym samym oknie
- nie zamykaj okna serwera, jesli aplikacja ma dzialac
- do migracji na PostgreSQL trzeba jeszcze skopiowac magazyn plikow dokumentow i OCR

8. `08 - Otworz ustawienia e-mail.bat`
   Tworzy z przykladu plik `.env.local` i otwiera go do wpisania danych skrzynki.

9. `09 - Test polaczenia e-mail.bat`
   Sprawdza polaczenie IMAP i pokazuje, ile nowych dokumentow system widzi przed importem.

10. `10 - Sprawdz gotowosc e-mail.bat`
   Pokazuje, czy system e-mail i konkretne organizacje sa juz gotowe do pierwszego realnego testu importu.

11. `11 - Konfigurator e-mail.bat`
   Otwiera prosty konfigurator i zapisuje dane IMAP, automat oraz podstawowe pola Google OAuth do `.env.local`.

12. `12 - Sprawdz gotowosc Google OAuth e-mail.bat`
   Sprawdza, czy publiczny adres HTTPS i dane klienta Google sa juz gotowe do przycisku `Polacz Google Workspace`.

13. `13 - Testy HTTP.bat`
   Uruchamia caly podzielony zestaw testow HTTP bez pozostalych, ciezszych modulow.

14. `14 - Testy HTTP szybkie.bat`
   Uruchamia te same testy HTTP jako jawna lista paczek tematycznych.
   To przydaje sie do codziennej pracy po zmianach w API i panelu.

15. `15 - Testy zadan.bat`
   Uruchamia rozbite testy modulu zadan i przypomnien.

16. `16 - Testy faktur.bat`
   Uruchamia rozbite testy modulu faktur, duplikatow, KSeF i wspolpracy zespolowej.

17. `17 - Testy kalendarzy.bat`
   Uruchamia rozbite testy modulu kalendarzy i integracji Google Calendar.

18. `18 - Testy wyszukiwania.bat`
   Uruchamia rozbite testy wyszukiwarki i uprawnien wynikow.

19. `19 - Testy smoke.bat`
   Uruchamia najsensowniejszy szybki zestaw do codziennej pracy: skladnia, core, faktury, kluczowe HTTP i wyszukiwarka.

20. `20 - Kontrola przed deployem.bat`
   Uruchamia uporzadkowany zestaw przed wdrozeniem: skladnia oraz wszystkie glowne grupy testow domenowych.

21. `21 - Pelny test discover.bat`
   Uruchamia pelne `unittest discover` dla calego repo.

22. `22 - Ustaw PostgreSQL URL lokalnie.bat`
   Jednorazowo zapisuje `INVOICE_DATABASE_URL` do `.env.local`.
   Po tym kroku nie trzeba juz ustawiac zmiennej recznie przy kazdym starcie.

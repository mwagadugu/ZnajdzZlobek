# Znajdź Żłobek — mapa żłobków we Wrocławiu

Aplikacja Streamlit do wizualizacji rozmieszczenia żłobków we Wrocławiu oraz analizy danych z PostgreSQL/PostGIS.

## Uruchomienie — jedna komenda

Wymaganie: [Docker Desktop](https://www.docker.com/products/docker-desktop/) lub Docker z wtyczką Compose.

Po pobraniu repozytorium z GitHuba otwórz terminal **w katalogu projektu** i uruchom:

```bash
docker compose up --build
```

Po starcie kontenerów wejdź na **http://localhost:8501**.

Docker automatycznie:
- buduje środowisko Pythona z bibliotekami z `requirements.txt`,
- uruchamia PostgreSQL z PostGIS,
- importuje dane z pliku `zlobki.sql` przy **pierwszym** utworzeniu bazy,
- uruchamia aplikację Streamlit.

Nie trzeba osobno instalować Pythona, PostgreSQL ani bibliotek.

## Zatrzymywanie i ponowne uruchomienie

Naciśnij `Ctrl+C`, aby zakończyć działanie uruchomionego polecenia.
Aby wyłączyć kontenery działające w tle (jeśli były uruchomione z `-d`):

```bash
docker compose down
```

Dane PostgreSQL są zapisywane w wolumenie Dockera i pozostają między uruchomieniami.
**Uwaga:** `docker compose down -v` usuwa wolumen bazy i jej dane — przy kolejnym uruchomieniu baza zostanie ponownie zaimportowana z `zlobki.sql`.

## Hasło bazy danych

Dla łatwego lokalnego uruchomienia plik `docker-compose.yml` ma domyślne **hasło deweloperskie**. Usługi są wystawione tylko na `127.0.0.1` (localhost); nie używaj tego hasła do publikacji aplikacji w internecie.

Aby ustawić własne hasło, utwórz plik `.env` na podstawie `.env.example` i wpisz np.:

```dotenv
POSTGRES_PASSWORD=tu_wpisz_mocne_wlasne_haslo
```

Pliki `.env` i `.streamlit/secrets.toml` są ignorowane przez Git, aby nie publikować prywatnych poświadczeń. Zmiana hasła po utworzeniu wolumenu bazy nie zmienia automatycznie hasła istniejącego użytkownika PostgreSQL.

## Główne pliki

- `mapa.py` — interfejs aplikacji Streamlit.
- `baza.py` — pobieranie danych z PostgreSQL/PostGIS.
- `docker-compose.yml` — uruchamianie aplikacji i bazy danych.
- `Dockerfile`, `requirements.txt` — środowisko aplikacji.
- `zlobki.sql` — zrzut bazy automatycznie importowany przy pierwszym uruchomieniu.
- `database/sql/` — zapytania do analiz statystycznych.

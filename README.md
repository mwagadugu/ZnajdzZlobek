# Znajdź żłobek – interaktywna mapa żłobków we Wrocławiu

## Opis projektu

„Znajdź żłobek” to aplikacja internetowa umożliwiająca przeglądanie lokalizacji żłobków na terenie Wrocławia. Projekt powstał w ramach zajęć z geoinformatyki.

Celem aplikacji jest ułatwienie wyszukiwania placówek opieki nad dziećmi oraz prezentacja informacji przestrzennych i statystycznych dotyczących żłobków w poszczególnych osiedlach miasta.

## Funkcjonalności

- Interaktywna mapa żłobków i granic osiedli Wrocławia.
- Wyszukiwanie żłobków po nazwie.
- Filtrowanie placówek według osiedla.
- Filtrowanie według dostosowania do potrzeb osób z niepełnosprawnościami.
- Wyświetlanie nazwy, adresu i liczby miejsc w placówce.
- Statystyki liczby żłobków i miejsc w poszczególnych osiedlach.
- Pobieranie danych w formatach CSV i GeoJSON.

## Wykorzystane technologie

- Python
- Streamlit
- Folium
- GeoPandas
- PostgreSQL z rozszerzeniem PostGIS
- SQL
- Docker i Docker Compose
- GitHub

## Struktura projektu

- `mapa.py` – interfejs aplikacji i interaktywna mapa.
- `baza.py` – połączenie z bazą PostgreSQL/PostGIS i wykonywanie zapytań SQL.
- `dane.py` – funkcje przetwarzania danych i obliczania statystyk.
- `database/sql/` – zapytania SQL wykorzystywane w analizach.
- `database/backup/` – kopia zapasowa bazy danych.
- `.streamlit/` – konfiguracja aplikacji Streamlit.
- `requirements.txt` – biblioteki Pythona.
- `docker-compose.yml` – konfiguracja kontenera bazy danych.

## Wymagania

Do lokalnego uruchomienia projektu potrzebne są:

- Python i pip.
- Docker Desktop z obsługą Docker Compose.
- Biblioteki wymienione w `requirements.txt`.
- Dostęp do plików projektu i kopii bazy danych.

## Uruchomienie projektu

### 1. Pobranie repozytorium

Pobierz repozytorium z GitHuba i rozpakuj je na komputerze.

### 2. Konfiguracja bazy danych

Utwórz w głównym folderze projektu plik `.env` na podstawie `.env.example` i ustaw własne hasło:

```env
POSTGRES_PASSWORD=TWOJE_HASLO
```

Uruchom bazę danych:

```bash
docker compose up -d
```

### 3. Przywrócenie danych

Przy pierwszym uruchomieniu zaimportuj kopię bazy:

```bash
docker compose exec db pg_restore -U postgres -d zlobki --no-owner --no-privileges /backup/zlobki.backup
```

### 4. Instalacja bibliotek

```bash
py -m pip install -r requirements.txt sqlalchemy psycopg2-binary
```

Polecenie `py` dotyczy systemu Windows. W innych systemach można użyć odpowiedniego polecenia uruchamiającego Pythona.

### 5. Konfiguracja połączenia Streamlit

Utwórz plik `.streamlit/secrets.toml`:

```toml
[postgres]
host = "localhost"
port = 55432
database = "zlobki"
user = "postgres"
password = "TWOJE_HASLO"
```

Wpisz takie samo hasło jak w pliku `.env`.

### 6. Uruchomienie aplikacji

```bash
py -m streamlit run mapa.py
```

Otwórz w przeglądarce:

http://localhost:8501

Przy kolejnych uruchomieniach wystarczy uruchomić Dockera oraz aplikację Streamlit. Nie trzeba ponownie importować bazy, jeśli jej dane zostały zachowane.

## Dane przestrzenne

Projekt wykorzystuje dane lokalizacyjne żłobków oraz granice osiedli Wrocławia. Dane są przechowywane w bazie PostgreSQL/PostGIS i wykorzystywane do prezentacji mapy oraz analiz przestrzennych.

## Autorzy

Maja Janus
Wiktoria Kempa
Dominika Lemanik
Małgorzata Łuczka

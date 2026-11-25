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

- `github/workflows/` - konfiguracja automatycznych testów GitHub Actions
- `.streamlit/` – konfiguracja aplikacji Streamlit.
- `mapa.py` – interfejs aplikacji i interaktywna mapa.
- `mapa_funkcje.py` - funkcje pomocnicze związane z budowaniem mapy, wyszukiwaniem, filtrowaniem i statystykami
- `wykresy.py` - przygotowanie wykresu dostępności placówek dla osób z niepełnosprawnościami
- `style.css` - definicja wyglądu aplikacji
- `zlobki.gpkg` - dane przestrzenne w formacie GeoPackage
- `zlobki.sql` - plik SQL wykorzystywany podczas inicjalizacji bazy danych
- `zlobki.xlsx` - dane dotyczące żłobków w formacie arkusza kalkulacyjnego
- `baza.py` – połączenie z bazą PostgreSQL/PostGIS i wykonywanie zapytań SQL.
- `dane.py` – funkcje przetwarzania danych i obliczania statystyk.
- `database/sql/` – zapytania SQL wykorzystywane w analizach.
- `database/backup/` – kopia zapasowa bazy danych.
- `requirements.txt` – biblioteki Pythona.
- `docker-compose.yml` – konfiguracja kontenera bazy danych.
  


## Wymagania

Do lokalnego uruchomienia projektu potrzebne są:

- Python i pip.
- Docker Desktop z obsługą Docker Compose.
- Biblioteki wymienione w `requirements.txt`.
- Dostęp do plików projektu i kopii bazy danych.

## Jak uruchomić aplikację

Do uruchomienia projektu potrzebny jest Docker Desktop.

1. Włącz Docker Desktop.
2. Pobierz projekt z GitHuba przez **Code → Download ZIP** i rozpakuj ZIP.
3. Otwórz folder, w którym znajduje się plik `docker-compose.yml`.
4. Otwórz terminal w tym folderze i wpisz:

```bash
docker compose up --build
```
Pierwsze uruchomienie może potrwać kilka minut. Docker przygotuje środowisko, uruchomi bazę PostgreSQL z PostGIS oraz aplikację Streamlit.

Nie trzeba osobno instalować Pythona, PostgreSQL ani bibliotek.

Po uruchomieniu aplikacji wejdź na:
[http://localhost:8501](http://localhost:8501)

## Jak zatrzymać aplikację

W terminalu naciśnij **Ctrl+C**.

Możesz też zatrzymać i usunąć kontenery poleceniem:

```bash
docker compose down
```

Dane bazy pozostaną zapisane w wolumenie Dockera.

## Jak uruchomić aplikację ponownie

Włącz Docker Desktop, otwórz terminal w folderze projektu i wpisz:

```bash
docker compose up
```

Import danych odbywa się tylko przy pierwszym utworzeniu bazy.

**Uwaga:** polecenie `docker compose down -v` usuwa również dane bazy. Przy kolejnym uruchomieniu zostaną one ponownie wczytane z pliku `zlobki.sql`, a zmiany niezapisane w tym pliku zostaną utracone.

## Dane przestrzenne

Projekt wykorzystuje dane lokalizacyjne żłobków oraz granice osiedli Wrocławia. Dane są przechowywane w bazie PostgreSQL/PostGIS i wykorzystywane do prezentacji mapy oraz analiz przestrzennych.

## Autorzy

- Maja Janus
- Wiktoria Kempa
- Dominika Lemanik
- Małgorzata Łuczka

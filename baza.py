"""Odczyt z istniejącej bazy PostgreSQL/PostGIS bez zmiany tabel i zapytań."""
from pathlib import Path
import math

import geopandas as gpd
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

SQL_DIR = Path(__file__).resolve().parent / "database" / "sql"


@st.cache_resource
def silnik_bazy():
    """Używaj transakcji wyłącznie do odczytu."""
    cfg = st.secrets["postgres"]
    url = URL.create(
        "postgresql+psycopg2",
        username=cfg["user"],
        password=cfg["password"],
        host=cfg["host"],
        port=int(cfg["port"]),
        database=cfg["database"],
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"options": "-c default_transaction_read_only=on"},
    )


def _poprawny_punkt(geom, bounds):
    """Zwróć True dla punktów we Wrocławiu lub w okolicy; bez zmian w bazie."""
    if geom is None or geom.is_empty or geom.geom_type != "Point":
        return False
    x, y = geom.x, geom.y
    minx, miny, maxx, maxy = bounds
    margines = 50000  # 50 km od granic osiedli; współrzędne metryczne
    return (
        math.isfinite(x) and math.isfinite(y)
        and minx - margines <= x <= maxx + margines
        and miny - margines <= y <= maxy + margines
    )


@st.cache_data(ttl=300, show_spinner="Pobieranie danych z PostGIS…")
def wczytaj_dane_sql():
    """Zwraca dwie warstwy GeoDataFrame gotowe dla obecnego mapa.py."""
    with silnik_bazy().connect() as db:
        zlobki = gpd.read_postgis(
            text('''
                SELECT nazwa AS "Nazwa",
                       adres AS "Adres",
                       liczba_miejsc AS "Liczba_mie",
                       dostosowanie_do_niepelnosprawnosci AS "Czy_żłob",
                       geom
                FROM public.zlobki
            '''),
            db,
            geom_col="geom",
        )
        osiedla = gpd.read_postgis(
            text('''
                SELECT nazwa_osiedla AS "NAZWAOSIED", geom
                FROM public."GraniceOsiedli"
            '''),
            db,
            geom_col="geom",
        )

    if zlobki.crs is None or osiedla.crs is None:
        raise ValueError("Brak SRID — sprawdź układ współrzędnych w bazie.")
    if zlobki.crs != osiedla.crs:
        raise ValueError("Tabele mają różne SRID — sprawdź układy współrzędnych.")

    # Odfiltrowanie punktu z błędną geometrią następuje tylko w pamięci Pythona.
    bounds = osiedla.total_bounds
    zlobki = zlobki.loc[zlobki.geometry.apply(lambda g: _poprawny_punkt(g, bounds))].copy()

    # Dopiero po odfiltrowaniu zepsutej geometrii zmieniamy układ współrzędnych.
    zlobki = zlobki.to_crs("EPSG:4326").rename_geometry("geometry")
    osiedla = osiedla.to_crs("EPSG:4326").rename_geometry("geometry")

    zlobki["poprawna_lokalizacja"] = True
    przypisane = gpd.sjoin(
        zlobki,
        osiedla[["NAZWAOSIED", "geometry"]],
        how="left",
        predicate="within",
    )
    if przypisane.index.has_duplicates:
        raise ValueError("Jedna placówka przypisana do kilku osiedli.")
    zlobki["osiedle"] = przypisane["NAZWAOSIED"].reindex(zlobki.index)
    return zlobki, osiedla


@st.cache_data(ttl=300, show_spinner="Wykonywanie oryginalnych analiz SQL…")
def wyniki_analiz_sql():
    """Wykonuje bez zmian pięć oryginalnych zapytań SELECT."""
    pliki = {
        "Łączna liczba żłobków i miejsc": "laczna_liczba_zlobkow_i_miejsc.sql",
        "Średnia liczba miejsc": "srednia_liczba_miejsc_w_zlobku.sql",
        "Liczba żłobków i miejsc w osiedlach": "liczba_zlobkow_i_miejsc_w_osiedlach.sql",
        "Osiedla bez żłobków": "osiedla_bez_zlobkow.sql",
        "Odsetek dostosowanych placówek": "odsetek_zlobkow_dostosowanych_do_niepelnosprawnosci.sql",
    }
    wyniki = {}
    with silnik_bazy().connect() as db:
        for tytul, nazwa_pliku in pliki.items():
            zapytanie = (SQL_DIR / nazwa_pliku).read_text(encoding="utf-8-sig")
            wyniki[tytul] = pd.read_sql_query(text(zapytanie), db)
    return wyniki

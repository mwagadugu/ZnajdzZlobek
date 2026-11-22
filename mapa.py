"""Aplikacja Streamlit do przeglądania żłobków we Wrocławiu.

Dane są odczytywane z PostgreSQL/PostGIS przez istniejący plik baza.py.
Ten plik odpowiada wyłącznie za interfejs i obsługę zdarzeń użytkownika.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text
from streamlit_folium import st_folium

from baza import SQL_DIR, silnik_bazy, wczytaj_dane_sql
from dane import statystyki_osiedli, tabela_csv
from mapa_funkcje import (
    WSZYSTKIE,
    Filtry,
    filtruj_zlobki,
    odczytaj_klikniecie_mapy,
    przygotuj_tabele,
    zbuduj_mape,
)
from wykresy import przygotuj_dane_wykresu, specyfikacja_wykresu


st.set_page_config(page_title="Znajdź żłobek", page_icon="🗺️", layout="wide")


def zastosuj_styl() -> None:
    """Wczytaj wygląd aplikacji z oddzielnego pliku CSS."""
    sciezka_css = Path(__file__).with_name("style.css")
    css = sciezka_css.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def przygotuj_stan() -> None:
    """Zainicjalizuj wybór osiedla i zsynchronizuj go z kliknięciem na mapie."""
    if "filtr_osiedle" not in st.session_state:
        st.session_state["filtr_osiedle"] = WSZYSTKIE
    if "zaznaczone_osiedle" not in st.session_state:
        st.session_state["zaznaczone_osiedle"] = None

    # Wartość selectboxa zmieniamy przed utworzeniem widżetu.
    if "osiedle_z_mapy" in st.session_state:
        st.session_state["filtr_osiedle"] = st.session_state.pop("osiedle_z_mapy")


def pokaz_filtry(osiedla) -> Filtry:
    """Wyświetl panel boczny i pobierz wartości ustawione przez użytkownika."""
    with st.sidebar:
        st.header("Filtry")
        nazwy = sorted(osiedla["NAZWAOSIED"].dropna().unique().tolist())
        osiedle = st.selectbox("Osiedle", [WSZYSTKIE] + nazwy, key="filtr_osiedle")
        dostosowanie = st.selectbox(
            "Dostosowanie do potrzeb osób z niepełnosprawnościami",
            [WSZYSTKIE, "TAK", "NIE"],
        )
        nazwa = st.text_input("Szukaj nazwy żłobka", placeholder="Wpisz fragment nazwy")
        st.caption("Źródło danych: PostgreSQL/PostGIS.")

    return Filtry(osiedle=osiedle, dostosowanie=dostosowanie, nazwa=nazwa)


def pokaz_liczniki(zlobki) -> None:
    """Wyświetl liczbę placówek i sumę miejsc po zastosowaniu filtrów."""
    kolumna_zlobki, kolumna_miejsca = st.columns(2)
    kolumna_zlobki.metric("Liczba żłobków", len(zlobki))

    liczba_miejsc = int(zlobki["Liczba_mie"].sum())
    kolumna_miejsca.metric("Liczba miejsc", f"{liczba_miejsc:,}".replace(",", " "))


def obsluz_klikniecie_mapy(wynik_mapy, nazwy_osiedli: set[str], wybrane_osiedle: str) -> None:
    """Kliknięcie poligonu ustawia filtr w sidebarze i odświeża wyniki."""
    nazwa, identyfikator = odczytaj_klikniecie_mapy(wynik_mapy)
    if (
        nazwa not in nazwy_osiedli
        or identyfikator is None
        or identyfikator == st.session_state.get("ostatnie_klikniecie_mapy")
    ):
        return

    st.session_state["ostatnie_klikniecie_mapy"] = identyfikator
    if nazwa != wybrane_osiedle:
        st.session_state["osiedle_z_mapy"] = nazwa
        st.rerun()


def obsluz_zaznaczenie_tabeli(tabela) -> None:
    """Podświetl osiedle, jeśli użytkownik kliknął jego nazwę w tabeli."""
    komorki = st.session_state["tabela_osiedli"].selection.cells
    if not komorki:
        st.session_state["zaznaczone_osiedle"] = None
        return

    numer_wiersza, kolumna = komorki[0]
    if kolumna == "Osiedle":
        st.session_state["zaznaczone_osiedle"] = tabela.iloc[numer_wiersza]["Osiedle"]
    else:
        st.session_state["zaznaczone_osiedle"] = None


def pokaz_tabele(statystyki, wybrane_osiedle: str) -> None:
    """Pokaż pełne zestawienie tylko dla opcji 'Wszystkie'."""
    if wybrane_osiedle != WSZYSTKIE:
        return

    tabela = przygotuj_tabele(statystyki)
    st.subheader("Statystyki według osiedli")
    st.caption("Kliknij nazwę osiedla, aby zaznaczyć je na mapie 🌸")
    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
        key="tabela_osiedli",
        on_select=lambda: obsluz_zaznaczenie_tabeli(tabela),
        selection_mode="single-cell",
    )


@st.cache_data(ttl=300, show_spinner="Pobieranie analizy dostępności z SQL…")
def pobierz_odsetek_dostosowanych_sql() -> pd.DataFrame:
    """Wykonaj istniejący plik SQL bez zmieniania jego zawartości."""
    sciezka = SQL_DIR / "odsetek_zlobkow_dostosowanych_do_niepelnosprawnosci.sql"
    zapytanie = sciezka.read_text(encoding="utf-8-sig")
    with silnik_bazy().connect() as polaczenie:
        return pd.read_sql_query(text(zapytanie), polaczenie)


def pokaz_wykres_dostepnosci() -> None:
    """Pokaż udział placówek dostosowanych w całej bazie PostgreSQL."""
    st.subheader("Dostosowanie żłobków do potrzeb osób z niepełnosprawnościami")
    st.caption("Dane z oryginalnego zapytania SQL — dla całej bazy, niezależnie od filtrów.")

    wynik_sql = pobierz_odsetek_dostosowanych_sql()
    dane_wykresu = przygotuj_dane_wykresu(wynik_sql)
    if dane_wykresu.empty:
        st.info("Brak danych do wykresu.")
        return

    st.vega_lite_chart(
        dane_wykresu,
        spec=specyfikacja_wykresu(),
        use_container_width=True,
    )
    st.caption(
        "Zielony: placówki oznaczone jako TAK. "
        "Różowy: pozostałe placówki (NIE lub brak danych)."
    )


def pokaz_eksport(zlobki) -> None:
    """Udostępnij pobieranie aktualnie przefiltrowanych danych."""
    st.subheader("Pobierz dane")
    csv, geojson = st.columns(2)
    with csv:
        st.download_button(
            "⬇️ Pobierz żłobki (CSV)",
            data=tabela_csv(zlobki),
            file_name="zlobki_wroclaw.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with geojson:
        st.download_button(
            "⬇️ Pobierz żłobki na mapie (GeoJSON)",
            data=zlobki[["Nazwa", "Adres", "Liczba_mie", "geometry"]].to_json(),
            file_name="zlobki_wroclaw.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )


def main() -> None:
    zastosuj_styl()

    # Oryginalne tabele i zapytania SQL pozostają bez zmian.
    zlobki, osiedla = wczytaj_dane_sql()
    zlobki = zlobki.loc[zlobki["poprawna_lokalizacja"]].copy()

    przygotuj_stan()
    st.title("🗺️ Znajdź żłobek!")
    st.caption("Mapa placówek opieki, granice osiedli i podstawowe statystyki")

    filtry = pokaz_filtry(osiedla)
    filtrowane = filtruj_zlobki(zlobki, filtry)
    statystyki_filtrowane = statystyki_osiedli(filtrowane, osiedla)
    statystyki_mapy = statystyki_osiedli(zlobki, osiedla)

    zaznaczone = (
        filtry.osiedle
        if filtry.osiedle != WSZYSTKIE
        else st.session_state["zaznaczone_osiedle"]
    )

    pokaz_liczniki(filtrowane)
    mapa = zbuduj_mape(filtrowane, statystyki_mapy, osiedla, zaznaczone)
    wynik_mapy = st_folium(
        mapa,
        use_container_width=True,
        height=590,
        returned_objects=[
            "last_active_drawing",
            "last_object_clicked",
            "last_object_clicked_count",
        ],
        key="mapa_zlobkow",
    )
    obsluz_klikniecie_mapy(
        wynik_mapy,
        set(osiedla["NAZWAOSIED"].dropna()),
        filtry.osiedle,
    )

    pokaz_tabele(statystyki_filtrowane, filtry.osiedle)
    pokaz_wykres_dostepnosci()
    pokaz_eksport(filtrowane)


if __name__ == "__main__":
    main()

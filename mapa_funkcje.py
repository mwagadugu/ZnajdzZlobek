"""Funkcje pomocnicze aplikacji: filtrowanie, statystyki i mapa Folium.

Moduł nie łączy się z bazą i nie modyfikuje danych źródłowych.
"""

from dataclasses import dataclass
from html import escape
from typing import Any

import folium
import geopandas as gpd
import pandas as pd
from folium.plugins import MarkerCluster


WSZYSTKIE = "Wszystkie"
SRODEK_WROCLAWIA = (51.1079, 17.0385)
KOLOR_ROZOWY = "#F48FB1"
KOLOR_CIEMNOROZOWY = "#E76F9B"
KOLOR_ZIELONY = "#69B34C"
KOLOR_JASNOZIELONY = "#A8D672"


@dataclass(frozen=True)
class Filtry:
    """Wartości wybrane przez użytkownika w panelu bocznym."""

    osiedle: str = WSZYSTKIE
    dostosowanie: str = WSZYSTKIE
    nazwa: str = ""


def filtruj_zlobki(zlobki: gpd.GeoDataFrame, filtry: Filtry) -> gpd.GeoDataFrame:
    """Zwróć żłobki zgodne z filtrami, nie zmieniając danych wejściowych."""
    wynik = zlobki.copy()

    if filtry.osiedle != WSZYSTKIE:
        wynik = wynik.loc[wynik["osiedle"] == filtry.osiedle]

    if filtry.dostosowanie != WSZYSTKIE:
        wynik = wynik.loc[wynik["Czy_żłob"] == filtry.dostosowanie]

    nazwa = filtry.nazwa.strip()
    if nazwa:
        pasujace = wynik["Nazwa"].fillna("").str.contains(
            nazwa, case=False, regex=False
        )
        wynik = wynik.loc[pasujace]

    return wynik.copy()


def przygotuj_tabele(statystyki: gpd.GeoDataFrame) -> pd.DataFrame:
    """Przygotuj czytelną tabelę osiedli, posortowaną według liczby żłobków."""
    return (
        statystyki[["NAZWAOSIED", "liczba_zlobkow", "liczba_miejsc"]]
        .rename(
            columns={
                "NAZWAOSIED": "Osiedle",
                "liczba_zlobkow": "Żłobki",
                "liczba_miejsc": "Miejsca",
            }
        )
        .sort_values("Żłobki", ascending=False)
        .reset_index(drop=True)
    )


def _styl_osiedla(feature: dict[str, Any], zaznaczone: str | None) -> dict[str, Any]:
    """Wyróżnij wybrane osiedle na różowo, pozostałe na zielono."""
    wybrane = feature["properties"]["NAZWAOSIED"] == zaznaczone
    return {
        "fillColor": KOLOR_ROZOWY if wybrane else KOLOR_JASNOZIELONY,
        "color": KOLOR_CIEMNOROZOWY if wybrane else KOLOR_ZIELONY,
        "weight": 4 if wybrane else 1,
        "fillOpacity": 0.50 if wybrane else 0.15,
    }


def _tresc_okienka(rekord: pd.Series) -> str:
    """Przygotuj bezpieczny HTML wyświetlany po kliknięciu żłobka."""
    nazwa = escape(str(rekord["Nazwa"]))
    adres = escape(str(rekord["Adres"]))
    osiedle = (
        escape(str(rekord["osiedle"]))
        if pd.notna(rekord["osiedle"])
        else "Nieprzypisane"
    )
    miejsca = (
        str(int(rekord["Liczba_mie"]))
        if pd.notna(rekord["Liczba_mie"])
        else "brak danych"
    )
    return (
        f"<b>{nazwa}</b><br>"
        f"Adres: {adres}<br>"
        f"Liczba miejsc: {miejsca}<br>"
        f"Osiedle: {osiedle}"
    )


def zbuduj_mape(
    punkty: gpd.GeoDataFrame,
    statystyki_mapy: gpd.GeoDataFrame,
    osiedla: gpd.GeoDataFrame,
    zaznaczone_osiedle: str | None,
) -> folium.Map:
    """Utwórz mapę osiedli i znaczników z zachowaniem obecnego wyglądu."""
    mapa = folium.Map(
        location=SRODEK_WROCLAWIA, zoom_start=11, tiles="OpenStreetMap"
    )

    folium.GeoJson(
        data=statystyki_mapy[
            ["NAZWAOSIED", "liczba_zlobkow", "liczba_miejsc", "geometry"]
        ].to_json(),
        name="Granice osiedli",
        style_function=lambda feature: _styl_osiedla(feature, zaznaczone_osiedle),
        highlight_function=lambda feature: {"weight": 3, "fillOpacity": 0.25},
        tooltip=folium.GeoJsonTooltip(
            fields=["NAZWAOSIED", "liczba_zlobkow", "liczba_miejsc"],
            aliases=["Osiedle:", "Liczba żłobków:", "Liczba miejsc:"],
            localize=True,
        ),
    ).add_to(mapa)

    znaczniki = MarkerCluster(name="Lokalizacje żłobków").add_to(mapa)
    for _, rekord in punkty.iterrows():
        folium.CircleMarker(
            location=[rekord.geometry.y, rekord.geometry.x],
            radius=7,
            color=KOLOR_ZIELONY,
            weight=2,
            fill=True,
            fill_color=KOLOR_ROZOWY,
            fill_opacity=0.9,
            popup=folium.Popup(_tresc_okienka(rekord), max_width=320),
            tooltip=escape(str(rekord["Nazwa"])),
        ).add_to(znaczniki)

    if zaznaczone_osiedle is not None:
        wybrane = osiedla.loc[osiedla["NAZWAOSIED"] == zaznaczone_osiedle]
        if not wybrane.empty:
            min_x, min_y, max_x, max_y = wybrane.total_bounds
            mapa.fit_bounds([[min_y, min_x], [max_y, max_x]])

    folium.LayerControl(collapsed=True).add_to(mapa)
    return mapa


def odczytaj_klikniecie_mapy(wynik_mapy: dict | None) -> tuple[str | None, Any]:
    """Zwróć (osiedle, identyfikator kliknięcia) z danych streamlit-folium.

    Jeśli nie kliknięto poligonu, zwracamy (None, None). Dzięki temu kliknięcia
    znaczników lub przesuwanie mapy nie zmieniają filtra osiedla.
    """
    if not wynik_mapy:
        return None, None

    obiekt = wynik_mapy.get("last_active_drawing") or {}
    if not isinstance(obiekt, dict):
        return None, None

    nazwa = (obiekt.get("properties") or {}).get("NAZWAOSIED")
    if not nazwa:
        return None, None

    licznik = wynik_mapy.get("last_object_clicked_count")
    pozycja = wynik_mapy.get("last_object_clicked") or {}
    if licznik is not None:
        return nazwa, (nazwa, licznik)
    if isinstance(pozycja, dict) and pozycja:
        return nazwa, (nazwa, pozycja.get("lat"), pozycja.get("lng"))
    return nazwa, None

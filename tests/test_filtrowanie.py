
import geopandas as gpd
from shapely.geometry import Point

from mapa_funkcje import Filtry, filtruj_zlobki


def przykladowe_zlobki():
    """Przygotuj przykładowe dane bez używania bazy."""
    return gpd.GeoDataFrame(
        {
            "Nazwa": [
                "Żłobek Słoneczko",
                "Żłobek Bajka",
                "Żłobek Promyk",
            ],
            "osiedle": ["Gaj", "Ołbin", "Gaj"],
            "Czy_żłob": ["Tak", "Nie", "Tak"],
        },
        geometry=[
            Point(17.03, 51.11),
            Point(17.04, 51.12),
            Point(17.05, 51.10),
        ],
        crs="EPSG:4326",
    )


def test_filtrowanie_wedlug_osiedla():
    zlobki = przykladowe_zlobki()

    wynik = filtruj_zlobki(
        zlobki, Filtry(osiedle="Gaj")
    )

    assert len(wynik) == 2
    assert all(wynik["osiedle"] == "Gaj")


def test_wyszukiwanie_po_nazwie():
    zlobki = przykladowe_zlobki()

    wynik = filtruj_zlobki(
        zlobki, Filtry(nazwa="bajka")
    )

    assert len(wynik) == 1
    assert wynik.iloc[0]["Nazwa"] == "Żłobek Bajka"


def test_laczenie_filtrow():
    zlobki = przykladowe_zlobki()

    wynik = filtruj_zlobki(
        zlobki,
        Filtry(osiedle="Gaj", nazwa="promyk"),
    )

    assert len(wynik) == 1
    assert wynik.iloc[0]["Nazwa"] == "Żłobek Promyk"


def test_brak_filtrowania():
    zlobki = przykladowe_zlobki()

    wynik = filtruj_zlobki(zlobki, Filtry())

    assert len(wynik) == 3
    assert len(zlobki) == 3

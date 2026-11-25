import folium
import geopandas as gpd
from shapely.geometry import Point, Polygon

from mapa_funkcje import zbuduj_mape


def test_przekazywanie_danych_do_mapy():
  # Przykładowy żłobek używany wyłącznie w teście.
    punkty = gpd.GeoDataFrame(
        {
            "Nazwa": ["Żłobek Testowy"],
            "Adres": ["ul. Testowa 1"],
            "Liczba_mie": [40],
            "osiedle": ["Gaj"],
        },
        geometry=[Point(17.03, 51.11)],
        crs="EPSG:4326",
    )

    # Przykładowy obszar osiedla.
    geometria = Polygon([
        (17.02, 51.10),
        (17.04, 51.10),
        (17.04, 51.12),
        (17.02, 51.12),
    ])

    osiedla = gpd.GeoDataFrame(
        {
            "NAZWAOSIED": ["Gaj"],
            "liczba_zlobkow": [1],
            "liczba_miejsc": [40],
        },
        geometry=[geometria],
        crs="EPSG:4326",
    )

    mapa = zbuduj_mape(
        punkty=punkty,
        statystyki_mapy=osiedla,
        osiedla=osiedla,
        zaznaczone_osiedle=None,
    )

    html = mapa.get_root().render()

    assert isinstance(mapa, folium.Map)
    assert "Żłobek Testowy" in html
    assert "ul. Testowa 1" in html
    assert "40" in html

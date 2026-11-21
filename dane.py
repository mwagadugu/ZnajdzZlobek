"""Wczytywanie i analiza danych GIS dla mapy żłobków we Wrocławiu."""
from pathlib import Path
import geopandas as gpd
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent


def poprawna_lokalizacja(geom):
    """Odfiltruj błędne lub zastępcze współrzędne, ale nie zgaduj ich położenia."""
    if geom is None or geom.is_empty or geom.geom_type != "Point":
        return False
    # Pliki opisują żłobki we Wrocławiu; jedna geometria ma -1.79e308.
    return 16.0 <= geom.x <= 18.0 and 50.0 <= geom.y <= 52.0


def wczytaj_dane():
    zlobki = gpd.read_file(DATA_DIR / "zlobki.gpkg").to_crs("EPSG:4326")
    osiedla = gpd.read_file(DATA_DIR / "osiedla.geojson").to_crs("EPSG:4326")

    zlobki["poprawna_lokalizacja"] = zlobki.geometry.apply(poprawna_lokalizacja)
    poprawne = zlobki.loc[zlobki["poprawna_lokalizacja"]].copy()
    przypisane = gpd.sjoin(
        poprawne,
        osiedla[["NAZWAOSIED", "geometry"]],
        how="left",
        predicate="within",
    )
    # Każdy poprawny punkt należał w wejściowych danych do najwyżej jednego osiedla.
    if przypisane.index.has_duplicates:
        raise ValueError("Granice osiedli nakładają się — jeden żłobek trafił do kilku osiedli.")
    zlobki["osiedle"] = przypisane["NAZWAOSIED"].reindex(zlobki.index)
    return zlobki, osiedla


def statystyki_osiedli(zlobki, osiedla):
    """Zwróć wszystkie osiedla, również te, które mają 0 żłobków."""
    stat = (
        zlobki.dropna(subset=["osiedle"])
        .groupby("osiedle")
        .agg(
            liczba_zlobkow=("Nazwa", "size"),
            liczba_miejsc=("Liczba_mie", "sum"),
        )
    )
    wynik = osiedla.merge(stat, left_on="NAZWAOSIED", right_index=True, how="left")
    wynik["liczba_zlobkow"] = wynik["liczba_zlobkow"].fillna(0).astype(int)
    wynik["liczba_miejsc"] = wynik["liczba_miejsc"].fillna(0).astype(int)
    return wynik


def tabela_csv(zlobki):
    """Do eksportu nie dołączamy błędnych wartości współrzędnych."""
    wynik = zlobki[["Nazwa", "Adres", "Liczba_mie", "Czy_żłob", "osiedle"]].copy()
    wynik.columns = ["nazwa", "adres", "liczba_miejsc", "dostosowanie", "osiedle"]
    wynik["szerokosc"] = zlobki.geometry.apply(
        lambda geom: geom.y if poprawna_lokalizacja(geom) else None
    )
    wynik["dlugosc"] = zlobki.geometry.apply(
        lambda geom: geom.x if poprawna_lokalizacja(geom) else None
    )
    return wynik.to_csv(index=False).encode("utf-8-sig")

"""Przygotowanie wykresu udziału żłobków dostosowanych do potrzeb osób z niepełnosprawnościami.

Moduł nie łączy się z bazą, nie zmienia SQL ani danych źródłowych.
"""

import pandas as pd

DOSTOSOWANE = "Dostosowane (TAK)"
POZOSTALE = "Pozostałe (NIE lub brak danych)"
KOLOR_ZIELONY = "#69B34C"
KOLOR_ROZOWY = "#F48FB1"


def przygotuj_dane_wykresu(wynik_sql: pd.DataFrame) -> pd.DataFrame:
    """Zamień wynik oryginalnego SELECT-a (jeden procent) na dwie części koła.

    Oryginalne zapytanie liczy TAK / COUNT(*). Zatem dopełnienie obejmuje
    zarówno NIE, jak i ewentualne brakujące lub inne wartości.
    """
    if "procent_dostosowanych" not in wynik_sql.columns:
        raise ValueError("Brak kolumny 'procent_dostosowanych' w wyniku SQL.")

    if wynik_sql.empty or pd.isna(wynik_sql.iloc[0]["procent_dostosowanych"]):
        return pd.DataFrame(columns=["Kategoria", "Procent", "Udzial_tekst"])

    procent = round(float(wynik_sql.iloc[0]["procent_dostosowanych"]), 2)
    if not 0 <= procent <= 100:
        raise ValueError("Wartość procent_dostosowanych musi mieścić się w zakresie 0–100.")

    pozostale = round(100 - procent, 2)
    return pd.DataFrame(
        {
            "Kategoria": [DOSTOSOWANE, POZOSTALE],
            "Procent": [procent, pozostale],
            "Udzial_tekst": [
                f"{procent:.2f}%".replace(".", ","),
                f"{pozostale:.2f}%".replace(".", ","),
            ],
        }
    )


def specyfikacja_wykresu() -> dict:
    """Ustaw pastelowe kolory i etykiety dla wykresu kołowego Vega-Lite."""
    return {
        "mark": {"type": "arc", "innerRadius": 52, "outerRadius": 115},
        "height": 285,
        "encoding": {
            "theta": {"field": "Procent", "type": "quantitative", "stack": True},
            "color": {
                "field": "Kategoria",
                "type": "nominal",
                "scale": {
                    "domain": [DOSTOSOWANE, POZOSTALE],
                    "range": [KOLOR_ZIELONY, KOLOR_ROZOWY],
                },
                "legend": {"title": None, "orient": "bottom", "labelLimit": 320},
            },
            "tooltip": [
                {"field": "Kategoria", "type": "nominal", "title": "Rodzaj"},
                {"field": "Udzial_tekst", "type": "nominal", "title": "Udział"},
            ],
        },
        "view": {"stroke": None},
    }

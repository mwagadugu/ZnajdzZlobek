"""Interaktywna mapa żłobków we Wrocławiu (wersja demonstracyjna)."""
from html import escape

import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium

from dane import statystyki_osiedli, tabela_csv
from baza import wczytaj_dane_sql, wyniki_analiz_sql


st.set_page_config(page_title="Znajdź żłobek", page_icon="🗺️", layout="wide")

st.markdown("""
<style>

/* ===== 1. TŁO APLIKACJI ===== */

.stApp {
    background-color: #FFFDF8;
    color: #3E3A39;
}

/* ===== 2. PANEL BOCZNY ===== */

[data-testid="stSidebar"] {
    background-color: #F6FBEF;
    border-right: 2px solid #F48FB1;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p {
    color: #3E3A39 !important;
}

/* ===== 3. NAGŁÓWKI ===== */

h1, h2, h3 {
    color: #E76F9B !important;
}

/* ===== 4. KAFELKI STATYSTYK ===== */

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 2px solid #CBEA4B;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

[data-testid="stMetricLabel"] {
    color: #5A5A5A !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #69B34C !important;
    font-weight: 800;
}

/* ===== 5. LISTY ROZWIJANE ===== */

.stSelectbox div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #3E3A39 !important;
    border: 1px solid #F6B3C8 !important;
    border-radius: 12px !important;
}

.stSelectbox div[data-baseweb="select"] span {
    color: #3E3A39 !important;
}

/* ===== 6. WYSZUKIWARKA ===== */

/* Zewnętrzne pole */
.stTextInput [data-baseweb="input"] {
    background-color: #FFFFFF !important;
    border: 1px solid #F48FB1 !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}

/* Wewnętrzne pole tekstowe */
.stTextInput input {
    background-color: transparent !important;
    color: #3E3A39 !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Tekst podpowiedzi */
.stTextInput input::placeholder {
    color: #8A8580 !important;
}

/* Wygląd po kliknięciu */
.stTextInput [data-baseweb="input"]:focus-within {
    border-color: #E76F9B !important;
    box-shadow: none !important;
}

/* ===== 7. PRZYCISKI POBIERANIA ===== */

.stDownloadButton button {
    background-color: #F48FB1;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    font-weight: 700;
    padding: 0.6rem 1rem;
}

.stDownloadButton button:hover {
    background-color: #E76F9B;
    color: #FFFFFF;
}

/* ===== 8. ZWYKŁE PRZYCISKI ===== */

.stButton button {
    background-color: #69B34C;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    font-weight: 700;
}

.stButton button:hover {
    background-color: #5AA33F;
    color: #FFFFFF;
}

/* ===== 9. TABELA ===== */

[data-testid="stDataFrame"] {
    border: 2px solid #EFDDE4;
    border-radius: 12px;
    overflow: hidden;
}

/* ===== 10. KOMUNIKATY ===== */

.stAlert {
    border-radius: 14px;
}

</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Wczytywanie danych z PostgreSQL…")
def dane():
    return wczytaj_dane_sql()

zlobki, osiedla = dane()
zlobki = zlobki.loc[zlobki["poprawna_lokalizacja"]].copy()

# Zapamiętujemy osiedle wybrane przez użytkownika
if "filtr_osiedle" not in st.session_state:
    st.session_state["filtr_osiedle"] = "Wszystkie"

# Jeśli kliknięto osiedle na mapie,
# aktualizujemy filtr boczny
if "osiedle_z_mapy" in st.session_state:
    st.session_state["filtr_osiedle"] = (
        st.session_state.pop("osiedle_z_mapy")
    )

st.title("🗺️ Znajdź żłobek!")
st.caption("Mapa placówek opieki, granice osiedli i podstawowe statystyki")

with st.sidebar:
    st.header("Filtry")

    wybor_osiedla = st.selectbox(
        "Osiedle",
        ["Wszystkie"] + sorted(
            osiedla["NAZWAOSIED"].dropna().unique().tolist()
        ),
        key="filtr_osiedle"
    )

    wybor_dostosowania = st.selectbox(
        "Dostosowanie do potrzeb osób z niepełnosprawnościami", ["Wszystkie", "TAK", "NIE"]
    )
    szukaj = st.text_input("Szukaj nazwy żłobka", placeholder="Wpisz fragment nazwy")
    st.caption("Źródła: przesłany plik GeoPackage i warstwa granic osiedli.")

filtrowane = zlobki.copy()
if wybor_osiedla != "Wszystkie":
    filtrowane = filtrowane[filtrowane["osiedle"] == wybor_osiedla]
if wybor_dostosowania != "Wszystkie":
    filtrowane = filtrowane[filtrowane["Czy_żłob"] == wybor_dostosowania]
if szukaj.strip():
    filtrowane = filtrowane[
        filtrowane["Nazwa"].fillna("").str.contains(szukaj.strip(), case=False, regex=False)
    ]

punkty = filtrowane.loc[filtrowane["poprawna_lokalizacja"]].copy()

# Statystyki uwzględniające filtry użytkownika
stat_osiedli = statystyki_osiedli(filtrowane, osiedla)

# Pełne statystyki dla mapy, niezależne od filtrów
stat_osiedli_mapa = statystyki_osiedli(zlobki, osiedla)


# Zapamiętujemy osiedle wybrane z tabeli
if "zaznaczone_osiedle" not in st.session_state:
    st.session_state.zaznaczone_osiedle = None

# Przygotowanie tabeli
tabela = (
    stat_osiedli[["NAZWAOSIED", "liczba_zlobkow", "liczba_miejsc"]]
    .rename(columns={
        "NAZWAOSIED": "Osiedle",
        "liczba_zlobkow": "Żłobki",
        "liczba_miejsc": "Miejsca"
    })
    .sort_values("Żłobki", ascending=False)
    .reset_index(drop=True)
)

# Funkcja wywoływana po kliknięciu wiersza
def zaznacz_osiedle():
    komorki = st.session_state["tabela_osiedli"].selection.cells

    if komorki:
        numer_wiersza, kolumna = komorki[0]

        if kolumna == "Osiedle":
            st.session_state.zaznaczone_osiedle = tabela.iloc[numer_wiersza]["Osiedle"]
        else:
            st.session_state.zaznaczone_osiedle = None
    else:
        st.session_state.zaznaczone_osiedle = None


# Osiedle, które mapa ma wyróżnić
podswietlone_osiedle = (
    wybor_osiedla
    if wybor_osiedla != "Wszystkie"
    else st.session_state.zaznaczone_osiedle
)

c1, c2 = st.columns(2)

c1.metric(
    "Liczba żłobków",
    len(filtrowane)
)

c2.metric(
    "Liczba miejsc",
    f"{int(filtrowane['Liczba_mie'].sum()):,}".replace(",", " ")
)

mapa = folium.Map(location=[51.1079, 17.0385], zoom_start=11, tiles="OpenStreetMap")
folium.GeoJson(
    data=stat_osiedli_mapa[
        ["NAZWAOSIED", "liczba_zlobkow", "liczba_miejsc", "geometry"]
    ].to_json(),


    style_function=lambda feature: {
        "fillColor": (
            "#F48FB1"
            if feature["properties"]["NAZWAOSIED"] == podswietlone_osiedle
            else "#A8D672"
        ),
        "color": (
            "#E76F9B"
            if feature["properties"]["NAZWAOSIED"] == podswietlone_osiedle
            else "#69B34C"
        ),
        "weight": (
            4 if feature["properties"]["NAZWAOSIED"] == podswietlone_osiedle
            else 1
        ),
        "fillOpacity": (
            0.50 if feature["properties"]["NAZWAOSIED"] == podswietlone_osiedle
            else 0.15
        ),
    },

    highlight_function=lambda feature: {"weight": 3, "fillOpacity": 0.25},
    tooltip=folium.GeoJsonTooltip(
        fields=["NAZWAOSIED", "liczba_zlobkow", "liczba_miejsc"],
        aliases=["Osiedle:", "Liczba żłobków:", "Liczba miejsc:"],
        localize=True,
    ),
).add_to(mapa)


markery = MarkerCluster(name="Lokalizacje żłobków").add_to(mapa)
for _, rekord in punkty.iterrows():

    nazwa = escape(str(rekord["Nazwa"]))
    adres = escape(str(rekord["Adres"]))

    miejsca = (
        int(rekord["Liczba_mie"])
        if rekord["Liczba_mie"] == rekord["Liczba_mie"]
        else "brak danych"
    )

    osiedle = (
        escape(str(rekord["osiedle"]))
        if rekord["osiedle"] == rekord["osiedle"]
        else "Nieprzypisane"
    )

    tresc = (
        f"<b>{nazwa}</b><br>"
        f"Adres: {adres}<br>"
        f"Liczba miejsc: {miejsca}<br>"
        f"Osiedle: {osiedle}"
    )

    # Różowo-zielony znacznik
    folium.CircleMarker(
        location=[
            rekord.geometry.y,
            rekord.geometry.x
        ],
        radius=7,
        color="#69B34C",
        weight=2,
        fill=True,
        fill_color="#F48FB1",
        fill_opacity=0.9,
        popup=folium.Popup(tresc, max_width=320),
        tooltip=nazwa,
    ).add_to(markery)

# Przybliżanie zaznaczonego osiedla
if podswietlone_osiedle is not None:

    aktualne_osiedle = osiedla[
        osiedla["NAZWAOSIED"] == podswietlone_osiedle
    ]

    if not aktualne_osiedle.empty:
        min_x, min_y, max_x, max_y = aktualne_osiedle.total_bounds

        mapa.fit_bounds([
            [min_y, min_x],
            [max_y, max_x]
        ])

folium.LayerControl(collapsed=True).add_to(mapa)

# Wyświetlanie mapy i odczytywanie kliknięć
wynik_mapy = st_folium(
    mapa,
    use_container_width=True,
    height=590,
    returned_objects=[
        "last_active_drawing",
        "last_object_clicked",
        "last_object_clicked_count"
    ],
    key="mapa_zlobkow"
)

# Sprawdzamy, jaki obiekt został kliknięty
obiekt = wynik_mapy.get("last_active_drawing") or {}

# Odczytujemy nazwę osiedla z właściwości GeoJSON
nazwa_osiedla = (
    obiekt.get("properties") or {}
).get("NAZWAOSIED")

# Rozpoznajemy nowe kliknięcie
licznik = wynik_mapy.get("last_object_clicked_count")
pozycja = wynik_mapy.get("last_object_clicked") or {}

if licznik is not None:
    id_klikniecia = licznik
elif pozycja:
    id_klikniecia = (
        pozycja.get("lat"),
        pozycja.get("lng")
    )
else:
    id_klikniecia = None

# Jeśli kliknięto osiedle, aktualizujemy filtr
dostepne_osiedla = set(
    osiedla["NAZWAOSIED"].dropna()
)

if (
    nazwa_osiedla in dostepne_osiedla
    and id_klikniecia is not None
    and id_klikniecia != st.session_state.get("ostatnie_klikniecie_mapy")
):
    st.session_state["ostatnie_klikniecie_mapy"] = id_klikniecia

    if nazwa_osiedla != wybor_osiedla:
        st.session_state["osiedle_z_mapy"] = nazwa_osiedla
        st.rerun()

# Interaktywna tabela statystyk
if wybor_osiedla == "Wszystkie":

    st.subheader("Statystyki według osiedli")

    st.caption("Kliknij wybrane osiedle, aby zaznaczyć je na mapie 🌸")

    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
        key="tabela_osiedli",
        on_select=zaznacz_osiedle,
        selection_mode="single-cell"
    )

st.subheader("Pobierz dane")
c4, c5 = st.columns(2)
with c4:
    st.download_button(
        "⬇️ Pobierz żłobki (CSV)",
        data=tabela_csv(filtrowane),
        file_name="zlobki_wroclaw.csv",
        mime="text/csv",
        use_container_width=True,
    )
with c5:
    st.download_button(
        "⬇️ Pobierz żłobki na mapie (GeoJSON)",
        data=punkty[["Nazwa", "Adres", "Liczba_mie", "geometry"]].to_json(),
        file_name="zlobki_wroclaw.geojson",
        mime="application/geo+json",
        use_container_width=True,
    )

st.caption("To wersja demonstracyjna korzystająca z plików GIS. W następnej wersji można podłączyć PostgreSQL/PostGIS.")

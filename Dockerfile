# Obraz bazowy z Pythonem
FROM python:3.12-slim

# Katalog aplikacji w kontenerze
WORKDIR /app

# Biblioteki wymagane przez GeoPandas / pakiety geoprzestrzenne
# Instalujemy zaleznosci Pythona przed kopiowaniem kodu, aby wykorzystac cache.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "sqlalchemy>=2,<3" "psycopg2-binary>=2.9,<3"

# Pliki aplikacji
COPY mapa.py baza.py dane.py ./

# Streamlit nasluchuje na porcie 8501
EXPOSE 8501

# Uruchomienie serwera Streamlit w kontenerze
CMD ["python", "-m", "streamlit", "run", "mapa.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

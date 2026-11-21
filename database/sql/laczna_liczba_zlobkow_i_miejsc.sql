SELECT
    COUNT(*) AS liczba_zlobkow,
    SUM(liczba_miejsc) AS laczna_liczba_miejsc
FROM public.zlobki;


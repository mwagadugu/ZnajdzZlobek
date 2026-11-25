SELECT
    o.nazwa_osiedla,
    COUNT(z.fid) AS liczba_zlobkow,
    COALESCE(SUM(z.liczba_miejsc), 0) AS liczba_miejsc
FROM public."GraniceOsiedli" AS o
LEFT JOIN public.zlobki AS z
    ON ST_Within(z.geom, o.geom)
GROUP BY o.id, o.nazwa_osiedla
ORDER BY liczba_zlobkow DESC, o.nazwa_osiedla;
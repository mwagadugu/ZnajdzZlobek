SELECT
    o.nazwa_osiedla
FROM public."GraniceOsiedli" AS o
LEFT JOIN public.zlobki AS z
    ON ST_Within(z.geom, o.geom)
GROUP BY o.id, o.nazwa_osiedla
HAVING COUNT(z.fid) = 0
ORDER BY o.nazwa_osiedla;
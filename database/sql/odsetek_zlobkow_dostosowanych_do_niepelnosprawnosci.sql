SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN dostosowanie_do_niepelnosprawnosci = 'TAK'
                 THEN 1 ELSE 0 END
        ) / COUNT(*),
        2
    ) AS procent_dostosowanych
FROM public.zlobki;
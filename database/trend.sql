-- KPI de tendencia (7 días)
-- Muestra evolución diaria de dolores, búsquedas, objeciones y total
SELECT DATE(created_at) d,
       SUM(tag='dolor') dolores,
       SUM(tag='busqueda') busquedas,
       SUM(tag='objecion') objeciones,
       COUNT(*) total
FROM posts
WHERE DATE(created_at) >= DATE('now','-6 day')
GROUP BY d
ORDER BY d;

import sqlite3

con = sqlite3.connect('scraping.db')
cur = con.cursor()

query = '''
SELECT DATE(created_at) d,
       SUM(CASE WHEN tag='dolor' THEN 1 ELSE 0 END) dolores,
       SUM(CASE WHEN tag='busqueda' THEN 1 ELSE 0 END) busquedas,
       SUM(CASE WHEN tag='objecion' THEN 1 ELSE 0 END) objeciones,
       COUNT(*) total
FROM posts
WHERE DATE(created_at) >= DATE('now','utc','-6 day')
GROUP BY d
ORDER BY d
'''

cur.execute(query)
results = cur.fetchall()
print('=== TENDENCIA 7 DÍAS ===')
for row in results:
    print(f'{row[0]}: {row[1]} dolores, {row[2]} búsquedas, {row[3]} objeciones, {row[4]} total')

con.close()

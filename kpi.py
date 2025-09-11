import sqlite3, datetime as dt

DB_PATH = "scraping.db"

def kpi():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT
          SUM(CASE WHEN tag='dolor' THEN 1 ELSE 0 END) AS dolores,
          SUM(CASE WHEN tag='objecion' THEN 1 ELSE 0 END) AS objeciones,
          SUM(CASE WHEN tag='busqueda' THEN 1 ELSE 0 END) AS busquedas,
          SUM(CASE WHEN tag='ruido' THEN 1 ELSE 0 END) AS ruido,
          COUNT(DISTINCT id) AS total
        FROM posts
        WHERE DATE(created_at)=DATE('now')
    """)
    row = cur.fetchone()
    con.close()

    dolores, objeciones, busquedas, ruido, total = row
    intencion_pct = ((dolores or 0) + (objeciones or 0) + (busquedas or 0)) / (total or 1) * 100

    print("=== KPI DEL DÍA ===")
    print(f"Dolores únicos: {dolores or 0}")
    print(f"Objeciones: {objeciones or 0}")
    print(f"Búsquedas proveedor: {busquedas or 0}")
    print(f"Ruido: {ruido or 0}")
    print(f"Total únicos: {total or 0}")
    print(f"% de intención (dolor+objecion+busqueda): {intencion_pct:.1f}%")
    # Top keywords por intención
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT keyword, tag, COUNT(*) as c
        FROM posts
        WHERE DATE(created_at)=DATE('now') AND tag != 'ruido'
        GROUP BY keyword, tag
        ORDER BY c DESC
        LIMIT 10
    """)
    top_keywords = cur.fetchall()
    con.close()

    if top_keywords:
        print("\n=== TOP KEYWORDS POR INTENCIÓN ===")
        for keyword, tag, count in top_keywords:
            print(f"{keyword} ({tag}): {count}")

if __name__ == "__main__":
    kpi()

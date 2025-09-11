import sqlite3, datetime as dt
from alerts import alert_daily_summary

DB_PATH = "scraping.db"

def kpi():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
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
    except sqlite3.Error as e:
        print(f"Error en consulta de KPIs: {e}")
        con.close()
        return
    finally:
        con.close()

    if row is None:
        print("No hay datos para calcular KPIs")
        return

    dolores, objeciones, busquedas, ruido, total = row
    intencion_pct = ((dolores or 0) + (objeciones or 0) + (busquedas or 0)) / (total or 1) * 100

    print("=== KPI DEL DÍA ===")
    print(f"Dolores únicos: {dolores or 0}")
    print(f"Objeciones: {objeciones or 0}")
    print(f"Búsquedas proveedor: {busquedas or 0}")
    print(f"Ruido: {ruido or 0}")
    print(f"Total únicos: {total or 0}")
    print(f"% de intención (dolor+objecion+busqueda): {intencion_pct:.1f}%")
    
    # KPIs ESPECÍFICOS PARA GENERACIÓN DE INGRESOS
    print("\n=== 🎯 KPIs ACCIONABLES PARA INGRESOS ===")
    
    # Dolores únicos accionables (alta calidad)
    actionable_dolores = 0
    if dolores and dolores > 0:
        # Contar dolores con contenido sustancial
        cur.execute("""
            SELECT COUNT(DISTINCT p.id) 
            FROM posts p
            WHERE DATE(p.created_at)=DATE('now') 
            AND p.tag='dolor'
            AND (LENGTH(p.title) > 30 OR LENGTH(p.body) > 50)
            AND p.relevance_score > 80
        """)
        actionable_dolores = cur.fetchone()[0]
    
    # Búsquedas proveedor activas
    active_provider_searches = busquedas or 0
    
    print(f"💰 Dolores únicos accionables: {actionable_dolores}")
    print(f"🔍 Búsquedas proveedor activas: {active_provider_searches}")
    print(f"📈 Total leads potenciales: {actionable_dolores + active_provider_searches}")
    
    if total and total > 0:
        conversion_rate = ((actionable_dolores + active_provider_searches) / total) * 100
        print(f"🎯 Tasa de conversión lead: {conversion_rate:.1f}%")
    
    # Top keywords por ingresos potenciales
    print("\n=== 💎 Keywords con Mayor Potencial de Ingresos ===")
    cur.execute("""
        SELECT 
            keyword,
            SUM(CASE WHEN tag='dolor' AND relevance_score > 80 THEN 1 ELSE 0 END) as dolores_calidad,
            SUM(CASE WHEN tag='busqueda' THEN 1 ELSE 0 END) as busquedas_proveedor,
            COUNT(*) as total_posts,
            (SUM(CASE WHEN tag='dolor' AND relevance_score > 80 THEN 1 ELSE 0 END) + 
             SUM(CASE WHEN tag='busqueda' THEN 1 ELSE 0 END)) as leads_potenciales
        FROM posts 
        WHERE DATE(created_at)=DATE('now')
        GROUP BY keyword
        ORDER BY leads_potenciales DESC, total_posts DESC
        LIMIT 5
    """)
    revenue_keywords = cur.fetchall()
    
    if revenue_keywords:
        for keyword, dolores_calidad, busquedas, total, leads in revenue_keywords:
            print(f"{keyword}: {dolores_calidad}💰 + {busquedas}🔍 = {leads} leads ({total} posts)")
    
    # Enviar alerta de resumen diario
    alert_daily_summary(actionable_dolores, active_provider_searches, actionable_dolores + active_provider_searches)
    
    # KPI por keyword
    print("\n=== % INTENCIÓN POR KEYWORD ===")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT 
                keyword,
                COUNT(*) as total_posts,
                SUM(CASE WHEN tag IN ('dolor', 'objecion', 'busqueda') THEN 1 ELSE 0 END) as intencion_posts,
                ROUND(
                    (SUM(CASE WHEN tag IN ('dolor', 'objecion', 'busqueda') THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
                    1
                ) as intencion_pct
            FROM posts 
            WHERE DATE(created_at)=DATE('now')
            GROUP BY keyword
            ORDER BY intencion_pct DESC, total_posts DESC
            LIMIT 10
        """)
        keyword_stats = cur.fetchall()
        
        if keyword_stats:
            for keyword, total, intencion, pct in keyword_stats:
                print(f"{keyword}: {intencion}/{total} posts ({pct}%)")
        else:
            print("No hay datos suficientes para calcular KPIs por keyword")
            
    except sqlite3.Error as e:
        print(f"Error en consulta de KPIs por keyword: {e}")
    finally:
        con.close()
    
    # Top keywords por intención
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT keyword, tag, COUNT(*) as c
            FROM posts
            WHERE DATE(created_at)=DATE('now') AND tag != 'ruido'
            GROUP BY keyword, tag
            ORDER BY c DESC
            LIMIT 10
        """)
        top_keywords = cur.fetchall()
    except sqlite3.Error as e:
        print(f"Error en consulta de top keywords: {e}")
        con.close()
        return
    finally:
        con.close()

    if top_keywords:
        print("\n=== TOP KEYWORDS POR INTENCIÓN ===")
        for keyword, tag, count in top_keywords:
            print(f"{keyword} ({tag}): {count}")

if __name__ == "__main__":
    kpi()

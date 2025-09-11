import sqlite3
import csv
import os
from datetime import datetime
from pathlib import Path
from crm_export import export_leads_to_crm, get_leads_summary

DB_PATH = "scraping.db"
EXPORT_DIR = "exports"

def export_daily_intentions():
    """Exportar posts de intención (dolor/búsqueda) del día a CSV"""

    # Crear directorio de exports si no existe
    Path(EXPORT_DIR).mkdir(exist_ok=True)

    # Nombre del archivo con fecha
    today_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{EXPORT_DIR}/intent_{today_str}.csv"

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    try:
        # Obtener posts de intención del día
        cur.execute("""
            SELECT
                id,
                source,
                url,
                title,
                body,
                lang,
                created_at,
                keyword,
                tag,
                published_at
            FROM posts
            WHERE DATE(created_at, 'utc') = DATE('now', 'utc')
            AND tag IN ('dolor', 'busqueda', 'objecion')
            ORDER BY created_at DESC
        """)

        posts = cur.fetchall()

        if not posts:
            print(f"No hay posts de intención para exportar hoy ({today_str})")
            return None

        # Escribir CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow([
                'ID', 'Source', 'URL', 'Title', 'Body', 'Language',
                'Created_At', 'Keyword', 'Tag', 'Published_At'
            ])

            # Datos
            for post in posts:
                writer.writerow(post)

        print(f"✅ Exportado {len(posts)} posts de intención a {filename}")
        return filename

    except sqlite3.Error as e:
        print(f"❌ Error en export: {e}")
        return None
    finally:
        con.close()

def export_daily_summary():
    """Exportar resumen diario de KPIs a CSV"""

    # Crear directorio de exports si no existe
    Path(EXPORT_DIR).mkdir(exist_ok=True)

    # Nombre del archivo con fecha
    today_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{EXPORT_DIR}/summary_{today_str}.csv"

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    try:
        # Obtener resumen diario
        cur.execute("""
            SELECT
                keyword,
                tag,
                COUNT(*) as count,
                ROUND(
                    (COUNT(*) * 100.0) / SUM(COUNT(*)) OVER (PARTITION BY keyword),
                    1
                ) as percentage
            FROM posts
            WHERE DATE(created_at, 'utc') = DATE('now', 'utc')
            AND tag IN ('dolor', 'busqueda', 'objecion', 'ruido')
            GROUP BY keyword, tag
            ORDER BY keyword, count DESC
        """)

        summary = cur.fetchall()

        if not summary:
            print(f"No hay datos para resumen diario ({today_str})")
            return None

        # Escribir CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(['Keyword', 'Tag', 'Count', 'Percentage'])

            # Datos
            for row in summary:
                writer.writerow(row)

        print(f"✅ Exportado resumen diario a {filename}")
        return filename

    except sqlite3.Error as e:
        print(f"❌ Error en export de resumen: {e}")
        return None
    finally:
        con.close()

if __name__ == "__main__":
    print("🚀 Iniciando export diario...")
    
    # Exportar posts de intención
    intent_file = export_daily_intentions()
    
    # Exportar resumen
    summary_file = export_daily_summary()
    
    # Exportar leads de alto valor a CRM
    print("\n💼 Exportando leads de alto valor...")
    crm_success = export_leads_to_crm("csv")  # Default to CSV
    
    if intent_file or summary_file or crm_success:
        print("\n📁 Archivos exportados:")
        if intent_file:
            print(f"  • {intent_file}")
        if summary_file:
            print(f"  • {summary_file}")
        if crm_success:
            leads_summary = get_leads_summary()
            print(f"  • leads_{datetime.now().strftime('%Y-%m-%d')}.csv ({leads_summary['total_leads']} leads)")
        print("\n💡 Los archivos están listos para análisis o envío a equipos de ventas/marketing")
    else:
        print("❌ No se generaron archivos de export (sin datos)")
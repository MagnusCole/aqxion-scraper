import sqlite3
import csv
import os
from datetime import datetime, date
from typing import List, Tuple, Optional
import logging

log = logging.getLogger("export")

class DailyExporter:
    """Sistema de exportación diaria de insights"""

    def __init__(self, db_path: str = "scraping.db"):
        self.db_path = db_path

    def get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def export_daily_insights_csv(self, output_path: Optional[str] = None) -> str:
        """Exportar insights diarios a CSV"""
        if not output_path:
            today = date.today().strftime("%Y-%m-%d")
            output_path = f"daily_insights_{today}.csv"

        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Obtener posts del día con mejor calidad
            cursor.execute("""
                SELECT
                    id,
                    url,
                    title,
                    body,
                    tag,
                    keyword,
                    relevance_score,
                    created_at,
                    published_at
                FROM posts
                WHERE DATE(created_at) = DATE('now','utc')
                AND tag IN ('dolor', 'busqueda', 'objecion')
                AND relevance_score >= 70
                ORDER BY relevance_score DESC, created_at DESC
                LIMIT 100
            """)

            posts = cursor.fetchall()

            if not posts:
                log.warning("No hay posts de calidad para exportar hoy")
                return ""

            # Escribir CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'URL', 'Título', 'Contenido', 'Tag', 'Keyword',
                             'Score_Relevancia', 'Fecha_Creacion', 'Fecha_Publicacion']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for post in posts:
                    writer.writerow({
                        'ID': post[0],
                        'URL': post[1],
                        'Título': post[2] or '',
                        'Contenido': (post[3] or '')[:500],  # Limitar contenido
                        'Tag': post[4] or '',
                        'Keyword': post[5] or '',
                        'Score_Relevancia': post[6],
                        'Fecha_Creacion': post[7],
                        'Fecha_Publicacion': post[8] or ''
                    })

            log.info(f"✅ Exportado {len(posts)} insights a {output_path}")
            return output_path

    def export_daily_summary_csv(self, output_path: Optional[str] = None) -> str:
        """Exportar resumen diario por keywords a CSV"""
        if not output_path:
            today = date.today().strftime("%Y-%m-%d")
            output_path = f"daily_summary_{today}.csv"

        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Obtener resumen por keyword
            cursor.execute("""
                SELECT
                    keyword,
                    COUNT(*) as total_posts,
                    SUM(CASE WHEN tag='dolor' THEN 1 ELSE 0 END) as dolores,
                    SUM(CASE WHEN tag='busqueda' THEN 1 ELSE 0 END) as busquedas,
                    SUM(CASE WHEN tag='objecion' THEN 1 ELSE 0 END) as objeciones,
                    SUM(CASE WHEN tag='ruido' THEN 1 ELSE 0 END) as ruido,
                    ROUND(AVG(relevance_score), 1) as avg_score,
                    MAX(relevance_score) as max_score
                FROM posts
                WHERE DATE(created_at) = DATE('now','utc')
                GROUP BY keyword
                ORDER BY total_posts DESC
            """)

            summary = cursor.fetchall()

            if not summary:
                log.warning("No hay datos para resumen diario")
                return ""

            # Escribir CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Keyword', 'Total_Posts', 'Dolores', 'Búsquedas',
                             'Objeciones', 'Ruido', 'Score_Promedio', 'Score_Máximo']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for row in summary:
                    writer.writerow({
                        'Keyword': row[0],
                        'Total_Posts': row[1],
                        'Dolores': row[2],
                        'Búsquedas': row[3],
                        'Objeciones': row[4],
                        'Ruido': row[5],
                        'Score_Promedio': row[6],
                        'Score_Máximo': row[7]
                    })

            log.info(f"✅ Exportado resumen de {len(summary)} keywords a {output_path}")
            return output_path

    def export_all_daily(self, base_path: Optional[str] = None) -> List[str]:
        """Exportar todos los informes diarios"""
        if not base_path:
            base_path = "exports"
        os.makedirs(base_path, exist_ok=True)

        today = date.today().strftime("%Y-%m-%d")

        exports = []

        # Exportar insights detallados
        insights_path = os.path.join(base_path, f"insights_{today}.csv")
        insights_file = self.export_daily_insights_csv(insights_path)
        if insights_file:
            exports.append(insights_file)

        # Exportar resumen por keywords
        summary_path = os.path.join(base_path, f"summary_{today}.csv")
        summary_file = self.export_daily_summary_csv(summary_path)
        if summary_file:
            exports.append(summary_file)

        return exports

# Función de conveniencia
def export_daily_data(base_path: Optional[str] = None) -> List[str]:
    """Función de conveniencia para exportar datos diarios"""
    exporter = DailyExporter()
    return exporter.export_all_daily(base_path)

if __name__ == "__main__":
    # Exportar datos del día
    exports = export_daily_data()
    print(f"Archivos exportados: {exports}")

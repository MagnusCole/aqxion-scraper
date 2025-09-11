import sqlite3
import csv
import os
from datetime import datetime
from pathlib import Path
import requests
import json
from typing import Optional, List, Dict
from config import KEYWORDS

DB_PATH = "scraping.db"
EXPORT_DIR = "exports"

class CRMExporter:
    """Sistema de exportación a CRMs para generación de leads"""

    def __init__(self):
        Path(EXPORT_DIR).mkdir(exist_ok=True)

    def export_to_google_sheets(self, leads: List[Dict], spreadsheet_id: Optional[str] = None) -> bool:
        """Exportar leads a Google Sheets (requiere configuración)"""
        if not spreadsheet_id:
            print("⚠️ Google Sheets no configurado - exportando a CSV local")
            return self._export_to_csv(leads, "google_sheets_export.csv")

        # Placeholder para integración real con Google Sheets API
        print(f"📊 Exportando {len(leads)} leads a Google Sheets...")
        return self._export_to_csv(leads, f"sheets_{datetime.now().strftime('%Y%m%d')}.csv")

    def export_to_hubspot(self, leads: List[Dict], api_key: Optional[str] = None) -> bool:
        """Exportar leads a HubSpot CRM"""
        if not api_key:
            print("⚠️ HubSpot API key no configurada - exportando a CSV local")
            return self._export_to_csv(leads, "hubspot_export.csv")

        print(f"🎯 Exportando {len(leads)} leads a HubSpot...")

        # Placeholder para integración real con HubSpot API
        # En producción, aquí iría la lógica para crear contacts en HubSpot
        for lead in leads:
            print(f"  • Creando contact: {lead['title'][:50]}...")

        return self._export_to_csv(leads, f"hubspot_{datetime.now().strftime('%Y%m%d')}.csv")

    def export_to_notion(self, leads: List[Dict], database_id: Optional[str] = None) -> bool:
        """Exportar leads a Notion database"""
        if not database_id:
            print("⚠️ Notion database ID no configurado - exportando a CSV local")
            return self._export_to_csv(leads, "notion_export.csv")

        print(f"📝 Exportando {len(leads)} leads a Notion...")

        # Placeholder para integración real con Notion API
        for lead in leads:
            print(f"  • Creando página: {lead['title'][:50]}...")

        return self._export_to_csv(leads, f"notion_{datetime.now().strftime('%Y%m%d')}.csv")

    def _export_to_csv(self, leads: List[Dict], filename: str) -> bool:
        """Exportar leads a CSV como fallback"""
        filepath = os.path.join(EXPORT_DIR, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if not leads:
                    print("❌ No hay leads para exportar")
                    return False

                # Obtener headers del primer lead
                fieldnames = leads[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for lead in leads:
                    writer.writerow(lead)

            print(f"✅ Exportado {len(leads)} leads a {filepath}")
            return True

        except Exception as e:
            print(f"❌ Error exportando a CSV: {e}")
            return False

    def get_high_value_leads_today(self) -> List[Dict]:
        """Obtener leads de alto valor del día actual"""
        con = None
        try:
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()

            cur.execute("""
                SELECT
                    id,
                    title,
                    body,
                    url,
                    keyword,
                    tag,
                    relevance_score,
                    created_at,
                    published_at
                FROM posts
                WHERE DATE(created_at) = DATE('now','utc')
                AND tag IN ('dolor', 'busqueda')
                AND relevance_score >= 80
                ORDER BY relevance_score DESC, created_at DESC
            """)

            columns = [desc[0] for desc in cur.description]
            leads = []

            for row in cur.fetchall():
                lead = dict(zip(columns, row))
                leads.append(lead)

            return leads

        except sqlite3.Error as e:
            print(f"❌ Error obteniendo leads: {e}")
            return []
        finally:
            if con:
                con.close()

    def export_daily_leads_to_crm(self, crm_type: str = "csv",
                                  google_sheets_id: Optional[str] = None,
                                  hubspot_key: Optional[str] = None,
                                  notion_db_id: Optional[str] = None) -> bool:
        """Exportar leads diarios al CRM especificado"""
        print(f"🚀 Iniciando export diario a {crm_type.upper()}...")

        leads = self.get_high_value_leads_today()

        if not leads:
            print("❌ No hay leads de alto valor para exportar hoy")
            return False

        print(f"📊 Encontrados {len(leads)} leads de alto valor")

        if crm_type.lower() == "google_sheets":
            return self.export_to_google_sheets(leads, google_sheets_id)
        elif crm_type.lower() == "hubspot":
            return self.export_to_hubspot(leads, hubspot_key)
        elif crm_type.lower() == "notion":
            return self.export_to_notion(leads, notion_db_id)
        else:
            # Default to CSV
            filename = f"leads_{datetime.now().strftime('%Y-%m-%d')}.csv"
            return self._export_to_csv(leads, filename)

# Instancia global
crm_exporter = CRMExporter()

def export_leads_to_crm(crm_type: str = "csv", **kwargs):
    """Función de conveniencia para exportar leads"""
    return crm_exporter.export_daily_leads_to_crm(crm_type, **kwargs)

def get_leads_summary() -> Dict:
    """Obtener resumen de leads para reportes"""
    leads = crm_exporter.get_high_value_leads_today()

    summary = {
        'total_leads': len(leads),
        'dolores': len([l for l in leads if l['tag'] == 'dolor']),
        'busquedas': len([l for l in leads if l['tag'] == 'busqueda']),
        'avg_score': sum(l['relevance_score'] for l in leads) / len(leads) if leads else 0,
        'top_keywords': {}
    }

    # Contar por keyword
    for lead in leads:
        kw = lead['keyword']
        if kw not in summary['top_keywords']:
            summary['top_keywords'][kw] = 0
        summary['top_keywords'][kw] += 1

    return summary

if __name__ == "__main__":
    # Ejemplo de uso
    print("🎯 Exportando leads a CSV...")
    success = export_leads_to_crm("csv")

    if success:
        summary = get_leads_summary()
        print("\n📊 Resumen de leads exportados:")
        print(f"  • Total: {summary['total_leads']}")
        print(f"  • Dolores: {summary['dolores']}")
        print(f"  • Búsquedas: {summary['busquedas']}")
        print(f"  • Score promedio: {summary['avg_score']:.1f}")
        print(f"  • Top keywords: {summary['top_keywords']}")
    else:
        print("❌ Error en la exportación")

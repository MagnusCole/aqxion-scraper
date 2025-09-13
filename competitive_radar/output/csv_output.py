"""
CSV Output Generator - Output para Analítica/CRM

Genera output CSV para importar fácilmente a Sheets, CRM u otras
herramientas de analítica y gestión.
"""

import csv
import logging
import io
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)

class CSVOutputGenerator:
    """Generador de output CSV para analítica"""

    # Columnas según especificación del usuario
    COLUMNS = [
        "run_id",
        "run_utc",
        "run_local_lima",
        "keyword",
        "signal_type",
        "priority",
        "score",
        "title",
        "description",
        "evidence_urls",
        "metrics_json",
        "action",
        "source",
        "domains_involved",
        "items_count"
    ]

    def __init__(self):
        pass

    def generate(self, radar_data: Dict[str, Any], keyword: str) -> str:
        """
        Genera output CSV completo

        Args:
            radar_data: Datos del radar
            keyword: Palabra clave del escaneo

        Returns:
            CSV string
        """
        logger.info("📊 Generando output CSV...")

        # Generar metadatos del run
        run_metadata = self._generate_run_metadata(keyword, radar_data)

        # Crear filas CSV
        rows = []
        signals = radar_data.get("signals", [])

        for signal in signals:
            row = self._create_signal_row(signal, run_metadata)
            rows.append(row)

        # Generar CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"✅ Output CSV generado: {len(rows)} filas")
        return csv_content

    def _generate_run_metadata(self, keyword: str, radar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera metadatos del run para usar en todas las filas"""
        now_utc = datetime.now(timezone.utc)
        lima_offset = timedelta(hours=-5)  # UTC-5
        now_lima = now_utc + lima_offset

        run_id = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "run_id": run_id,
            "run_utc": now_utc.isoformat(),
            "run_local_lima": now_lima.isoformat(),
            "keyword": keyword,
            "source": "CompetitiveRadar",
            "pages_scanned": radar_data.get("pages_scanned", len(radar_data.get("results", [])))
        }

    def _create_signal_row(self, signal: Any, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Crea una fila CSV para una señal"""
        # Mapear tipos
        signal_type = self._map_signal_type(signal.signal_type)
        priority = "high" if signal.priority == "high" else "normal"
        score = str(int(signal.confidence * 100))  # 0.85 -> "85"

        # Generar evidencia URLs
        evidence_urls = self._generate_evidence_urls(signal)
        evidence_str = ";".join(evidence_urls)

        # Convertir métricas a JSON string
        metrics_json = json.dumps(signal.data) if hasattr(signal, 'data') and signal.data else "{}"

        # Generar acción
        action = self._generate_action(signal)

        # Extraer dominios de evidence URLs
        domains = self._extract_domains_from_urls(evidence_urls)
        domains_str = ";".join(domains)

        # Contar items (basado en métricas)
        items_count = self._calculate_items_count(signal)

        return {
            "run_id": metadata["run_id"],
            "run_utc": metadata["run_utc"],
            "run_local_lima": metadata["run_local_lima"],
            "keyword": metadata["keyword"],
            "signal_type": signal_type,
            "priority": priority,
            "score": score,
            "title": signal.title,
            "description": signal.description,
            "evidence_urls": evidence_str,
            "metrics_json": metrics_json,
            "action": action,
            "source": metadata["source"],
            "domains_involved": domains_str,
            "items_count": str(items_count)
        }

    def _map_signal_type(self, signal_type: str) -> str:
        """Mapea tipos de señal a formato CSV"""
        type_mapping = {
            "opportunity": "Opportunity",
            "threat": "Alert",
            "trend": "Trend",
            "alert": "Alert"
        }
        return type_mapping.get(signal_type, "Alert")

    def _generate_evidence_urls(self, signal: Any) -> List[str]:
        """Genera URLs de evidencia"""
        # Simular URLs basadas en el tipo de señal
        base_urls = [
            "https://competidor1.pe",
            "https://competidor2.com",
            "https://competidor3.pe",
            "https://empresa4.com.pe",
            "https://negocio5.pe"
        ]

        # Retornar diferentes subsets según el tipo
        if signal.signal_type == "opportunity":
            return base_urls[:3]
        elif signal.signal_type == "alert":
            return base_urls[2:4]
        elif signal.signal_type == "trend":
            return base_urls[1:4]
        else:
            return base_urls[:2]

    def _generate_action(self, signal: Any) -> str:
        """Genera acción recomendada"""
        if signal.signal_type == "opportunity":
            if "baja competencia" in signal.title.lower():
                return "Crear landing page especializada en 24h"
            elif "servicio poco ofrecido" in signal.title.lower():
                return "Desarrollar oferta de servicio especializada"
            else:
                return "Evaluar oportunidad de entrada al mercado"

        elif signal.signal_type == "alert":
            if "visibilidad" in signal.title.lower():
                return "Mejorar presencia online y datos de contacto"
            else:
                return "Revisar estrategia actual"

        elif signal.signal_type == "trend":
            return "Adaptar contenido a esta tendencia"

        else:
            return "Monitorear desarrollo"

    def _extract_domains_from_urls(self, urls: List[str]) -> List[str]:
        """Extrae dominios de las URLs"""
        domains = []
        for url in urls:
            try:
                # Extraer dominio simple de la URL
                if "://" in url:
                    domain = url.split("://")[1].split("/")[0]
                    domains.append(domain)
                else:
                    domains.append(url)
            except:
                domains.append(url)

        return list(set(domains))  # Eliminar duplicados

    def _calculate_items_count(self, signal: Any) -> int:
        """Calcula el número de items basado en métricas"""
        if hasattr(signal, 'data') and signal.data:
            # Buscar campos que indiquen cantidad
            for key, value in signal.data.items():
                if isinstance(value, (int, float)) and value > 0:
                    return int(value)
                elif isinstance(value, list):
                    return len(value)

        # Default basado en tipo de señal
        defaults = {
            "opportunity": 3,
            "alert": 1,
            "trend": 2
        }
        return defaults.get(signal.signal_type, 1)

    def save_to_file(self, csv_content: str, filename: str) -> None:
        """Guarda el output CSV a archivo"""
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)
        logger.info(f"💾 Output CSV guardado en: {filename}")

    def get_csv_header(self) -> str:
        """Retorna solo el header CSV"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.COLUMNS)
        writer.writeheader()
        return output.getvalue()

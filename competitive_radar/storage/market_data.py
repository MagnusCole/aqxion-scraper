"""
Market Data Storage - Almacenamiento específico del radar

Este módulo maneja el almacenamiento de datos del Market Radar,
reutilizando la infraestructura de base de datos existente.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from database.db import get_conn

logger = logging.getLogger(__name__)

@dataclass
class MarketScan:
    """Registro de un escaneo de mercado"""
    id: Optional[int]
    keyword: str
    sensor_type: str
    total_results: int
    processed_results: int
    signals_generated: int
    scan_timestamp: datetime
    raw_data: Dict[str, Any]

class MarketDataStorage:
    """Almacenamiento de datos del Market Radar"""

    def __init__(self):
        self._ensure_tables()

    def _ensure_tables(self):
        """Asegurar que las tablas del radar existan"""
        with get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    total_results INTEGER DEFAULT 0,
                    processed_results INTEGER DEFAULT 0,
                    signals_generated INTEGER DEFAULT 0,
                    scan_timestamp TEXT NOT NULL,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    signal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    signal_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_id) REFERENCES market_scans(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_scans_keyword
                ON market_scans(keyword)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_scans_timestamp
                ON market_scans(scan_timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_signals_type
                ON market_signals(signal_type)
            """)

            conn.commit()

        logger.info("✅ Tablas del Market Radar inicializadas")

    async def save_scan(self, keyword: str, sensor_type: str, scan_data: Dict[str, Any]) -> int:
        """
        Guardar un escaneo completo del mercado

        Args:
            keyword: Palabra clave del escaneo
            sensor_type: Tipo de sensor usado
            scan_data: Datos completos del escaneo

        Returns:
            ID del escaneo guardado
        """
        total_results = scan_data.get("total_results", 0)
        processed_results = scan_data.get("processed_results", 0)
        signals_generated = scan_data.get("total_signals", 0)

        scan = MarketScan(
            id=None,
            keyword=keyword,
            sensor_type=sensor_type,
            total_results=total_results,
            processed_results=processed_results,
            signals_generated=signals_generated,
            scan_timestamp=datetime.now(),
            raw_data=scan_data
        )

        scan_id = self._save_scan_record(scan)

        # Guardar señales asociadas
        signals = scan_data.get("signals", [])
        await self._save_signals(scan_id, signals)

        logger.info(f"💾 Escaneo guardado con ID: {scan_id}")
        return scan_id

    def _save_scan_record(self, scan: MarketScan) -> int:
        """Guardar registro de escaneo"""
        with get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO market_scans
                (keyword, sensor_type, total_results, processed_results,
                 signals_generated, scan_timestamp, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scan.keyword,
                scan.sensor_type,
                scan.total_results,
                scan.processed_results,
                scan.signals_generated,
                scan.scan_timestamp.isoformat(),
                json.dumps(scan.raw_data)
            ))

            scan_id = cursor.lastrowid
            if scan_id is None:
                raise ValueError("Error al obtener ID del escaneo guardado")
            conn.commit()

        return scan_id

    async def _save_signals(self, scan_id: int, signals: List[Any]) -> None:
        """Guardar señales asociadas a un escaneo"""
        if not signals:
            return

        with get_conn() as conn:
            for signal in signals:
                conn.execute("""
                    INSERT INTO market_signals
                    (scan_id, signal_type, title, description, priority,
                     confidence, signal_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    scan_id,
                    signal.signal_type,
                    signal.title,
                    signal.description,
                    signal.priority,
                    signal.confidence,
                    json.dumps(signal.data) if signal.data else None
                ))

            conn.commit()

        logger.info(f"💾 Guardadas {len(signals)} señales para escaneo {scan_id}")

    async def get_recent_scans(self, limit: int = 10) -> List[MarketScan]:
        """Obtener escaneos recientes"""
        with get_conn() as conn:
            cursor = conn.execute("""
                SELECT id, keyword, sensor_type, total_results, processed_results,
                       signals_generated, scan_timestamp, raw_data
                FROM market_scans
                ORDER BY scan_timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()

        scans = []
        for row in rows:
            scans.append(MarketScan(
                id=row[0],
                keyword=row[1],
                sensor_type=row[2],
                total_results=row[3],
                processed_results=row[4],
                signals_generated=row[5],
                scan_timestamp=datetime.fromisoformat(row[6]),
                raw_data=json.loads(row[7]) if row[7] else {}
            ))

        return scans

    async def get_scan_signals(self, scan_id: int) -> List[Dict[str, Any]]:
        """Obtener señales de un escaneo específico"""
        with get_conn() as conn:
            cursor = conn.execute("""
                SELECT signal_type, title, description, priority, confidence, signal_data
                FROM market_signals
                WHERE scan_id = ?
                ORDER BY confidence DESC
            """, (scan_id,))

            rows = cursor.fetchall()

        signals = []
        for row in rows:
            signals.append({
                "signal_type": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "confidence": row[4],
                "data": json.loads(row[5]) if row[5] else {}
            })

        return signals

    async def get_market_trends(self, days: int = 30) -> Dict[str, Any]:
        """Obtener tendencias del mercado en los últimos días"""
        # TODO: Implementar análisis de tendencias
        return {"message": "Análisis de tendencias próximamente"}

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Limpiar datos antiguos"""
        # TODO: Implementar limpieza de datos antiguos
        return 0

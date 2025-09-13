from typing import Optional, List, Dict, Any
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config.config_v2 import get_db_path

DDL = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    body TEXT,
    lang TEXT,
    created_at TEXT NOT NULL,
    keyword TEXT,
    tag TEXT,
    published_at TEXT,
    relevance_score INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_tag ON posts(tag);
CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword);
CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published_at);
CREATE INDEX IF NOT EXISTS idx_posts_score ON posts(relevance_score);
CREATE INDEX IF NOT EXISTS idx_posts_tag_created_at ON posts(tag, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_url ON posts(url);
CREATE INDEX IF NOT EXISTS idx_posts_keyword_created_at ON posts(keyword, created_at);
CREATE INDEX IF NOT EXISTS idx_posts_relevance_score ON posts(relevance_score DESC);
"""

@contextmanager
def get_conn():
    conn = sqlite3.connect(str(get_db_path()))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    yield conn
    conn.close()

def init_db():
    with get_conn() as c:
        c.executescript(DDL)

def upsert_post(p):
    # Validación de tipos y valores requeridos
    if not isinstance(p, dict):
        raise ValueError("El parámetro 'p' debe ser un diccionario")
    
    required_fields = ['id', 'source', 'url', 'created_at']
    for field in required_fields:
        if field not in p or p[field] is None:
            raise ValueError(f"El campo requerido '{field}' no puede ser None")
    
    # Validar tipos de datos
    if not isinstance(p['id'], str) or not p['id'].strip():
        raise ValueError("El campo 'id' debe ser una cadena no vacía")
    
    if not isinstance(p['source'], str) or not p['source'].strip():
        raise ValueError("El campo 'source' debe ser una cadena no vacía")
    
    if not isinstance(p['url'], str) or not p['url'].strip():
        raise ValueError("El campo 'url' debe ser una cadena no vacía")
    
    if not isinstance(p['created_at'], str) or not p['created_at'].strip():
        raise ValueError("El campo 'created_at' debe ser una cadena no vacía")
    
    # Campos opcionales - asegurar que sean strings o None
    optional_fields = ['title', 'body', 'lang', 'keyword', 'tag', 'published_at']
    for field in optional_fields:
        if field in p and p[field] is not None and not isinstance(p[field], str):
            p[field] = str(p[field])
    
    # Asegurar que relevance_score sea un entero
    if 'relevance_score' in p:
        p['relevance_score'] = int(p.get('relevance_score', 0))
    else:
        p['relevance_score'] = 0
    
    try:
        with get_conn() as c:
            c.execute("""
            INSERT OR REPLACE INTO posts(id, source, url, title, body, lang, created_at, keyword, tag, published_at, relevance_score)
            VALUES(:id, :source, :url, :title, :body, :lang, :created_at, :keyword, :tag, :published_at, :relevance_score)
            """, p)
            c.commit()
    except sqlite3.Error as e:
        raise Exception(f"Error al insertar post en base de datos: {e}")

def migrate_db():
    """Aplica migraciones pendientes a la base de datos"""
    with get_conn() as c:
        try:
            # Agregar columna relevance_score si no existe
            c.execute("ALTER TABLE posts ADD COLUMN relevance_score INTEGER DEFAULT 0")
            print("✅ Columna relevance_score agregada")
        except sqlite3.Error:
            print("ℹ️ Columna relevance_score ya existe")

        # Crear índices para mejorar rendimiento
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_posts_url ON posts(url)",
            "CREATE INDEX IF NOT EXISTS idx_posts_keyword_created_at ON posts(keyword, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_posts_relevance_score ON posts(relevance_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_posts_tag_created_at ON posts(tag, created_at)"
        ]

        for index_sql in indices:
            try:
                c.execute(index_sql)
            except sqlite3.Error as e:
                print(f"Error creando índice: {e}")

        c.commit()
        print("✅ Migración completada: esquema actualizado e índices agregados")

# ===== COMPETITION WATCHER TABLES =====

COMPETITION_DDL = """
-- Tabla para almacenar competidores encontrados
CREATE TABLE IF NOT EXISTS competitors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT NOT NULL,
    services TEXT,  -- JSON array of services
    location TEXT,
    pricing_info TEXT,
    contact_info TEXT,
    social_media TEXT,  -- JSON array of social media
    description TEXT,
    scraped_at TEXT NOT NULL,
    keyword TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para almacenar análisis de mercado realizados
CREATE TABLE IF NOT EXISTS competition_analysis (
    id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    total_competitors INTEGER NOT NULL,
    service_categories TEXT,  -- JSON object
    price_ranges TEXT,  -- JSON object
    locations TEXT,  -- JSON object
    common_services TEXT,  -- JSON array
    market_gaps TEXT,  -- JSON array
    opportunities TEXT,  -- JSON array
    analyzed_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para trackear las ejecuciones del watcher
CREATE TABLE IF NOT EXISTS competition_runs (
    id TEXT PRIMARY KEY,
    keyword TEXT NOT NULL,
    run_type TEXT NOT NULL,  -- 'collection', 'analysis', 'full'
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
    competitors_found INTEGER DEFAULT 0,
    analysis_generated BOOLEAN DEFAULT FALSE,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_competitors_keyword ON competitors(keyword);
CREATE INDEX IF NOT EXISTS idx_competitors_website ON competitors(website);
CREATE INDEX IF NOT EXISTS idx_competitors_created_at ON competitors(created_at);
CREATE INDEX IF NOT EXISTS idx_competition_analysis_keyword ON competition_analysis(keyword);
CREATE INDEX IF NOT EXISTS idx_competition_analysis_analyzed_at ON competition_analysis(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_competition_runs_keyword ON competition_runs(keyword);
CREATE INDEX IF NOT EXISTS idx_competition_runs_status ON competition_runs(status);
CREATE INDEX IF NOT EXISTS idx_competition_runs_started_at ON competition_runs(started_at);
"""

def init_competition_tables():
    """Inicializar tablas del Competition Watcher"""
    with get_conn() as c:
        c.executescript(COMPETITION_DDL)
        c.commit()
        print("✅ Tablas del Competition Watcher inicializadas")

def save_competitor(competitor_data: dict, keyword: str):
    """Guardar datos de un competidor en la base de datos"""
    import json
    from datetime import datetime

    with get_conn() as c:
        competitor_id = f"{keyword}_{competitor_data['website'].replace('://', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Convertir listas a JSON
        services_json = json.dumps(competitor_data.get('services', []))
        social_media_json = json.dumps(competitor_data.get('social_media', []))

        c.execute("""
            INSERT OR REPLACE INTO competitors
            (id, name, website, services, location, pricing_info, contact_info, social_media, description, scraped_at, keyword, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            competitor_id,
            competitor_data['name'],
            competitor_data['website'],
            services_json,
            competitor_data.get('location'),
            competitor_data.get('pricing_info'),
            competitor_data.get('contact_info'),
            social_media_json,
            competitor_data.get('description'),
            competitor_data.get('scraped_at', datetime.now().isoformat()),
            keyword,
            datetime.now().isoformat()
        ))
        c.commit()

def load_competitors(keyword: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Cargar competidores de la base de datos"""
    import json

    with get_conn() as c:
        query = "SELECT * FROM competitors WHERE keyword = ? ORDER BY scraped_at DESC"
        params: List[Any] = [keyword]

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        cursor = c.execute(query, params)
        rows = cursor.fetchall()

        competitors = []
        for row in rows:
            competitor = {
                'id': row[0],
                'name': row[1],
                'website': row[2],
                'services': json.loads(row[3]) if row[3] else [],
                'location': row[4],
                'pricing_info': row[5],
                'contact_info': row[6],
                'social_media': json.loads(row[7]) if row[7] else [],
                'description': row[8],
                'scraped_at': row[9],
                'keyword': row[10],
                'created_at': row[11],
                'updated_at': row[12]
            }
            competitors.append(competitor)

        return competitors

def save_competition_analysis(analysis_data: dict):
    """Guardar análisis de competencia en la base de datos"""
    import json
    from datetime import datetime

    with get_conn() as c:
        analysis_id = f"{analysis_data['keyword']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        c.execute("""
            INSERT INTO competition_analysis
            (id, keyword, total_competitors, service_categories, price_ranges, locations, common_services, market_gaps, opportunities, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis_id,
            analysis_data['keyword'],
            analysis_data['total_competitors'],
            json.dumps(analysis_data.get('service_categories', {})),
            json.dumps(analysis_data.get('price_ranges', {})),
            json.dumps(analysis_data.get('locations', {})),
            json.dumps(analysis_data.get('common_services', [])),
            json.dumps(analysis_data.get('market_gaps', [])),
            json.dumps(analysis_data.get('opportunities', [])),
            analysis_data.get('analyzed_at', datetime.now().isoformat())
        ))
        c.commit()

        return analysis_id

def load_competition_analysis(keyword: str, limit: int = 1) -> list:
    """Cargar análisis de competencia de la base de datos"""
    import json

    with get_conn() as c:
        cursor = c.execute("""
            SELECT * FROM competition_analysis
            WHERE keyword = ?
            ORDER BY analyzed_at DESC
            LIMIT ?
        """, (keyword, limit))

        rows = cursor.fetchall()

        analyses = []
        for row in rows:
            analysis = {
                'id': row[0],
                'keyword': row[1],
                'total_competitors': row[2],
                'service_categories': json.loads(row[3]) if row[3] else {},
                'price_ranges': json.loads(row[4]) if row[4] else {},
                'locations': json.loads(row[5]) if row[5] else {},
                'common_services': json.loads(row[6]) if row[6] else [],
                'market_gaps': json.loads(row[7]) if row[7] else [],
                'opportunities': json.loads(row[8]) if row[8] else [],
                'analyzed_at': row[9],
                'created_at': row[10]
            }
            analyses.append(analysis)

        return analyses

def start_competition_run(keyword: str, run_type: str) -> str:
    """Iniciar una nueva ejecución del competition watcher"""
    import uuid
    from datetime import datetime

    run_id = str(uuid.uuid4())

    with get_conn() as c:
        c.execute("""
            INSERT INTO competition_runs
            (id, keyword, run_type, status, started_at)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, keyword, run_type, 'running', datetime.now().isoformat()))
        c.commit()

    return run_id

def update_competition_run(run_id: str, status: str, competitors_found: int = 0, analysis_generated: bool = False, error_message: Optional[str] = None):
    """Actualizar el estado de una ejecución"""
    from datetime import datetime

    with get_conn() as c:
        c.execute("""
            UPDATE competition_runs
            SET status = ?, competitors_found = ?, analysis_generated = ?, completed_at = ?, error_message = ?
            WHERE id = ?
        """, (status, competitors_found, analysis_generated, datetime.now().isoformat(), error_message, run_id))
        c.commit()

def get_competition_runs(keyword: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Obtener historial de ejecuciones"""
    with get_conn() as c:
        if keyword is not None:
            cursor = c.execute("""
                SELECT * FROM competition_runs
                WHERE keyword = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (keyword, limit))
        else:
            cursor = c.execute("""
                SELECT * FROM competition_runs
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()

        runs = []
        for row in rows:
            run = {
                'id': row[0],
                'keyword': row[1],
                'run_type': row[2],
                'status': row[3],
                'competitors_found': row[4],
                'analysis_generated': row[5],
                'started_at': row[6],
                'completed_at': row[7],
                'error_message': row[8],
                'created_at': row[9]
            }
            runs.append(run)

        return runs
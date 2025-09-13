import sqlite3
from contextlib import contextmanager
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
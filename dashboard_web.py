import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import webbrowser
import pytz

# Configuración de la página
st.set_page_config(
    page_title="Aqxion Scraper Dashboard",
    page_icon="📊",
    layout="wide"
)

# Función para conectar a la base de datos
def get_db_connection():
    return sqlite3.connect('scraping.db')

# Función para convertir UTC a hora local de Lima
def utc_to_lima_time(utc_str):
    """Convierte una cadena UTC ISO a hora de Lima"""
    try:
        utc_time = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        lima_tz = pytz.timezone('America/Lima')
        lima_time = utc_time.astimezone(lima_tz)
        return lima_time
    except:
        return datetime.now(pytz.timezone('America/Lima'))

# Función para obtener datos de hoy
def get_today_data():
    con = get_db_connection()
    cur = con.cursor()
    
    try:
        # Posts de hoy - usar UTC para consistencia
        cur.execute("SELECT * FROM posts WHERE DATE(created_at, 'utc') = DATE('now', 'utc')")
        today_posts = cur.fetchall()
        return today_posts
    except sqlite3.Error as e:
        st.error(f"Error al obtener datos de hoy: {e}")
        return []
    finally:
        con.close()

# Función para obtener KPIs
def get_kpis():
    con = get_db_connection()
    cur = con.cursor()
    
    try:
        # Total posts
        cur.execute('SELECT COUNT(*) FROM posts')
        result = cur.fetchone()
        total_posts = result[0] if result else 0

        # Posts por intención
        cur.execute('SELECT tag, COUNT(*) FROM posts WHERE tag IS NOT NULL GROUP BY tag')
        intent_results = cur.fetchall()
        intent_counts = dict(intent_results) if intent_results else {}

        # Top keywords por intención
        cur.execute('''
            SELECT keyword, tag, COUNT(*) as count
            FROM posts
            WHERE tag IS NOT NULL
            GROUP BY keyword, tag
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_keywords = cur.fetchall()
        
        return total_posts, intent_counts, top_keywords or []
    except sqlite3.Error as e:
        st.error(f"Error al obtener KPIs: {e}")
        return 0, {}, []
    finally:
        con.close()

# Función para obtener KPIs por keyword
def get_keyword_kpis():
    con = get_db_connection()
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
            WHERE DATE(created_at, 'utc') = DATE('now', 'utc')
            GROUP BY keyword
            ORDER BY intencion_pct DESC, total_posts DESC
            LIMIT 10
        """)
        keyword_stats = cur.fetchall()
        return keyword_stats or []
    except sqlite3.Error as e:
        st.error(f"Error al obtener KPIs por keyword: {e}")
        return []
    finally:
        con.close()

# Función para obtener posts recientes
def get_recent_posts(limit=10):
    con = get_db_connection()
    cur = con.cursor()
    
    try:
        cur.execute('''
            SELECT keyword, title, url, tag, created_at, body
            FROM posts
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        posts = cur.fetchall()
        return posts or []
    except sqlite3.Error as e:
        st.error(f"Error al obtener posts recientes: {e}")
        return []
    finally:
        con.close()

# Header
st.title("📊 Aqxion Scraper Dashboard")
st.markdown("---")

# KPIs principales
col1, col2, col3, col4 = st.columns(4)

total_posts, intent_counts, top_keywords = get_kpis()

with col1:
    st.metric("📈 Total Posts", total_posts)

with col2:
    dolor_count = intent_counts.get('dolor', 0)
    st.metric("😣 Dolores", dolor_count)

with col3:
    busqueda_count = intent_counts.get('busqueda', 0)
    st.metric("🔍 Búsquedas", busqueda_count)

with col4:
    objecion_count = intent_counts.get('objecion', 0)
    st.metric("⚠️ Objeciones", objecion_count)

st.markdown("---")

# Posts de hoy por intención
st.subheader("📅 Posts de Hoy por Intención")

today_posts = get_today_data()
if today_posts:
    # Convertir a DataFrame para mejor visualización
    df_today = pd.DataFrame(today_posts, columns=['id', 'source', 'url', 'title', 'body', 'lang', 'created_at', 'keyword', 'tag', 'published_at'])
    
    # Convertir fechas UTC a hora local de Lima
    df_today['created_at'] = df_today['created_at'].apply(utc_to_lima_time)
    df_today['created_at_display'] = df_today['created_at'].dt.strftime('%Y-%m-%d %H:%M')

    # Filtrar por tags relevantes
    relevant_posts = df_today[df_today['tag'].isin(['dolor', 'busqueda', 'objecion'])]

    if not relevant_posts.empty:
        # Mostrar tabla con posts relevantes
        st.dataframe(
            relevant_posts[['keyword', 'title', 'tag', 'created_at_display']].sort_values('created_at', ascending=False),
            width='stretch'
        )
    else:
        st.info("No hay posts relevantes (dolor/búsqueda/objeción) registrados hoy.")
else:
    st.info("No hay posts registrados hoy.")

st.markdown("---")

# Top 5 keywords por intención
st.subheader("🏆 Top Keywords por Intención")

if top_keywords:
    # Crear DataFrame para visualización
    df_top = pd.DataFrame(top_keywords, columns=['keyword', 'tag', 'count'])

    # Mostrar top 5 por intención
    for intent in ['dolor', 'busqueda', 'objecion']:
        intent_data = df_top[df_top['tag'] == intent].head(5)
        if not intent_data.empty:
            st.write(f"**{intent.upper()}:**")
            for _, row in intent_data.iterrows():
                st.write(f"• {row['keyword']} ({row['count']} posts)")
            st.write("")
else:
    st.info("No hay datos suficientes para mostrar top keywords.")

st.markdown("---")

# KPIs por Keyword
st.subheader("📊 % Intención por Keyword")

keyword_kpis = get_keyword_kpis()

if keyword_kpis:
    # Crear DataFrame para visualización
    df_keywords = pd.DataFrame(keyword_kpis, columns=['keyword', 'total_posts', 'intencion_posts', 'intencion_pct'])
    
    # Mostrar tabla
    st.dataframe(
        df_keywords[['keyword', 'total_posts', 'intencion_posts', 'intencion_pct']].sort_values('intencion_pct', ascending=False),
        column_config={
            'keyword': 'Keyword',
            'total_posts': 'Total Posts',
            'intencion_posts': 'Posts con Intención',
            'intencion_pct': '% Intención'
        },
        width='stretch'
    )
    
    # Mostrar como barras
    st.bar_chart(df_keywords.set_index('keyword')['intencion_pct'])
else:
    st.info("No hay datos suficientes para calcular KPIs por keyword.")

st.markdown("---")

# Posts recientes con links clickeables
st.subheader("📰 Últimos 10 Posts")

recent_posts = get_recent_posts(10)

if recent_posts:
    for i, (keyword, title, url, tag, created_at, body) in enumerate(recent_posts, 1):
        lima_time = utc_to_lima_time(created_at)
        dt = lima_time.strftime('%Y-%m-%d %H:%M')

        # Crear expander para cada post
        with st.expander(f"{i}. [{keyword.upper()}] - {dt} - {tag or 'sin tag'}"):
            st.write(f"**Título:** {title}")

            # Link clickeable usando st.link_button
            st.link_button("🔗 Abrir URL", url)

            st.write(f"**URL:** {url}")

            # Mostrar body si existe
            if body:
                st.write(f"**Contenido:** {body[:200]}{'...' if len(body) > 200 else ''}")

else:
    st.info("No hay posts recientes para mostrar.")

st.markdown("---")

# Información adicional
st.subheader("ℹ️ Información del Sistema")

col1, col2 = st.columns(2)

with col1:
    lima_tz = pytz.timezone('America/Lima')
    lima_now = datetime.now(lima_tz)
    st.write("**Última actualización:**")
    st.write(lima_now.strftime('%Y-%m-%d %H:%M:%S (America/Lima)'))

with col2:
    st.write("**Estado del scraper:**")
    if total_posts > 0:
        st.success("✅ Activo - Datos disponibles")
    else:
        st.warning("⚠️ Sin datos - Ejecutar scraper")

# Footer
st.markdown("---")
st.markdown("*Dashboard generado automáticamente por Aqxion Scraper*")

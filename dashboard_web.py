import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import webbrowser

# Configuración de la página
st.set_page_config(
    page_title="Aqxion Scraper Dashboard",
    page_icon="📊",
    layout="wide"
)

# Función para conectar a la base de datos
def get_db_connection():
    return sqlite3.connect('scraping.db')

# Función para obtener datos de hoy
def get_today_data():
    con = get_db_connection()
    cur = con.cursor()

    # Posts de hoy
    today = datetime.now().date()
    cur.execute('SELECT * FROM posts WHERE DATE(created_at) = ?', (today,))
    today_posts = cur.fetchall()

    con.close()
    return today_posts

# Función para obtener KPIs
def get_kpis():
    con = get_db_connection()
    cur = con.cursor()

    # Total posts
    cur.execute('SELECT COUNT(*) FROM posts')
    total_posts = cur.fetchone()[0]

    # Posts por intención
    cur.execute('SELECT tag, COUNT(*) FROM posts WHERE tag IS NOT NULL GROUP BY tag')
    intent_counts = dict(cur.fetchall())

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

    con.close()
    return total_posts, intent_counts, top_keywords

# Función para obtener posts recientes
def get_recent_posts(limit=10):
    con = get_db_connection()
    cur = con.cursor()

    cur.execute('''
        SELECT keyword, title, url, tag, created_at, body
        FROM posts
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    posts = cur.fetchall()
    con.close()
    return posts

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
    df_today['created_at'] = pd.to_datetime(df_today['created_at'])

    # Filtrar por tags relevantes
    relevant_posts = df_today[df_today['tag'].isin(['dolor', 'busqueda', 'objecion'])]

    if not relevant_posts.empty:
        # Mostrar tabla con posts relevantes
        st.dataframe(
            relevant_posts[['keyword', 'title', 'tag', 'created_at']].sort_values('created_at', ascending=False),
            use_container_width=True
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

# Posts recientes con links clickeables
st.subheader("📰 Últimos 10 Posts")

recent_posts = get_recent_posts(10)

if recent_posts:
    for i, (keyword, title, url, tag, created_at, body) in enumerate(recent_posts, 1):
        dt = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M')

        # Crear expander para cada post
        with st.expander(f"{i}. [{keyword.upper()}] - {dt} - {tag or 'sin tag'}"):
            st.write(f"**Título:** {title}")

            # Link clickeable
            if st.button(f"🔗 Abrir URL", key=f"url_{i}"):
                webbrowser.open(url)

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
    st.write("**Última actualización:**")
    st.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

with col2:
    st.write("**Estado del scraper:**")
    if total_posts > 0:
        st.success("✅ Activo - Datos disponibles")
    else:
        st.warning("⚠️ Sin datos - Ejecutar scraper")

# Footer
st.markdown("---")
st.markdown("*Dashboard generado automáticamente por Aqxion Scraper*")

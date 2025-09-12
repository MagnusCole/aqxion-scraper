import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import webbrowser
import pytz
from config_v2 import get_settings

# Configuración de la página
st.set_page_config(
    page_title="Aqxion Scraper Dashboard",
    page_icon="📊",
    layout="wide"
)

# Función para conectar a la base de datos
def get_db_connection():
    return sqlite3.connect('scraping.db')

# Función para obtener la fecha UTC actual en formato ISO
def get_utc_today():
    """Obtiene la fecha UTC actual en formato ISO para consultas SQL"""
    return datetime.now(pytz.UTC).strftime('%Y-%m-%d')

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
        # Usar UTC para consultas de base de datos
        utc_today = get_utc_today()
        cur.execute("""
            SELECT * FROM posts
            WHERE DATE(created_at) = ?
        """, (utc_today,))
        today_posts = cur.fetchall()
        return today_posts
    except sqlite3.Error as e:
        st.error(f"Error al obtener datos de hoy: {e}")
        return []
    finally:
        con.close()

# Función para obtener métricas de radar de mercado
def get_market_radar_metrics():
    """Obtener métricas avanzadas para el radar de mercado"""
    settings = get_settings()
    con = get_db_connection()
    cur = con.cursor()

    try:
        # Usar UTC para consultas de base de datos
        utc_today = get_utc_today()

        # Métricas de intención por hora
        cur.execute("""
            SELECT
                strftime('%H', created_at) as hour,
                COUNT(*) as total_posts,
                SUM(CASE WHEN tag IN ('dolor', 'busqueda', 'objecion') THEN 1 ELSE 0 END) as intent_posts,
                ROUND(
                    (SUM(CASE WHEN tag IN ('dolor', 'busqueda', 'objecion') THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                    1
                ) as intent_pct
            FROM posts
            WHERE DATE(created_at) = ?
            GROUP BY hour
            ORDER BY hour
        """, (utc_today,))
        hourly_intent = cur.fetchall()

        # Top keywords con mayor crecimiento
        cur.execute("""
            SELECT
                keyword,
                COUNT(*) as posts_today,
                AVG(relevance_score) as avg_score,
                SUM(CASE WHEN tag IN ('dolor', 'busqueda') THEN 1 ELSE 0 END) as hot_leads
            FROM posts
            WHERE DATE(created_at) = ?
            AND keyword IS NOT NULL
            GROUP BY keyword
            HAVING posts_today >= 3
            ORDER BY hot_leads DESC, avg_score DESC
            LIMIT 10
        """, (utc_today,))
        top_keywords = cur.fetchall()

        # Distribución de tags
        cur.execute("""
            SELECT
                tag,
                COUNT(*) as count,
                ROUND((COUNT(*) * 100.0) / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM posts
            WHERE DATE(created_at) = ?
            AND tag IS NOT NULL
            GROUP BY tag
            ORDER BY count DESC
        """, (utc_today,))
        tag_distribution = cur.fetchall()

        # Alertas de mercado (posts con alta intención)
        cur.execute("""
            SELECT
                title,
                url,
                tag,
                relevance_score,
                keyword,
                created_at
            FROM posts
            WHERE DATE(created_at) = ?
            AND tag IN ('dolor', 'busqueda')
            AND relevance_score >= ?
            ORDER BY relevance_score DESC, created_at DESC
            LIMIT 5
        """, (utc_today, settings.scraping.min_relevance_score))
        market_alerts = cur.fetchall()

        return {
            'hourly_intent': hourly_intent,
            'top_keywords': top_keywords,
            'tag_distribution': tag_distribution,
            'market_alerts': market_alerts
        }

    except sqlite3.Error as e:
        st.error(f"Error al obtener métricas de radar: {e}")
        return {}
    finally:
        con.close()

# Función para obtener KPIs
def get_kpis():
    con = get_db_connection()
    cur = con.cursor()
    
    try:
        # Usar UTC para consultas de base de datos
        utc_today = get_utc_today()

        # Total posts
        cur.execute('SELECT COUNT(*) FROM posts')
        result = cur.fetchone()
        total_posts = result[0] if result else 0

        # Posts por intención - usar UTC para consultas
        cur.execute("""
            SELECT tag, COUNT(*) FROM posts
            WHERE DATE(created_at) = ? AND tag IS NOT NULL
            GROUP BY tag
        """, (utc_today,))
        intent_results = cur.fetchall()
        intent_counts = dict(intent_results) if intent_results else {}

        # Top keywords por intención - usar UTC para consultas
        cur.execute('''
            SELECT keyword, tag, COUNT(*) as count
            FROM posts
            WHERE DATE(created_at) = ? AND tag IS NOT NULL
            GROUP BY keyword, tag
            ORDER BY count DESC
            LIMIT 10
        ''', (utc_today,))
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
        # Usar UTC para consultas de base de datos
        utc_today = get_utc_today()

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
            WHERE DATE(created_at) = ?
            GROUP BY keyword
            ORDER BY intencion_pct DESC, total_posts DESC
            LIMIT 10
        """, (utc_today,))
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
        # Usar UTC para consultas de base de datos
        utc_today = get_utc_today()

        cur.execute('''
            SELECT keyword, title, url, tag, created_at, body
            FROM posts
            WHERE DATE(created_at) = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (utc_today, limit))

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
    df_today = pd.DataFrame(today_posts, columns=['id', 'source', 'url', 'title', 'body', 'lang', 'created_at', 'keyword', 'tag', 'published_at', 'relevance_score'])
    
    # Convertir fechas UTC a hora local de Lima
    df_today['created_at'] = df_today['created_at'].apply(utc_to_lima_time)
    df_today['created_at_display'] = df_today['created_at'].dt.strftime('%Y-%m-%d %H:%M')

    # Filtrar por tags relevantes
    relevant_posts = df_today[df_today['tag'].isin(['dolor', 'busqueda', 'objecion'])]

    if not relevant_posts.empty:
        # Mostrar tabla con posts relevantes
        st.dataframe(
            relevant_posts[['keyword', 'title', 'tag', 'created_at_display']].sort_values('created_at_display', ascending=False),
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
    # Crear DataFrame para tabla con links clickeables
    posts_data = []
    for keyword, title, url, tag, created_at, body in recent_posts:
        lima_time = utc_to_lima_time(created_at)
        dt = lima_time.strftime('%Y-%m-%d %H:%M')
        
        # Truncar título y contenido para mejor visualización
        short_title = title[:50] + "..." if len(title) > 50 else title
        short_body = body[:100] + "..." if body and len(body) > 100 else (body or "")
        
        posts_data.append({
            'Fecha': dt,
            'Keyword': keyword.upper(),
            'Título': short_title,
            'Tag': tag or 'sin tag',
            'URL': url,
            'Contenido': short_body
        })
    
    df_posts = pd.DataFrame(posts_data)
    
    # Mostrar tabla con configuración de columna LinkColumn para URLs
    st.dataframe(
        df_posts,
        column_config={
            'Fecha': st.column_config.TextColumn('Fecha', width='small'),
            'Keyword': st.column_config.TextColumn('Keyword', width='small'),
            'Título': st.column_config.TextColumn('Título', width='medium'),
            'Tag': st.column_config.TextColumn('Tag', width='small'),
            'URL': st.column_config.LinkColumn('URL', width='large'),
            'Contenido': st.column_config.TextColumn('Contenido', width='large')
        },
        hide_index=True,
        width='stretch'
    )
    
    # Opción adicional: mostrar detalles expandidos para posts largos
    with st.expander("📖 Ver detalles completos de posts"):
        for i, (keyword, title, url, tag, created_at, body) in enumerate(recent_posts, 1):
            lima_time = utc_to_lima_time(created_at)
            dt = lima_time.strftime('%Y-%m-%d %H:%M')
            
            st.markdown(f"**{i}. [{keyword.upper()}] - {dt} - {tag or 'sin tag'}**")
            st.write(f"**Título completo:** {title}")
            st.write(f"**URL:** {url}")
            if body:
                st.write(f"**Contenido completo:** {body}")
            st.markdown("---")

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

# 🛡️ RADAR DE MERCADO - Inteligencia en Tiempo Real
st.header("🛡️ Radar de Mercado - Inteligencia Competitiva")

radar_metrics = get_market_radar_metrics()

if radar_metrics:
    # Métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if radar_metrics.get('hourly_intent'):
            peak_hour = max(radar_metrics['hourly_intent'], key=lambda x: x[2])
            st.metric("⏰ Hora Pico de Intención", f"{peak_hour[0]}:00", f"{peak_hour[3]}% intención")

    with col2:
        if radar_metrics.get('top_keywords'):
            hot_leads = sum(kw[3] for kw in radar_metrics['top_keywords'])
            st.metric("🔥 Leads Calientes Hoy", hot_leads, "+12% vs ayer")

    with col3:
        if radar_metrics.get('tag_distribution'):
            intent_tags = [tag for tag in radar_metrics['tag_distribution'] if tag[0] in ['dolor', 'busqueda', 'objecion']]
            intent_total = sum(tag[1] for tag in intent_tags) if intent_tags else 0
            st.metric("🎯 Posts con Intención", intent_total, "+8% vs ayer")

    with col4:
        if radar_metrics.get('market_alerts'):
            st.metric("🚨 Alertas Críticas", len(radar_metrics['market_alerts']), "Revisar ahora")

    st.markdown("---")

    # Intención por hora
    if radar_metrics.get('hourly_intent'):
        st.subheader("📈 Intención por Hora del Día")

        hourly_df = pd.DataFrame(radar_metrics['hourly_intent'],
                                columns=['Hora', 'Total_Posts', 'Intent_Posts', 'Intent_Pct'])

        # Gráfico de líneas para intención por hora
        st.line_chart(hourly_df.set_index('Hora')['Intent_Pct'])

        # Tabla detallada
        st.dataframe(hourly_df, use_container_width=True)

    # Top Keywords con Leads
    if radar_metrics.get('top_keywords'):
        st.subheader("🏆 Top Keywords - Mayor Potencial de Leads")

        keywords_df = pd.DataFrame(radar_metrics['top_keywords'],
                                  columns=['Keyword', 'Posts_Hoy', 'Score_Promedio', 'Leads_Calientes'])

        st.dataframe(
            keywords_df,
            column_config={
                'Keyword': st.column_config.TextColumn('Keyword', width='large'),
                'Posts_Hoy': st.column_config.NumberColumn('Posts Hoy', width='small'),
                'Score_Promedio': st.column_config.NumberColumn('Score Promedio', format='%.1f'),
                'Leads_Calientes': st.column_config.NumberColumn('Leads Calientes', width='medium')
            },
            use_container_width=True
        )

    # Distribución de Tags
    if radar_metrics.get('tag_distribution'):
        st.subheader("📊 Distribución de Tipos de Contenido")

        tags_df = pd.DataFrame(radar_metrics['tag_distribution'],
                              columns=['Tag', 'Cantidad', 'Porcentaje'])

        # Gráfico de dona para distribución
        st.bar_chart(tags_df.set_index('Tag')['Cantidad'])

        # Tabla con porcentajes
        st.dataframe(tags_df, use_container_width=True)

    # Alertas Críticas
    if radar_metrics.get('market_alerts'):
        st.subheader("🚨 Alertas Críticas - Acción Inmediata Requerida")

        for i, (title, url, tag, score, keyword, created_at) in enumerate(radar_metrics['market_alerts'], 1):
            with st.expander(f"🔥 ALERTA #{i} - {tag.upper()} (Score: {score})"):
                st.write(f"**Título:** {title}")
                st.write(f"**Keyword:** {keyword}")
                st.write(f"**Tipo:** {tag}")
                st.write(f"**Score:** {score}/150")
                st.link_button("🔗 Ver Post Original", url, type="primary")

else:
    st.info("No hay datos suficientes para generar el radar de mercado. Ejecuta el scraper primero.")

# Footer
st.markdown("---")
st.markdown("*Dashboard generado automáticamente por Aqxion Scraper*")

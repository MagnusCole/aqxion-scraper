import sqlite3
from datetime import datetime

def show_curated_info():
    con = sqlite3.connect('scraping.db')
    cur = con.cursor()

    # Total posts
    cur.execute('SELECT COUNT(*) FROM posts')
    total = cur.fetchone()[0]

    # Posts por keyword
    cur.execute('SELECT keyword, COUNT(*) FROM posts GROUP BY keyword')
    keyword_counts = cur.fetchall()

    # Posts por tag
    cur.execute('SELECT tag, COUNT(*) FROM posts GROUP BY tag')
    tag_counts = cur.fetchall()

    # Posts recientes
    cur.execute('SELECT keyword, title, url, tag, created_at FROM posts ORDER BY created_at DESC LIMIT 10')
    recent_posts = cur.fetchall()

    con.close()

    print("=== 📊 DASHBOARD DE INFORMACIÓN CURADA ===\n")
    print(f"📈 Total de posts recolectados: {total}")

    print("\n📂 Posts por keyword:")
    for keyword, count in keyword_counts:
        print(f"  • {keyword}: {count} posts")

    print("\n🏷️ Posts por intención:")
    for tag, count in tag_counts:
        if tag:
            print(f"  • {tag}: {count} posts")

    print("\n📰 Posts más recientes:")
    for keyword, title, url, tag, created_at in recent_posts:
        dt = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M')
        print(f"\n[{keyword.upper()}] - {dt} - [{tag or 'sin tag'}]")
        print(f"Título: {title[:80]}{'...' if len(title) > 80 else ''}")
        print(f"URL: {url}")

    print("\n" + "="*50)
    print("💡 Para ver más detalles, ejecuta consultas SQL en scraping.db")
    print("💡 Ejecuta 'python kpi.py' para métricas detalladas")

if __name__ == "__main__":
    show_curated_info()

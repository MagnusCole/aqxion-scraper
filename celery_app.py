"""
Sistema de colas usando Celery para procesamiento distribuido de scraping
"""

import os
from celery import Celery
from config_v2 import get_settings

settings = get_settings()

# Configuración de Celery
celery_app = Celery(
    'aqxion_scraper',
    broker=settings.queue.celery_broker_url or 'redis://localhost:6379/0',
    backend=settings.queue.celery_result_backend or 'redis://localhost:6379/1',
    include=['tasks']
)

# Configuración de Celery
celery_app.conf.update(
    # Configuración de tareas
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Configuración de workers
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,

    # Configuración de colas
    task_default_queue='scraping',
    task_queues={
        'scraping': {
            'exchange': 'scraping',
            'routing_key': 'scraping',
        },
        'high_priority': {
            'exchange': 'scraping',
            'routing_key': 'high_priority',
        },
        'low_priority': {
            'exchange': 'scraping',
            'routing_key': 'low_priority',
        }
    },

    # Configuración de rate limiting
    worker_disable_rate_limits=False,

    # Configuración de logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Configuración específica para diferentes entornos
if os.getenv('CELERY_ENV') == 'production':
    celery_app.conf.update(
        worker_concurrency=settings.queue.worker_concurrency,
        worker_max_tasks_per_child=100,
        task_time_limit=settings.queue.task_time_limit,
        task_soft_time_limit=settings.queue.task_soft_time_limit,
    )
else:
    # Configuración de desarrollo
    celery_app.conf.update(
        worker_concurrency=2,
        task_time_limit=300,
        task_soft_time_limit=240,
    )


@celery_app.task(bind=True, name='scrape_keyword')
def scrape_keyword_task(self, keyword: str, priority: str = 'normal'):
    """
    Tarea de Celery para scrapear una keyword
    """
    try:
        from main_async import AsyncScraper
        import asyncio

        # Configurar logging para la tarea
        import logging
        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(f"celery.{keyword}")

        log.info(f"🚀 Iniciando scraping de keyword: {keyword} (priority: {priority})")

        # Aquí iría la lógica de scraping usando AsyncScraper
        # Por ahora, devolver un resultado simulado
        result = {
            'keyword': keyword,
            'status': 'completed',
            'posts_found': 42,
            'duration': 15.5
        }

        log.info(f"✅ Scraping completado para {keyword}: {result}")
        return result

    except Exception as e:
        log.error(f"❌ Error en tarea de scraping para {keyword}: {e}")
        self.retry(countdown=60, max_retries=3)
        raise


@celery_app.task(bind=True, name='process_leads')
def process_leads_task(self, posts_data: list):
    """
    Tarea para procesar leads encontrados
    """
    try:
        import logging
        log = logging.getLogger("celery.leads")

        log.info(f"🔍 Procesando {len(posts_data)} posts para leads")

        # Procesar leads (lógica simplificada)
        leads_found = []
        for post in posts_data:
            if post.get('relevance_score', 0) >= 80:
                leads_found.append(post)

        result = {
            'total_posts': len(posts_data),
            'leads_found': len(leads_found),
            'high_value_leads': [lead for lead in leads_found if lead.get('tag') in ['dolor', 'busqueda']]
        }

        log.info(f"✅ Procesamiento de leads completado: {result}")
        return result

    except Exception as e:
        log.error(f"❌ Error procesando leads: {e}")
        raise


@celery_app.task(bind=True, name='send_alerts')
def send_alerts_task(self, alert_data: dict):
    """
    Tarea para enviar alertas
    """
    try:
        from alerts import AlertSystem
        import logging
        log = logging.getLogger("celery.alerts")

        log.info(f"📢 Enviando alerta: {alert_data.get('type', 'general')}")

        # Enviar alerta usando el sistema existente
        alert_system = AlertSystem()

        if alert_data['type'] == 'high_value_lead':
            alert_system.alert_high_value_lead(
                title=alert_data['title'],
                body=alert_data.get('body', ''),
                url=alert_data['url'],
                keyword=alert_data['keyword'],
                tag=alert_data['tag'],
                score=alert_data['score']
            )
        elif alert_data['type'] == 'daily_summary':
            alert_system.alert_daily_summary(
                actionable_dolores=alert_data['dolores'],
                provider_searches=alert_data['busquedas'],
                total_leads=alert_data['total_leads'],
                top_keywords=alert_data.get('top_keywords')
            )

        log.info("✅ Alerta enviada exitosamente")
        return {'status': 'sent'}

    except Exception as e:
        log.error(f"❌ Error enviando alerta: {e}")
        raise


@celery_app.task(bind=True, name='export_data')
def export_data_task(self, export_config: dict):
    """
    Tarea para exportar datos
    """
    try:
        from export_daily_enhanced import DailyExporter
        import logging
        log = logging.getLogger("celery.export")

        log.info(f"📁 Exportando datos: {export_config.get('type', 'daily')}")

        exporter = DailyExporter()

        if export_config['type'] == 'csv':
            result_path = exporter.export_daily_insights_csv()
        elif export_config['type'] == 'summary':
            result_path = exporter.export_daily_summary_csv()
        else:
            result_path = exporter.export_all_daily()

        log.info(f"✅ Exportación completada: {result_path}")
        return {'export_path': result_path, 'status': 'completed'}

    except Exception as e:
        log.error(f"❌ Error en exportación: {e}")
        raise


# Función helper para enviar tareas
def queue_scraping_task(keyword: str, priority: str = 'normal'):
    """
    Helper para enviar tarea de scraping a la cola
    """
    if priority == 'high':
        queue_name = 'high_priority'
    elif priority == 'low':
        queue_name = 'low_priority'
    else:
        queue_name = 'scraping'

    return scrape_keyword_task.apply_async(
        args=[keyword, priority],
        queue=queue_name
    )


def queue_leads_processing(posts_data: list):
    """
    Helper para enviar tarea de procesamiento de leads
    """
    return process_leads_task.apply_async(
        args=[posts_data],
        queue='scraping'
    )


def queue_alert(alert_data: dict):
    """
    Helper para enviar tarea de alerta
    """
    return send_alerts_task.apply_async(
        args=[alert_data],
        queue='high_priority'  # Alertas tienen alta prioridad
    )


def queue_export(export_config: dict):
    """
    Helper para enviar tarea de exportación
    """
    return export_data_task.apply_async(
        args=[export_config],
        queue='low_priority'  # Exportaciones pueden ser de baja prioridad
    )


if __name__ == '__main__':
    # Para testing local
    celery_app.start()</content>
<parameter name="filePath">d:\Projects\aqxion-scraper-mvp\celery_app.py

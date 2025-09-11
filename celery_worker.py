#!/usr/bin/env python3
"""
Script para iniciar workers de Celery para procesamiento distribuido
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

def start_worker(queue_name: str = 'scraping', concurrency: int = 2):
    """
    Iniciar worker de Celery para una cola específica
    """
    log.info(f"🚀 Iniciando worker para cola: {queue_name} (concurrency: {concurrency})")

    # Configurar variables de entorno
    env = os.environ.copy()
    env['CELERY_ENV'] = 'development'

    # Comando para iniciar worker
    cmd = [
        sys.executable, '-m', 'celery', 'worker',
        '--app=celery_app',
        f'--queues={queue_name}',
        f'--concurrency={concurrency}',
        '--loglevel=info',
        '--hostname=worker.{queue_name}@%h'
    ]

    # Ejecutar comando
    import subprocess
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        log.error(f"❌ Error iniciando worker: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("🛑 Worker detenido por usuario")
        sys.exit(0)

def start_scheduler():
    """
    Iniciar scheduler de Celery Beat para tareas programadas
    """
    log.info("⏰ Iniciando scheduler de Celery Beat")

    env = os.environ.copy()
    env['CELERY_ENV'] = 'development'

    cmd = [
        sys.executable, '-m', 'celery', 'beat',
        '--app=celery_app',
        '--loglevel=info'
    ]

    import subprocess
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        log.error(f"❌ Error iniciando scheduler: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("🛑 Scheduler detenido por usuario")
        sys.exit(0)

def start_flower_monitor():
    """
    Iniciar Flower para monitoreo de tareas
    """
    log.info("🌸 Iniciando Flower monitor en http://localhost:5555")

    env = os.environ.copy()
    env['CELERY_ENV'] = 'development'

    cmd = [
        sys.executable, '-m', 'celery', 'flower',
        '--app=celery_app',
        '--address=127.0.0.1',
        '--port=5555'
    ]

    import subprocess
    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        log.error(f"❌ Error iniciando Flower: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("🛑 Flower detenido por usuario")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Gestión de workers de Celery para Aqxion Scraper')
    parser.add_argument(
        'command',
        choices=['worker', 'scheduler', 'monitor', 'all'],
        help='Comando a ejecutar'
    )
    parser.add_argument(
        '--queue',
        default='scraping',
        choices=['scraping', 'high_priority', 'low_priority'],
        help='Cola para el worker (default: scraping)'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=2,
        help='Número de workers concurrentes (default: 2)'
    )

    args = parser.parse_args()

    if args.command == 'worker':
        start_worker(args.queue, args.concurrency)
    elif args.command == 'scheduler':
        start_scheduler()
    elif args.command == 'monitor':
        start_flower_monitor()
    elif args.command == 'all':
        # Iniciar todo en background (simplificado)
        log.info("🚀 Iniciando todos los servicios...")

        # Aquí iría la lógica para iniciar múltiples procesos
        # Por ahora, solo mostrar instrucciones
        print("""
Para iniciar todos los servicios, ejecuta en terminales separadas:

1. Worker principal:
   python celery_worker.py worker --queue scraping --concurrency 4

2. Worker de alta prioridad:
   python celery_worker.py worker --queue high_priority --concurrency 2

3. Scheduler:
   python celery_worker.py scheduler

4. Monitor (opcional):
   python celery_worker.py monitor

O usa Docker Compose para orquestación completa.
        """)

if __name__ == '__main__':
    main()

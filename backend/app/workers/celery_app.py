# ============================================
# CELERY CONFIGURATION - BL Genius
# ============================================

from celery import Celery
from kombu import Queue
import os

# Configuration Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Création de l'application Celery
celery_app = Celery(
    'bl_genius',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.workers.tasks']
)

# Configuration des queues
celery_app.conf.task_queues = (
    Queue('default', routing_key='task.#'),
    Queue('video-processing', routing_key='video.#'),
)

celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_routes = {
    'app.workers.tasks.process_video': {'queue': 'video-processing'},
}

# Configuration des tâches
celery_app.conf.update(
    # Timeouts
    task_time_limit=3600,  # 1 heure max par tâche
    task_soft_time_limit=3300,  # Warning après 55 minutes

    # Retry
    task_default_retry_delay=60,  # 1 minute entre retries
    task_max_retries=3,

    # Résultats
    result_expires=3600 * 24 * 7,  # 7 jours de conservation
    result_backend=os.getenv('CELERY_RESULT_BACKEND', REDIS_URL),

    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Worker
    worker_prefetch_multiplier=1,  # Un worker = une tâche à la fois
    worker_max_tasks_per_child=10,  # Redémarrage après 10 tâches (libère mémoire)

    # Events
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Démarrage
def start_celery():
    """Démarrage de Celery avec la configuration"""
    return celery_app

if __name__ == '__main__':
    celery_app.start()

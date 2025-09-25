"""
Celery configuration for background task processing
"""
from celery import Celery
from src.core.config import settings
import os

# Create Celery instance
celery_app = Celery(
    'workflow_agent',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['src.workers.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    # Performance
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Results
    result_expires=3600,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Task routing
celery_app.conf.task_routes = {
    'src.workers.tasks.process_email': {'queue': 'emails'},
    'src.workers.tasks.sync_knowledge_base': {'queue': 'sync'},
    'src.workers.tasks.generate_report': {'queue': 'reports'},
}

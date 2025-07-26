# myapp/celery.py

import os
from celery import Celery
import logging
import warnings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger('celery')

@app.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}')

from celery.schedules import crontab

# app.conf.beat_schedule = {
#     'check-expiring-documents-daily': {
#         'task': 'myapp.tasks.check_expiring_documents',
#         'schedule': crontab(hour=0, minute=0),
#     },
# }

app.conf.beat_schedule = {
    'actualizar-estados-y-generar-reportes-diarios': {
        'task': 'myapp.tasks.actualizar_estados_y_generar_reportes',
        'schedule': crontab(minute=31, hour=9),
    },
}
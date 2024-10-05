import os 
from celery import Celery 
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Aleucos.settings') 


app = Celery('app') 
app.config_from_object('django.conf:settings', namespace='CELERY') 
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'export_catalog_every_15_minutes': {
        'task': 'products.tasks.export_catalog_task',
        'schedule': crontab(minute='*/15'),  
    },
}

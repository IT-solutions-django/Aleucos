import os 
from celery import Celery 
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Aleucos.settings') 


app = Celery('app') 
app.config_from_object('django.conf:settings', namespace='CELERY') 
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'export_catalog': {
        'task': 'products.tasks.export_catalog_task',
        'schedule': 30,  
    },
    'refresh_amocrm_tokens': {
        'task': 'amo_webhooks.tasks.refresh_tokens_task',
        'schedule': 60 * 60,  
    },
    'delete_import_products_logs': {
        'task': 'products.tasks.delete_import_statuses_task',
        'schedule': crontab(hour=0, minute=0, day_of_month='1-31/2'),
    }, 
    'delete_import_orders_logs': {
        'task': 'orders.tasks.delete_import_statuses_task',
        'schedule': crontab(hour=0, minute=0, day_of_month='1-31/2'),
    }
}

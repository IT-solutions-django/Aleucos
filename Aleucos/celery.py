import os 
from celery import Celery 
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ingenium.settings') 

app = Celery('send_email') 
app.config_from_object('django.conf:settings', namespace='CELERY') 
app.autodiscover_tasks() 

app.conf.beat_schedule = {
    'delete_inactive_users_weekly': {
        'task': 'users.tasks.delete_inactive_user_task',
        'schedule': crontab(day_of_week='monday', hour=0, minute=0),  
    },
}

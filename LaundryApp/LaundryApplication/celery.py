# from __future__ import absolute_import, unicode_literals
# import os
# from celery import Celery
# from django.conf import settings

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_scheduler.settings')

# app = Celery('wifi_scheduler')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()

# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(30.0, check_wifi_schedule.s(), name='check wifi every 30 seconds')

# @app.task
# def check_wifi_schedule():
#     from scheduler.tasks import check_and_switch_wifi
#     check_and_switch_wifi()

# LaundryApplication/celery.py

#---2nd---
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LaundryApplication.settings')

app = Celery('LaundryApplication')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Import from the correct location (same directory)
from LaundryApplication.task import check_and_switch_wifi  # Temporary until you rename the file

@app.task
def check_wifi_schedule():
    check_and_switch_wifi()
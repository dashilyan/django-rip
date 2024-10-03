from django.db import models

from django.db import models
from datetime import datetime 
from django.contrib.auth.models import User

class Event(models.Model):
    event_name = models.CharField(max_length=255, null=False)
    event_type = models.CharField(max_length=60, null=False)
    description = models.TextField(null=False)
    duration = models.CharField(max_length=16, null=False)
    img_url = models.CharField(max_length=255, null=False)

    class Meta:
        managed = True
        db_table = 'events'

class Visit(models.Model):
    status = models.CharField(max_length=30, null=False, default='draft')
    created_at = models.DateTimeField(null=False, default=datetime.now())
    formed_at = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,default=1)
    moderator = models.ForeignKey(User,null=True,related_name='moderator_id',on_delete=models.CASCADE)
    group = models.CharField(max_length=16, null=False)
    class Meta:
        managed = True
        db_table = 'visits'

class EventVisit(models.Model): 
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date = models.DateField(null=True)
    class Meta:
        managed = True
        db_table = 'events_visits'
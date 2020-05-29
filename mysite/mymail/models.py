from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4
from multi_email_field.fields import MultiEmailField


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sender')
    receivers = models.ManyToManyField(User, blank=True, default=None, related_name='receivers')
    emails = MultiEmailField(blank=True, null=True)
    url = models.UUIDField(default=uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True, null=True)
    send_date = models.DateTimeField('date to send', blank=True, null=True)
    pub_date = models.DateTimeField('date message created', auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'


class Metadata(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, related_name='meta')
    file = models.FileField(upload_to=r'mymail/uploads/%Y/%m/%d/')

    class Meta:
        verbose_name = 'Metadata'
        verbose_name_plural = 'Metadata'

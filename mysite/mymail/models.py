from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4
from multi_email_field.fields import MultiEmailField


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sender')
    emails = MultiEmailField(blank=True, null=True)
    url = models.UUIDField(default=uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True, null=True)
    send_date = models.DateTimeField('date to send', blank=True, null=True)
    pub_date = models.DateTimeField('date message created', auto_now_add=True)

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'


class Receivers(models.Model):
    user = models.ForeignKey(User, blank=True, default=None, related_name='user', on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    message = models.ForeignKey(Message, blank=True, default=None, related_name='receivers', on_delete=models.CASCADE)

    def __str__(self):
        return "{} {}".format(str(self.id), str(self.user))


class Metadata(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=r'uploads/%Y/%m/%d/', blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, related_name='meta')

    class Meta:
        verbose_name = 'Metadata'
        verbose_name_plural = 'Metadata'
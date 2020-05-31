from django.contrib import admin
from .models import Message, Receivers, Metadata

admin.site.register(Message)
admin.site.register(Receivers)
admin.site.register(Metadata)

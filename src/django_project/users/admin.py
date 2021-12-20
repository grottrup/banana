from django.contrib import admin
from users.models import event, User
# Register your models here.

admin.site.register(event)
admin.site.register(User)
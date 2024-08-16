from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Folder)
admin.site.register(Document)
admin.site.register(DocumentVersion)
admin.site.register(Notification)
admin.site.register(ActivityLog)
admin.site.register(Report)